import pandas as pd


file_path = "data/raw/all-weeks-global.xlsx"

df = pd.read_excel(file_path)

print(df.head())

print("\n資料筆數與欄位數：")
print(df.shape)

print("\n欄位名稱：")
print(df.columns)

print("\n資料資訊：")
df.info()

print("\n缺失值數量：")
print(df.isnull().sum())

print("\n各類別：")
print(df["category"].unique())

print("\n最早與最新資料週：")
print(df["week"].min())
print(df["week"].max())

print("\nruntime 缺失資料的日期範圍：")

missing_runtime = df[df["runtime"].isnull()]

print("最早：", missing_runtime["week"].min())
print("最晚：", missing_runtime["week"].max())
print("筆數：", len(missing_runtime))

print("\n有 runtime 資料的最早日期：")

has_runtime = df[df["runtime"].notnull()]

print(has_runtime["week"].min())

df["week"] = pd.to_datetime(df["week"])

print("\n轉換後的資料型別：")
print(df.dtypes)