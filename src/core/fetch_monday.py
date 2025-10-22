import requests
import pandas as pd
from tqdm import tqdm
from src.config.settings import (
    MONDAY_BASE_URL,
    MONDAY_API_TOKEN,
    MONDAY_BOARD_ID,
    MONDAY_COLUMN_ID,
    MONDAY_GROUP_PADRAO,
    MONDAY_GROUP_MOVBCO,
)

# =========================================
# ⚙️ CONFIGURAÇÕES
# =========================================
MONDAY_API_URL = MONDAY_BASE_URL
BOARD_ID = int(MONDAY_BOARD_ID)
HEADERS = {
    "Authorization": MONDAY_API_TOKEN,
    "Content-Type": "application/json",
}

# =========================================
# 🔍 FUNÇÃO PARA BUSCAR ITENS DO MONDAY
# =========================================
def fetch_monday_ids():
    """
    Busca todos os itens de ambos os grupos no Monday.com e
    retorna um DataFrame com colunas: [Group, Numero AF, ID].
    """

    grupos = {
        "Padrão": MONDAY_GROUP_PADRAO,
        "MOVBCO": MONDAY_GROUP_MOVBCO,
    }

    all_items = []
    pbar = tqdm(total=len(grupos), desc="🔄 Buscando dados do Monday", unit="grupo")

    for nome_grupo, group_id in grupos.items():
        cursor = None
        print(f"\n📦 Consultando grupo {nome_grupo}")

        while True:
            query = f"""
            query ($cursor: String) {{
              boards (ids: ["{BOARD_ID}"]) {{
                groups (ids: ["{group_id}"]) {{
                  title
                  id
                  items_page (limit: 500, cursor: $cursor) {{
                    cursor
                    items {{
                      id
                      name
                      column_values(ids: ["{MONDAY_COLUMN_ID}"]) {{
                        id
                        text
                      }}
                    }}
                  }}
                }}
              }}
            }}
            """

            try:
                resp = requests.post(
                    MONDAY_API_URL,
                    headers=HEADERS,
                    json={"query": query, "variables": {"cursor": cursor}},
                    timeout=30,
                )
                data = resp.json()
            except Exception as e:
                print(f"❌ Erro de conexão com o Monday para o grupo {group_id}: {e}")
                break

            try:
                group_data = data["data"]["boards"][0]["groups"][0]
                items_page = group_data["items_page"]
                items = items_page["items"]
            except (KeyError, IndexError, TypeError):
                print(f"⚠️ Erro ao interpretar resposta para o grupo {group_id}: {data}")
                break

            for item in items:
                col_val = (
                    item["column_values"][0]["text"]
                    if item.get("column_values")
                    else None
                )
                all_items.append(
                    {
                        "Item ID": item["id"],       # <- interno, necessário para delete_item()
                        "Group": group_data["title"],
                        "Numero AF": item["name"],
                        "ID": col_val,
                    }
                )

            cursor = items_page.get("cursor")
            if not cursor:
                break

        pbar.update(1)

    pbar.close()

    print(f"\n📊 Total de pagamentos localizados no Monday: {len(all_items)}")

    df_monday = pd.DataFrame(all_items)
    return df_monday


# =========================================
# 🧪 TESTE DIRETO
# =========================================
if __name__ == "__main__":
    df_monday = fetch_monday_ids()
    print("\n📋 Dados obtidos do Monday:")
    print(df_monday)
