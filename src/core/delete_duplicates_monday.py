# src/core/delete_duplicates_monday.py
import requests
from src.config.settings import MONDAY_BASE_URL, MONDAY_API_TOKEN
from src.utils.detect_duplicates_monday import detect_duplicate_ids

HEADERS = {
    "Authorization": MONDAY_API_TOKEN,
    "Content-Type": "application/json"
}

def delete_duplicate_items():
    """
    Exclui itens duplicados no Monday, mantendo apenas 1 por ID.
    """
    df_dup = detect_duplicate_ids()
    if df_dup.empty:
        print("✅ Nenhum ID duplicado encontrado.")
        return

    for id_val, grupo in df_dup.groupby("ID"):
        itens = grupo.to_dict("records")
        itens_para_excluir = itens[1:]  # mantém o primeiro
        for item in itens_para_excluir:
            mutation = """
            mutation ($item_id: ID!) {
              delete_item(item_id: $item_id) {
                id
              }
            }
            """
            variables = {"item_id": str(item["Item ID"])}  # substitua se tiver o campo real do item_id

            try:
                requests.post(
                    MONDAY_BASE_URL,
                    headers=HEADERS,
                    json={"query": mutation, "variables": variables},
                    timeout=20
                )
                print(f"🗑️ Removido duplicado ID={id_val} ({item['Numero AF']}) do grupo {item['Group']}")
            except Exception as e:
                print(f"⚠️ Erro ao excluir {id_val}: {e}")
