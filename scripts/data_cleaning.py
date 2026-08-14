import pandas as pd


def clean_netflix_data(df):
    df = df.copy()

    df.columns = df.columns.str.strip()

    df["week"] = pd.to_datetime(df["week"])

    df = df.drop_duplicates()

    return df


def save_cleaned_data(df, output_path):
    df.to_excel(output_path, index=False)
