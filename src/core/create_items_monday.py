import requests
import json
import time
from tqdm import tqdm
from src.config.settings import (
    MONDAY_BASE_URL,
    MONDAY_API_TOKEN,
    MONDAY_BOARD_ID,
    MONDAY_GROUP_PADRAO,
    MONDAY_GROUP_MOVBCO
)

# =========================================
# ⚙️ CONFIGURAÇÕES
# =========================================
MONDAY_API_URL = MONDAY_BASE_URL
BOARD_ID = int(MONDAY_BOARD_ID)
GROUP_PADRAO = MONDAY_GROUP_PADRAO
GROUP_MOVBCO = MONDAY_GROUP_MOVBCO

HEADERS = {
    "Authorization": MONDAY_API_TOKEN,
    "Content-Type": "application/json"
}

# =========================================
# 🚀 FUNÇÃO PARA CRIAR ITEM NO MONDAY
# =========================================
def criar_item_monday(row):
    """
    Cria um item no Monday a partir de uma linha de DataFrame.
    Se o campo 'Nº Título' começar com 'MOVBCO', envia para o grupo MOVBCO.
    Caso contrário, envia para o grupo padrão.
    """
    mutation = """
    mutation ($board: ID!, $group: String!, $item_name: String!, $column_values: JSON!) {
      create_item(board_id: $board, group_id: $group, item_name: $item_name, column_values: $column_values) {
        id
      }
    }
    """

    # -----------------------------------------
    # 📦 Define grupo com base no Nº do Título
    # -----------------------------------------
    numero_titulo = str(row.get("Nº Título") or "").upper()
    if numero_titulo.startswith("MOVBCO"):
        grupo_escolhido = GROUP_MOVBCO
        nome_grupo_log = "MOVBCO"
    else:
        grupo_escolhido = GROUP_PADRAO
        nome_grupo_log = "Pagamentos"

    # -----------------------------------------
    # 🧱 Monta os valores das colunas
    # -----------------------------------------
    col_vals = {
        "text_mknh23aa": row.get("Nome da pessoa"),
        "text_mknhys8v": row.get("Nome curto"),
        "date_mknhf7dr": {"date": str(row.get("Dt. venc. original")) if row.get("Dt. venc. original") else None},
        "date_mknhk9yy": {"date": str(row.get("Dt. da Realização")) if row.get("Dt. da Realização") else None},
        "numeric_mknhx7xx": str(row.get("Vl. título (atualizado)") or ""),
        "numeric_mknh5gyx": str(row.get("Vl. líquido") or ""),
        "dropdown_mkqj16vc": {"labels": [row.get("Forma de Pagamento")]} if row.get("Forma de Pagamento") else None,
        "dropdown_mkqjnn18": {"labels": [row.get("Centro(s) de custo")]} if row.get("Centro(s) de custo") else None,
        "text_mknh7b0j": row.get("Nº Título"),
        "numeric_mknh99sh": str(row.get("Vl. desconto desmembramento") or ""),
        "numeric_mknhca65": str(row.get("Vl. PIS x COFINS x CSLL") or ""),
        "numeric_mknharz2": str(row.get("Vl. IRRF") or ""),
        "numeric_mknhqxpq": str(row.get("Vl. INSS") or ""),
        "numeric_mknhd7ss": str(row.get("Vl. ISS") or ""),
        "numeric_mknh8w8m": str(row.get("Vl. multa desmembramento") or ""),
        "numeric_mknhhe99": str(row.get("Vl. juros desmembramento") or ""),
        "text_mknh5an4": row.get("Observação"),
        "dropdown_mkqj1npx": {"labels": [row.get("TIPO DE OPERAÇÃO")]} if row.get("TIPO DE OPERAÇÃO") else None,
        "text_mktkv6ct": row.get("ID"),
    }

    col_vals = {k: v for k, v in col_vals.items() if v is not None}

    variables = {
        "board": BOARD_ID,
        "group": grupo_escolhido,
        "item_name": row.get("Numero af", "Sem nome"),
        "column_values": json.dumps(col_vals)
    }

    # -----------------------------------------
    # 🔁 Tentativas com retry
    # -----------------------------------------
    for tentativa in range(3):
        try:
            response = requests.post(
                MONDAY_API_URL,
                headers=HEADERS,
                json={"query": mutation, "variables": variables},
                timeout=30
            )
            data = response.json()

            if "errors" in data:
                print(f"⚠️ Erro ao criar item {row.get('ID')}: {data['errors'][0]['message']}")
                return None

            item_id = data["data"]["create_item"]["id"]
            numero_titulo_log = row.get("Nº Título", "—")
            print(f"📦 Enviado → ID: {row.get('ID')} | Nº Título: {numero_titulo_log} | Grupo: {nome_grupo_log}")
            return item_id

        except Exception as e:
            print(f"⚠️ Erro na tentativa {tentativa + 1} com ID {row.get('ID')}: {e}")
            time.sleep(2)

    print(f"❌ Falha ao criar item {row.get('ID')} após 3 tentativas.")
    return None


# =========================================
# 🧩 LOOP PARA SUBIR AO MONDAY
# =========================================
def enviar_para_monday(df_novos_detalhes):
    """
    Envia os novos pagamentos enriquecidos para o Monday.
    """
    ids_criados = []
    total_por_grupo = {"Pagamentos": 0, "MOVBCO": 0}

    for _, linha in tqdm(df_novos_detalhes.iterrows(), total=len(df_novos_detalhes), desc="⬆️ Upload", unit="item"):
        item_id = criar_item_monday(linha)
        if item_id:
            ids_criados.append(item_id)

            numero_titulo = str(linha.get("Nº Título") or "").upper()
            if numero_titulo.startswith("MOVBCO"):
                total_por_grupo["MOVBCO"] += 1
            else:
                total_por_grupo["Pagamentos"] += 1

        time.sleep(0.3)

    print(f"\n✅ Upload concluído! {len(ids_criados)} itens criados com sucesso no Monday.\n")
    print("📊 Resumo por grupo:")
    for grupo, total in total_por_grupo.items():
        print(f"  • {grupo}: {total} itens")

    return ids_criados
