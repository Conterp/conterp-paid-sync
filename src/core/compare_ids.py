import pandas as pd


def find_new_ids(df_alterdata: pd.DataFrame, df_monday: pd.DataFrame) -> pd.DataFrame:
    """
    Compara IDs da Alterdata e Monday e retorna apenas os novos.
    Mantém as colunas ['ID', 'DataBaixa', 'Pagina'].

    Args:
        df_alterdata (pd.DataFrame): DataFrame vindo da Alterdata (com colunas ID, DataBaixa, Pagina)
        df_monday (pd.DataFrame): DataFrame com IDs existentes no Monday (coluna 'ID')

    Returns:
        pd.DataFrame: Subconjunto de df_alterdata com os novos IDs.
    """

    # === Validação inicial ===
    if df_alterdata.empty:
        print("⚠️ Nenhum dado na Alterdata — retornando vazio.")
        return pd.DataFrame(columns=["ID", "DataBaixa", "Pagina"])

    if df_monday.empty:
        print("⚠️ Nenhum dado encontrado no Monday — retornando todos da Alterdata.")
        return df_alterdata[["ID", "DataBaixa", "Pagina"]].copy()

    # === Normalização de IDs ===
    df_alterdata["ID"] = df_alterdata["ID"].astype(str).str.strip().str.upper()
    df_monday["ID"] = df_monday["ID"].astype(str).str.strip().str.upper()

    # === Comparação ===
    novos = df_alterdata[~df_alterdata["ID"].isin(df_monday["ID"])].copy()

    # === Organização final ===
    novos = novos[["ID", "DataBaixa", "Pagina"]]  # garante apenas as colunas desejadas
    print(f"🆔 Total de novos IDs encontrados: {len(novos)}")

    return novos
