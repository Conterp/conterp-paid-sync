# src/core/compare_ids.py
from __future__ import annotations
import pandas as pd

def _norm_id_series(s: pd.Series) -> pd.Series:
    """
    Normaliza IDs para comparação:
    - string, strip, upper
    - preserva NaN
    """
    if s is None or s.empty:
        return pd.Series(dtype="object")
    s_str = s.astype(str)
    s_norm = s_str.where(~s.isna(), None)
    return pd.Series(s_norm).str.strip().str.upper()

def find_new_ids(df_alterdata: pd.DataFrame, df_monday: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna títulos da Alterdata que ainda NÃO existem no Monday.
    Compara por coluna 'ID' normalizada.
    Saída: colunas ['ID','DataBaixa','Pagina'] se existirem.
    """
    desired_cols = ["ID", "DataBaixa", "Pagina"]

    if df_alterdata is None or df_alterdata.empty:
        return pd.DataFrame(columns=desired_cols)

    if df_monday is None or df_monday.empty:
        existing = [c for c in desired_cols if c in df_alterdata.columns]
        return df_alterdata[existing].copy()

    alt = df_alterdata.copy()
    mon = df_monday.copy()
    alt["ID_norm"] = _norm_id_series(alt["ID"])
    mon["ID_norm"] = _norm_id_series(mon["ID"])

    novos = alt.loc[~alt["ID_norm"].isin(mon["ID_norm"])].copy()
    existing = [c for c in desired_cols if c in novos.columns]
    return novos[existing]

def find_monday_orphans(df_alter_filtrado: pd.DataFrame,
                        df_monday: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna itens do Monday cujo 'ID' NÃO aparece no df_alter_filtrado (mesma janela).
    Compara por coluna 'ID' normalizada.
    Saída preferida (se existirem): ['Item ID','Group','Numero AF','ID'].
    """
    if df_monday is None or df_monday.empty:
        return pd.DataFrame(columns=["Item ID", "Group", "Numero AF", "ID"])

    if df_alter_filtrado is None or df_alter_filtrado.empty:
        # se Alterdata filtrado está vazio, tudo do Monday vira candidato
        dm = df_monday.copy()
        cols = [c for c in ["Item ID", "Group", "Numero AF", "ID"] if c in dm.columns]
        return dm[cols].reset_index(drop=True)

    dm = df_monday.copy()
    dm["ID_norm"] = _norm_id_series(dm["ID"])
    alt_ids = set(_norm_id_series(df_alter_filtrado["ID"]).dropna())

    orfaos = dm.loc[~dm["ID_norm"].isin(alt_ids)].copy()
    preferred = ["Item ID", "Group", "Numero AF", "ID"]
    cols = [c for c in preferred if c in orfaos.columns] or ["ID_norm"]
    return orfaos[cols].reset_index(drop=True)
