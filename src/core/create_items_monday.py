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

    Retorna um dicionário com o resultado da tentativa:
    created ou error.
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

    id_negocio = row.get("ID")
    numero_titulo_log = row.get("Nº Título", "—")

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

        "numeric_mknh99sh": numero_monday(
            row.get("Vl. desconto desmembramento")
        ),
        "numeric_mknhca65": numero_monday(
            row.get("Vl. PIS x COFINS x CSLL")
        ),
        "numeric_mknharz2": numero_monday(row.get("Vl. IRRF")),
        "numeric_mknhqxpq": numero_monday(row.get("Vl. INSS")),
        "numeric_mknhd7ss": numero_monday(row.get("Vl. ISS")),
        "numeric_mknh8w8m": numero_monday(
            row.get("Vl. multa desmembramento")
        ),
        "numeric_mknhhe99": numero_monday(
            row.get("Vl. juros desmembramento")
        ),

        "text_mknh5an4": texto_monday(row.get("Observação")),
        "dropdown_mkqj1npx": dropdown_monday(
            row.get("TIPO DE OPERAÇÃO")
        ),

        "text_mktkv6ct": texto_monday(row.get("ID")),
    }

    col_vals = {
        key: value
        for key, value in col_vals.items()
        if value is not None
    }

    variables = {
        "board": BOARD_ID,
        "group": grupo_escolhido,
        "item_name": texto_monday(row.get("Numero af")) or "Sem nome",
        "column_values": json.dumps(
            col_vals,
            ensure_ascii=False,
            allow_nan=False
        )
    }

    # -----------------------------------------
    # 🔁 Tentativas com retry
    # -----------------------------------------
    ultimo_erro = None

    for tentativa in range(3):
        try:
            response = requests.post(
                MONDAY_API_URL,
                headers=HEADERS,
                json={
                    "query": mutation,
                    "variables": variables
                },
                timeout=30
            )
            data = response.json()

            if "errors" in data:
                ultimo_erro = data["errors"][0]["message"]

                print(
                    f"⚠️ Erro ao criar item {id_negocio}: "
                    f"{ultimo_erro}"
                )

                return {
                    "ID": id_negocio,
                    "Nº Título": numero_titulo_log,
                    "GROUP": nome_grupo_log,
                    "status": "error",
                    "item_id": None,
                    "error": ultimo_erro,
                }

            item_id = data["data"]["create_item"]["id"]

            print(
                f"📦 Enviado → ID: {id_negocio} | "
                f"Nº Título: {numero_titulo_log} | "
                f"Grupo: {nome_grupo_log}"
            )

            return {
                "ID": id_negocio,
                "Nº Título": numero_titulo_log,
                "GROUP": nome_grupo_log,
                "status": "created",
                "item_id": item_id,
                "error": None,
            }

        except Exception as exc:
            ultimo_erro = str(exc)

            print(
                f"⚠️ Erro na tentativa {tentativa + 1} "
                f"com ID {id_negocio}: {exc}"
            )

            time.sleep(2)

    print(
        f"❌ Falha ao criar item {id_negocio} "
        "após 3 tentativas."
    )

    return {
        "ID": id_negocio,
        "Nº Título": numero_titulo_log,
        "GROUP": nome_grupo_log,
        "status": "error",
        "item_id": None,
        "error": ultimo_erro,
    }


# =========================================
# 🧩 LOOP PARA SUBIR AO MONDAY
# =========================================
def enviar_para_monday(df_novos_detalhes):
    """
    Envia os novos pagamentos enriquecidos para o Monday.

    Retorna um DataFrame com uma linha por tentativa realizada.
    """
    result_rows = []
    total_por_grupo = {
        "Pagamentos": 0,
        "MOVBCO": 0
    }

    for _, linha in tqdm(
        df_novos_detalhes.iterrows(),
        total=len(df_novos_detalhes),
        desc="⬆️ Upload",
        unit="item"
    ):
        resultado = criar_item_monday(linha)
        result_rows.append(resultado)

        if resultado["status"] == "created":
            total_por_grupo[resultado["GROUP"]] += 1

        time.sleep(0.3)

    df_create_result = pd.DataFrame(
        result_rows,
        columns=[
            "ID",
            "Nº Título",
            "GROUP",
            "status",
            "item_id",
            "error",
        ]
    )

    total_criados = int(
        (df_create_result["status"] == "created").sum()
    )
    total_erros = int(
        (df_create_result["status"] == "error").sum()
    )

    print(
        f"\n✅ Upload concluído! {total_criados} itens "
        "criados com sucesso no Monday.\n"
    )

    print("📊 Resumo por grupo:")
    for grupo, total in total_por_grupo.items():
        print(f"  • {grupo}: {total} itens")

    if total_erros > 0:
        print(f"  • Erros: {total_erros} itens")

    return df_create_result