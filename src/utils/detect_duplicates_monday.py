import pandas as pd
from src.core.fetch_monday import fetch_monday_ids

def detect_duplicate_ids():
    """
    Busca todos os itens do Monday e retorna um DataFrame com IDs duplicados.
    """
    df = fetch_monday_ids()
    df = df.dropna(subset=["ID"])
    df_duplicados = df[df.duplicated(subset=["ID"], keep=False)]

    colunas = [c for c in ["Item ID", "Group", "Numero AF", "ID"] if c in df_duplicados.columns]
    df_resultado = df_duplicados[colunas].reset_index(drop=True)

    # Contagem de IDs duplicados únicos
    total_ids_unicos = df_duplicados["ID"].nunique()

    # Contagem real de linhas duplicadas (as que seriam excluídas)
    total_linhas_excluir = sum(df_duplicados["ID"].value_counts() - 1)

    print(f"IDs duplicados únicos: {total_ids_unicos}")
    print(f"Total de linhas duplicadas excluídas: {total_linhas_excluir}")
    
    return df_resultado
