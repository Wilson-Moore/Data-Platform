import pandas as pd
USD_TO_DZD = 135.0

def handle_neg_values(df, column_names = []) -> pd.DataFrame:
    for column in column_names:
        df[column] = df[column].apply(lambda x: x if x >= 0 else None)
    return df

def clean_id(df, column_name) -> pd.DataFrame:
    df[column_name] = df[column_name].astype(str).str.replace(r'\D', '', regex=True)
    df[column_name] = pd.to_numeric(df[column_name], errors='coerce')
    return df

def clean_date(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    df = df.copy()
    s = df[column_name].astype(str).str.strip()

    # normalize separators: 2021.02.28 -> 2021-02-28
    s = s.str.replace(r"\.", "-", regex=True)

    parsed = pd.to_datetime(s, errors="coerce")

    # YYYY-MM-DD (after dot->dash normalization)
    mask = parsed.isna()
    parsed_y = pd.to_datetime(s[mask], format="%Y-%m-%d", errors="coerce")
    parsed.loc[mask] = parsed_y

    # MM-DD-YYYY
    mask = parsed.isna()
    parsed_mdy = pd.to_datetime(s[mask], format="%m-%d-%Y", errors="coerce")
    parsed.loc[mask] = parsed_mdy

    # Month Day, Year (March 3, 2021)
    mask = parsed.isna()
    parsed_long = pd.to_datetime(s[mask], format="%B %d, %Y", errors="coerce")
    parsed.loc[mask] = parsed_long

    # Mon-YYYY (Feb-2023) -> 2023-02-01
    mask = parsed.isna()
    parsed_mon_year = pd.to_datetime(s[mask], format="%b-%Y", errors="coerce")
    parsed.loc[mask] = parsed_mon_year

    df[column_name] = parsed
    return df

def usd_to_dzd(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    df = df.copy()

    df[column_name] = df[column_name] * USD_TO_DZD

    new_column_name = column_name.replace("USD", "DZD").replace("usd", "dzd")
    df.rename(columns={column_name: new_column_name}, inplace=True)

    return df

def standarize_names(df: pd.DataFrame, column_names=[]) -> pd.DataFrame:
    df = df.copy()
    for column in column_names:
        df[column] = (
            df[column]
            .astype(str)
            .str.replace("_", " ", regex=False)
            .str.replace("-", " ", regex=False) 
            .str.strip()
            .str.title()
        )
    return df

def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop_duplicates(keep='first')
    return df


def normalize_number(df: pd.DataFrame, column_names) -> pd.DataFrame:
    df = df.copy()

    for col in column_names:
        s = df[col].astype("string")  # better than astype(str), preserves <NA>

        # remove currency text/symbols if they exist (optional)
        s = s.str.replace("USD", "", regex=False).str.replace("$", "", regex=False).str.strip()

        # remove spaces (thousand sep)
        s = s.str.replace(" ", "", regex=False)

        # if decimal comma is used, convert it to dot
        # example: "1234,56" -> "1234.56"
        s = s.str.replace(",", ".", regex=False)

        df[col] = pd.to_numeric(s, errors="coerce")

    return df


