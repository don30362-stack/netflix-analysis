# Netflix 全球 Top 10 資料分析

本專題使用 Netflix Global Top 10 公開資料，
透過 Python 進行資料整理、分析與視覺化。

## 預定分析問題

1. Netflix 電影與影集的熱門程度是否有差異？
2. 英語與非英語內容的觀看表現有何不同？
3. 哪些作品在 Netflix Top 10 停留最久？
4. Netflix 熱門內容是否存在明顯的時間趨勢？
5. Netflix 排名與觀看量／觀看時數之間是否具有相關性？

## 使用技術

- Python
- Pandas
- Matplotlib
- OpenPyXL

## 專案結構

```text
data/
├─ raw/
└─ processed/

src/
├─ data_loader.py
├─ data_cleaning.py
├─ analysis.py
└─ visualization.py

output/
└─ charts/

main.py
requirements.txt
README.md