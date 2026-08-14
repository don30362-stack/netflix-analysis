import pandas as pd


def load_netflix_data(file_path):
    df = pd.read_excel(file_path)

    return df
