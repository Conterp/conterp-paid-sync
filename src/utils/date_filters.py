from datetime import date
import pandas as pd


def get_current_semester_range(data_ref=None):
    """
    Período fixo do board Pagamentos Realizados 2026.2.
    """
    start = date(2026, 7, 1)
    end = date(2026, 12, 31)
    return start, end


def filter_by_current_semester(
    df: pd.DataFrame,
    column="DataBaixa"
) -> pd.DataFrame:
    """
    Filtra os pagamentos pelo período fixo configurado.
    """
    if column not in df.columns:
        raise ValueError(
            f"Coluna '{column}' não encontrada no DataFrame."
        )

    start, end = get_current_semester_range()

    df = df.copy()
    df[column] = pd.to_datetime(
        df[column],
        errors="coerce"
    )

    df_filtered = df[
        (df[column] >= pd.Timestamp(start)) &
        (df[column] < pd.Timestamp(end) + pd.Timedelta(days=1))
    ].reset_index(drop=True)

    print(f"📅 Período Fixo: {start} → {end}")
    print(
        f"✅ Total de Pagamentos no Período: "
        f"{len(df_filtered)}"
    )

    return df_filtered


if __name__ == "__main__":
    # Teste rápido do período fixo
    data = {
        "ID": ["1", "2", "3", "4"],
        "DataBaixa": [
            "2026-06-30",
            "2026-07-01",
            "2026-12-31",
            "2027-01-01"
        ]
    }

    df = pd.DataFrame(data)
    filtered = filter_by_current_semester(df)
    print(filtered)
