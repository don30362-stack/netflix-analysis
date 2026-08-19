from scripts.data_cleaning import clean_netflix_data, save_cleaned_data
from scripts.data_loader import load_netflix_data

file_path = "data/raw/all-weeks-global.xlsx"
output_path = "data/processed/netflix_cleaned.xlsx"

df = load_netflix_data(file_path)

df = clean_netflix_data(df)

save_cleaned_data(df, output_path)

print("資料清理完成")
print("資料筆數：", len(df))
print("已儲存至：", output_path)
