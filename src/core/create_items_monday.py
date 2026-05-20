import requests
import json
import time
import pandas as pd
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
# 🧹 HELPERS PARA EVITAR PAYLOAD INVÁLIDO
# =========================================
def valor_valido(valor):
    if valor is None:
        return False

    try:
        if pd.isna(valor):
            return False
    except (TypeError, ValueError):
        pass

    if isinstance(valor, str):
        valor = valor.strip()
        if not valor:
            return False
        if valor.lower() in ["nan", "nat", "none", "null"]:
            return False

    return True


def texto_monday(valor):
    if not valor_valido(valor):
        return None
    return str(valor).strip()


def numero_monday(valor):
    if not valor_valido(valor):
        return None
    return str(valor)


def data_monday(valor):
    if not valor_valido(valor):
        return None

    if isinstance(valor, str):
        valor_limpo = valor.strip()

        if valor_limpo in ["1-01-01", "0001-01-01", "0001-01-01T00:00:00"]:
            return None

        if valor_limpo.startswith("0001"):
            return None

    data = pd.to_datetime(valor, errors="coerce")

    if pd.isna(data):
        return None

    return {"date": data.strftime("%Y-%m-%d")}


def dropdown_monday(valor):
    valor = texto_monday(valor)
    if not valor:
        return None
    return {"labels": [valor]}


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
        "text_mknh23aa": texto_monday(row.get("Nome da pessoa")),
        "text_mknhys8v": texto_monday(row.get("Nome curto")),

        "date_mknhf7dr": data_monday(row.get("Dt. venc. original")),
        "date_mknhk9yy": data_monday(row.get("Dt. da Realização")),

        "numeric_mknhx7xx": numero_monday(row.get("Vl. título (atualizado)")),
        "numeric_mknh5gyx": numero_monday(row.get("Vl. líquido")),

        "dropdown_mkqj16vc": dropdown_monday(row.get("Forma de Pagamento")),
        "dropdown_mkqjnn18": dropdown_monday(row.get("Centro(s) de custo")),

        "text_mknh7b0j": texto_monday(row.get("Nº Título")),

        "numeric_mknh99sh": numero_monday(row.get("Vl. desconto desmembramento")),
        "numeric_mknhca65": numero_monday(row.get("Vl. PIS x COFINS x CSLL")),
        "numeric_mknharz2": numero_monday(row.get("Vl. IRRF")),
        "numeric_mknhqxpq": numero_monday(row.get("Vl. INSS")),
        "numeric_mknhd7ss": numero_monday(row.get("Vl. ISS")),
        "numeric_mknh8w8m": numero_monday(row.get("Vl. multa desmembramento")),
        "numeric_mknhhe99": numero_monday(row.get("Vl. juros desmembramento")),

        "text_mknh5an4": texto_monday(row.get("Observação")),
        "dropdown_mkqj1npx": dropdown_monday(row.get("TIPO DE OPERAÇÃO")),

        "text_mktkv6ct": texto_monday(row.get("ID")),
    }

    col_vals = {k: v for k, v in col_vals.items() if v is not None}

    variables = {
        "board": BOARD_ID,
        "group": grupo_escolhido,
        "item_name": texto_monday(row.get("Numero af")) or "Sem nome",
        "column_values": json.dumps(col_vals, ensure_ascii=False, allow_nan=False)
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