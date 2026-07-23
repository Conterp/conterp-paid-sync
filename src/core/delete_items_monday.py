import requests
import pandas as pd
from typing import Iterable, List, Dict, Optional
from src.config.settings import MONDAY_BASE_URL, MONDAY_API_TOKEN
from src.utils.detect_duplicates_monday import detect_duplicate_ids


HEADERS = {
    "Authorization": MONDAY_API_TOKEN,
    "Content-Type": "application/json",
}

RESULT_COLUMNS = [
    "ID",
    "item_id",
    "reason",
    "status",
    "error",
]

# Use ID! (string) — Item IDs podem exceder Int32
DELETE_ITEM_MUTATION = """
mutation ($item_id: ID!) {
  delete_item (item_id: $item_id) { id }
}
"""


def _empty_result() -> pd.DataFrame:
    """Retorna um DataFrame vazio com a estrutura padrão de resultados."""
    return pd.DataFrame(columns=RESULT_COLUMNS)


def _post_monday(query: str, variables: dict) -> requests.Response:
    return requests.post(
        MONDAY_BASE_URL,
        headers=HEADERS,
        json={"query": query, "variables": variables},
        timeout=30,
    )


def _delete_item(item_id: str) -> tuple[bool, Optional[str]]:
    """Deleta 1 item por Item ID (string). Retorna (ok, error_message)."""
    try:
        resp = _post_monday(
            DELETE_ITEM_MUTATION,
            {"item_id": str(item_id).strip()},
        )
    except requests.RequestException as exc:
        return False, f"{type(exc).__name__}: {exc}"

    try:
        body = resp.json()
    except ValueError:
        return False, f"HTTP {resp.status_code}: {resp.text}"

    if not resp.ok:
        return False, f"HTTP {resp.status_code}: {body}"

    if body.get("errors"):
        return False, str(body["errors"])

    ok = bool(body.get("data", {}).get("delete_item", {}).get("id"))
    return (True, None) if ok else (False, str(body))


def delete_monday_items_by_id(
    item_ids: Iterable[int | str],
    id_label_map: Optional[Dict[str, str]] = None,
    reason_label: str = "delete",
) -> pd.DataFrame:
    """
    Deleta itens no Monday por Item ID.

    - id_label_map (opcional): mapeia Item ID -> rótulo de exibição
      (ex.: 'ID' de negócio).
    - Todas as exclusões são tentadas.
    - Retorna uma linha por tentativa com status 'deleted' ou 'error'.
    """
    ids: List[str] = [
        str(x).strip()
        for x in item_ids
        if pd.notna(x)
    ]

    if not ids:
        print("ℹ️ Nenhum Item ID válido para exclusão.")
        return _empty_result()

    result_rows = []

    for iid in ids:
        label = (id_label_map or {}).get(iid, iid)
        ok, err = _delete_item(iid)

        if ok:
            print(f"🗑️ Deletado ID {label}")

            result_rows.append(
                {
                    "ID": label,
                    "item_id": iid,
                    "reason": reason_label,
                    "status": "deleted",
                    "error": None,
                }
            )
        else:
            error_message = err or "resposta inválida"
            print(
                f"⚠️ Falha ao deletar ID {label}: "
                f"{error_message}"
            )

            result_rows.append(
                {
                    "ID": label,
                    "item_id": iid,
                    "reason": reason_label,
                    "status": "error",
                    "error": error_message,
                }
            )

    return pd.DataFrame(
        result_rows,
        columns=RESULT_COLUMNS,
    )


def delete_monday_orphan_items(
    df_orfaos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Deleta itens 'órfãos' (presentes no Monday e ausentes no Alterdata).

    Espera 'Item ID' e 'ID' no df_orfaos.
    Logs exibem o 'ID' de negócio.
    Retorna um DataFrame com o resultado de cada exclusão.
    """
    if df_orfaos is None or df_orfaos.empty:
        print("ℹ️ Nenhum órfão para excluir.")
        return _empty_result()

    missing = [
        column
        for column in ["Item ID", "ID"]
        if column not in df_orfaos.columns
    ]

    if missing:
        raise RuntimeError(
            f"Colunas ausentes em df_orfaos: {', '.join(missing)}"
        )

    # Mapa ItemID -> ID (negócio) para logs
    df = df_orfaos[["Item ID", "ID"]].dropna().astype(str)

    id_label_map = dict(
        zip(
            df["Item ID"].str.strip(),
            df["ID"].str.strip(),
        )
    )

    item_ids = df["Item ID"].unique().tolist()

    print(f"🗑️ Excluindo {len(item_ids)} órfãos do Monday...")

    return delete_monday_items_by_id(
        item_ids,
        id_label_map=id_label_map,
        reason_label="orphan",
    )


def delete_duplicate_items() -> pd.DataFrame:
    """
    Exclui itens duplicados no Monday, mantendo apenas 1 por ID.

    Reaproveita a função genérica, imprime pelo ID de negócio
    e retorna um DataFrame com o resultado de cada exclusão.
    """
    df_dup = detect_duplicate_ids()

    if df_dup is None or df_dup.empty:
        print("✅ Nenhum ID duplicado encontrado.")
        return _empty_result()

    required = {"ID", "Item ID"}
    miss = required.difference(df_dup.columns)

    if miss:
        raise RuntimeError(
            f"Colunas ausentes em df_dup: "
            f"{', '.join(sorted(miss))}"
        )

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
        print(
            "✅ Duplicados identificados, mas nada a excluir "
            "(já consolidado)."
        )
        return _empty_result()

    print(
        f"🧹 Removendo {len(item_ids_to_delete)} "
        "duplicado(s) no Monday..."
    )

    return delete_monday_items_by_id(
        item_ids_to_delete,
        id_label_map=id_label_map,
        reason_label="duplicate",
    )