from datetime import date, datetime
import pandas as pd


def get_current_semester_range(data_ref=None):
    """
    Retorna o intervalo de datas do semestre atual (inicio, fim).
    """
    if data_ref is None:
        data_ref = date.today()
    elif isinstance(data_ref, str):
        data_ref = datetime.strptime(data_ref, "%Y-%m-%d").date()

    year = data_ref.year
    if data_ref.month <= 6:
        start = date(year, 1, 1)
        end = date(year, 6, 30)
    else:
        start = date(year, 7, 1)
        end = date(year, 12, 31)

    return start, end


def filter_by_current_semester(df: pd.DataFrame, column="DataBaixa") -> pd.DataFrame:
    """
    Filtra o DataFrame para manter apenas os registros cuja coluna de data
    esteja dentro do semestre atual.
    """
    if column not in df.columns:
        raise ValueError(f"Coluna '{column}' não encontrada no DataFrame.")

    start, end = get_current_semester_range()
    df[column] = pd.to_datetime(df[column], errors="coerce")

    df_filtered = df[
        (df[column] >= pd.Timestamp(start)) &
        (df[column] <= pd.Timestamp(end))
    ].reset_index(drop=True)

    print(f"📅 Semestre Atual: {start} → {end}")
    print(f"✅ Total de Pagamentos no Semestre Atual: {len(df_filtered)}")

    return df_filtered


if __name__ == "__main__":
    # Teste rápido
    data = {
        "ID": ["1", "2", "3", "4"],
        "DataBaixa": ["2025-01-05", "2025-03-12", "2025-08-20", "2025-12-15"]
    }
    import pandas as pd
    df = pd.DataFrame(data)
    filtered = filter_by_current_semester(df)
    print(filtered)
