from pathlib import Path

import pandas as pd

project_root = Path(__file__).resolve().parent.parent
input_path = project_root / "data" / "processed" / "netflix_top10_clean.csv"

df = pd.read_csv(input_path)

df["week"] = pd.to_datetime(df["week"])

print("資料筆數與欄位數：")
print(df.shape)

print("\n欄位型態：")
print(df.dtypes)

print("\n資料日期範圍：")
print("最早：", df["week"].min())
print("最新：", df["week"].max())

print("\n數值欄位基本統計：")
print(df.describe())

print("\n各內容類別資料筆數：")
print(df["category"].value_counts())

print("\n各類別平均觀看時數：")
print(df.groupby("category")["weekly_hours_viewed"].mean().sort_values(ascending=False))

print("\n各類別總觀看時數：")
print(df.groupby("category")["weekly_hours_viewed"].sum().sort_values(ascending=False))

print("\n各類別 weekly_views 有效資料筆數：")
print(df.groupby("category")["weekly_views"].count())
