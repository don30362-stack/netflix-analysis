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


# 建立電影 / 影集內容類型欄位
df["content_type"] = df["category"].apply(
    lambda x: "Films" if x.startswith("Films") else "TV"
)

print("\n電影與影集資料筆數：")
print(df["content_type"].value_counts())

print("\n電影與影集平均觀看時數：")
print(
    df.groupby("content_type")["weekly_hours_viewed"]
    .mean()
    .sort_values(ascending=False)
)

print("\n電影與影集平均觀看次數：")
print(df.groupby("content_type")["weekly_views"].mean().sort_values(ascending=False))

print("\n電影與影集總觀看時數：")
print(
    df.groupby("content_type")["weekly_hours_viewed"].sum().sort_values(ascending=False)
)

print("\n電影與影集 weekly_views 有效資料筆數：")
print(df.groupby("content_type")["weekly_views"].count())


# 建立英語 / 非英語內容分類欄位
df["language_type"] = df["category"].apply(
    lambda x: "Non-English" if "Non-English" in x else "English"
)

print("\n英語與非英語內容資料筆數：")
print(df["language_type"].value_counts())

print("\n英語與非英語內容平均觀看時數：")
print(
    df.groupby("language_type")["weekly_hours_viewed"]
    .mean()
    .sort_values(ascending=False)
)

print("\n英語與非英語內容平均觀看次數：")
print(df.groupby("language_type")["weekly_views"].mean().sort_values(ascending=False))

print("\n英語與非英語內容總觀看時數：")
print(
    df.groupby("language_type")["weekly_hours_viewed"]
    .sum()
    .sort_values(ascending=False)
)

print("\n英語與非英語內容總觀看次數：")
print(df.groupby("language_type")["weekly_views"].sum().sort_values(ascending=False))

print("\n英語與非英語內容 weekly_views 有效資料筆數：")
print(df.groupby("language_type")["weekly_views"].count())
