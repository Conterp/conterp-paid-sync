import requests
import pandas as pd
from typing import Iterable, List, Dict, Optional
from src.config.settings import MONDAY_BASE_URL, MONDAY_API_TOKEN
from src.utils.detect_duplicates_monday import detect_duplicate_ids

HEADERS = {
    "Authorization": MONDAY_API_TOKEN,
    "Content-Type": "application/json",
}

# Use ID! (string) — Item IDs podem exceder Int32
DELETE_ITEM_MUTATION = """
mutation ($item_id: ID!) {
  delete_item (item_id: $item_id) { id }
}
"""

def _post_monday(query: str, variables: dict) -> requests.Response:
    return requests.post(
        MONDAY_BASE_URL,
        headers=HEADERS,
        json={"query": query, "variables": variables},
        timeout=30,
    )

def _delete_item(item_id: str) -> tuple[bool, Optional[str]]:
    """Deleta 1 item por Item ID (string). Retorna (ok, error_message)."""
    resp = _post_monday(DELETE_ITEM_MUTATION, {"item_id": str(item_id).strip()})
    try:
        body = resp.json()
    except Exception:
        return False, resp.text

    if body.get("errors"):
        return False, str(body["errors"])

    ok = bool(body.get("data", {}).get("delete_item", {}).get("id"))
    return (True, None) if ok else (False, str(body))

def delete_monday_items_by_id(
    item_ids: Iterable[int | str],
    id_label_map: Optional[Dict[str, str]] = None,
) -> None:
    """
    Deleta itens no Monday por Item ID.
    - id_label_map (opcional): mapeia Item ID -> rótulo de exibição (ex.: 'ID' de negócio).
      Se fornecido, os logs usarão esse rótulo em vez do Item ID.
    """
    ids: List[str] = [str(x).strip() for x in item_ids if pd.notna(x)]
    if not ids:
        print("ℹ️ Nenhum Item ID válido para exclusão.")
        return

    for iid in ids:
        label = (id_label_map or {}).get(iid, iid)  # mostra o 'ID' se houver, senão o próprio Item ID
        ok, err = _delete_item(iid)
        if ok:
            print(f"🗑️ Deletado ID {label}")
        else:
            print(f"⚠️ Falha ao deletar ID {label}: {err or 'resposta inválida'}")

def delete_monday_orphan_items(df_orfaos: pd.DataFrame) -> None:
    """
    Deleta itens 'órfãos' (presentes no Monday e ausentes no Alterdata).
    Espera 'Item ID' e 'ID' no df_orfaos. Logs exibem o 'ID' de negócio.
    """
    if df_orfaos is None or df_orfaos.empty:
        print("ℹ️ Nenhum órfão para excluir.")
        return

    missing = [c for c in ["Item ID", "ID"] if c not in df_orfaos.columns]
    if missing:
        raise RuntimeError(f"Colunas ausentes em df_orfaos: {', '.join(missing)}")

    # Mapa ItemID -> ID (negócio) para logs
    df = df_orfaos[["Item ID", "ID"]].dropna().astype(str)
    id_label_map = dict(zip(df["Item ID"].str.strip(), df["ID"].str.strip()))

    item_ids = df["Item ID"].unique().tolist()
    print(f"🗑️ Excluindo {len(item_ids)} órfãos do Monday...")
    delete_monday_items_by_id(item_ids, id_label_map=id_label_map)

def delete_duplicate_items() -> None:
    """
    Exclui itens duplicados no Monday, mantendo apenas 1 por ID.
    Reaproveita a função genérica e imprime pelo ID de negócio.
    """
    df_dup = detect_duplicate_ids()
    if df_dup is None or df_dup.empty:
        print("✅ Nenhum ID duplicado encontrado.")
        return

    required = {"ID", "Item ID"}
    miss = required.difference(df_dup.columns)
    if miss:
        raise RuntimeError(f"Colunas ausentes em df_dup: {', '.join(sorted(miss))}")

    df_dup = df_dup.copy()

    # Monta lista de Item IDs a excluir e o mapa ItemID -> ID para logs
    item_ids_to_delete: List[str] = []
    id_label_map: Dict[str, str] = {}
    for _id, grupo in df_dup.groupby("ID", sort=False):
        if len(grupo) > 1:
            restantes = grupo.iloc[1:]
            for _, row in restantes.iterrows():
                if pd.notna(row["Item ID"]):
                    iid = str(row["Item ID"]).strip()
                    item_ids_to_delete.append(iid)
                    id_label_map[iid] = str(row["ID"]).strip()

    if not item_ids_to_delete:
        print("✅ Duplicados identificados, mas nada a excluir (já consolidado).")
        return

    print(f"🧹 Removendo {len(item_ids_to_delete)} duplicado(s) no Monday...")
    delete_monday_items_by_id(item_ids_to_delete, id_label_map=id_label_map)
