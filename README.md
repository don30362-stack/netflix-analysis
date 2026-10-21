# Netflix 全球 Top 10｜Python 資料分析專題

使用 Python 分析 Netflix 官方全球 Top 10 歷史資料，完成資料取得、清洗、驗證、統計分析與視覺化。
專題涵蓋五項研究問題，提供五張正式圖表、完整研究報告，以及不依賴網路或正式快照的離線測試。

[查看完整研究報告](docs/ANALYSIS_REPORT.md)

## 1. 技術與實作能力

| 技術 | 實際用途 |
|---|---|
| Python／pathlib | 以函式與模組串接資料流程，管理跨環境檔案路徑 |
| Requests／OpenPyXL | 下載官方 Excel，檢查 HTTP、逾時、檔案可讀性及必要欄位；驗證後以暫存檔安全替換 |
| Pandas | 日期／數值轉換、缺值處理、資料衝突驗證、分組彙總與時間序列 |
| Pandas／SciPy | 逐段計算 Pearson、Spearman 相關性與敏感度分析；SciPy 支援 Spearman 計算 |
| Matplotlib／NumPy | 製作五張統計圖、相關係數分箱及中文標示 |
| unittest／mock | 55 項離線測試，涵蓋 HTTP 模擬、邊界條件與跨模組整合 |
| CSV／SHA-256 | CSV 輸出與讀回驗證、固定快照的雜湊識別紀錄 |

資料流程：**下載 → 驗證 → 清洗 → CSV → 五題分析 → 五張圖表**。

清洗保留合法缺值與不同季度同週上榜紀錄；不合理類別、排名、數值或衝突會明確報錯，不靜默刪除修復。

## 2. 正式資料基準

| 項目 | 本次正式結果採用的基準 |
|---|---|
| 資料來源 | [Netflix 官方全球 Top 10 歷史 Excel](https://www.netflix.com/tudum/top10/data/all-weeks-global.xlsx) |
| 固定快照下載日期 | 2026-10-20 |
| 資料期間／截止週 | 2021-07-04～2026-10-04 |
| 清洗後資料 | 11,000 筆，275 週、四類榜單 |
| 有效 weekly_views 期間 | 2023-06-18～2026-10-04 |
| Git 資料範圍 | 原始 Excel、清洗 CSV 與本機預覽不包含在版本庫 |

**下載日期與資料截止週不同**；本頁採用新固定快照，不是較早版本分析的重現。
檔名、大小、完整 SHA-256 及缺失值數量見[研究報告第 2～3 節](docs/ANALYSIS_REPORT.md#2-資料來源與固定快照)。

## 3. 五個研究問題

| 題目 | 研究問題 | 簡短分析方式 |
|---|---|---|
| 1 | 電影與影集的觀看表現是否不同？ | 比較上榜項目－週平均 views |
| 2 | 英語與非英語內容的觀看表現有何不同？ | 在 Films／TV 內依官方 category 分組比較 |
| 3 | 哪些官方上榜項目／季度的最大累積上榜週數最高？ | 依類別、名稱、季度分組，取官方累積週數最大值 |
| 4 | 全球四類 Top 10 榜單的每週觀看時數如何變化？ | 週加總、年度週均及置中移動平均 |
| 5 | 在連續有效上榜觀測區段中，週次增加時，觀看次數是否傾向下降？ | 每段計算 Pearson／Spearman，再等區段摘要 |

## 4. 主要研究成果與圖表

以下均為上述固定快照的描述性結果，完整計算方法及數表見研究報告。

| 題目 | 主要發現 |
|---|---|
| 電影與影集 | 上榜項目－週平均：電影約 **552 萬次**、影集約 **395 萬次** |
| 英語與非英語 | 英語類別在 Films、TV 各自的平均均較高；不能推論全部 Netflix 使用者偏好英語 |
| 累積上榜週數 | KPop Demon Hunters 的官方最大累積為 **67 週**；影集須按季度解讀，不加總各季 |
| 時間趨勢 | 全球四類榜單每週時數隨時間波動，以 **13 週置中移動平均**觀察中期趨勢；不是全平台觀看量 |
| 連續上榜相關性 | 至少連續五個有效觀測週的 **258 段**中，Pearson 負相關 **251/258（97.3%）**，Spearman 負相關 **253/258（98.1%）** |

第一、二題的平均以每筆「上榜項目－週」為單位，不是每個唯一作品平均一次。
第五題每個有效區段等權，結果不代表全部作品、每週一定下降或因果關係。

### 代表圖一：電影與影集

![電影與影集上榜項目－週平均觀看次數；有效期間為 2023-06-18 至 2026-10-04](charts/01_films_vs_tv_average_views.png)

圖中單位為百萬次；views 是觀看次數指標，不是獨立觀看人數。

### 代表圖二：連續上榜與觀看次數

![連續有效上榜觀測區段的相關係數分布；限定合格樣本，並非完整上榜生命週期](charts/05_continuous_run_correlation_distribution.png)

多數符合條件的區段呈現：觀測週次增加，當週觀看次數傾向下降；負相關允許中途反彈。

其他圖表：
[英語與非英語比較](charts/02_english_vs_non_english_average_views.png) ·
[上榜項目最大累積週數](charts/03_top10_longest_stay_titles.png) ·
[四類榜單每週觀看時數](charts/04_weekly_total_hours_trend.png)。

五張完整圖表、敏感度分析與 TV 片長穩健性比較均收錄於[完整研究報告](docs/ANALYSIS_REPORT.md)。

## 5. 專案架構

```text
netflix-analysis/
├─ main.py                    # 下載、清洗、分析與繪圖入口
├─ scripts/
│  ├─ fetch_data.py            # 下載、Excel 驗證與安全儲存
│  ├─ clean_data.py            # 清洗、資料驗證與 CSV 輸出
│  ├─ analyze_data.py          # 五題分析與敏感度分析
│  └─ visualize.py             # 五張統計圖
├─ tests/                     # 離線 unittest 與正式 CSV 檢查入口
├─ charts/                    # 已提交的五張正式 PNG
├─ docs/
│  └─ ANALYSIS_REPORT.md       # 完整方法、結果、限制與重現說明
├─ README.md
├─ DEBUGGING.md               # 歷史除錯紀錄
└─ requirements.txt
```

`data/raw/` 的原始 Excel 與 `data/processed/` 的 CSV、預覽等資料產物僅保留本機，由 Git 忽略；Clone 後不保證存在這些資料夾或檔案。

## 6. 安裝與執行

### 環境與套件

已使用的環境為 **Python 3.14.3**，套件版本列於 [requirements.txt](requirements.txt)。
其他 Python 版本與全新環境安裝尚未完成最後驗收。

先 Clone 或下載專案，於 Windows PowerShell 切換至專案根目錄；以下假設目前位於專案的上一層資料夾：

```powershell
cd .\netflix-analysis
python -m venv .venv
.\.venv\Scripts\python.exe -X utf8 -m pip install -r requirements.txt
```

若已在專案根目錄，略過 `cd`。後續指令直接使用虛擬環境的 Python，不需啟用 PowerShell activation 腳本。

Matplotlib 需可用中文字型，本機正式圖使用 Microsoft JhengHei。
可用字型候選及環境限制見[研究報告第 11 節](docs/ANALYSIS_REPORT.md#11-資料重現與測試)。

### 執行最新資料完整流程

**執行下列命令前，請確認接受這些寫入行為：**

- 下載執行當時可取得的 Netflix 官方最新資料，成功時替換預設 raw 檔。
- 重新產生 `data/processed/netflix_top10_clean.csv`。
- **覆寫 `charts/` 中五張 PNG**。
- 資料與結果可能不同於本頁正式固定快照。

接受上述行為後，在專案根目錄執行：

```powershell
.\.venv\Scripts\python.exe -X utf8 main.py
```

預設原始輸出為 `data/raw/netflix_top10_raw.xlsx`，不會自動選取固定日期的原始 Excel。
此流程需要網路；只想查看成果或驗證程式時，可先使用下面的離線方式。

## 7. 固定快照與資料重現

| 目的 | 方式與前提 |
|---|---|
| 查看正式成果 | Clone 後直接閱讀已提交的五張圖與完整研究報告，不需原始資料 |
| 使用最新資料分析 | 執行 main.py，會下載及更新產物；不保證得到固定快照數字 |
| 重算正式固定基準 | 先持有 SHA-256 相符的 Excel 或 CSV，再以現有函式指定輸入及獨立輸出位置分步執行 |

固定快照不能只靠檔名或雜湊重新取得，也不能保證官方下載端點仍提供相同位元組。
分步範例見[研究報告第 11 節](docs/ANALYSIS_REPORT.md#11-資料重現與測試)，不需以完整 main.py 重下載。

## 8. 測試方式

所有命令均在專案根目錄執行，先安裝必要套件。

### 離線 unittest

**55 項離線測試不需要網路或正式 Netflix 快照**：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -t . -v
```

測試使用 mock HTTP、人造 DataFrame 及暫存目錄，涵蓋下載失敗／安全替換、資料驗證、季度識別、區段邊界、相關係數／敏感度，以及 CSV 讀寫串接五題分析與五圖輸出。

### 正式 CSV 檢查

須先持有預設位置的 `data/processed/netflix_top10_clean.csv`，且具備有效 views 與可分析區段：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m tests.test_analysis
```

此入口包含正式 CSV 品質與區段檢查，以及一項已知答案的相關係數案例。
它與離線測試不同；**55 項離線通過不等於 55 項真實 Netflix 資料驗證**。

Windows CP950 終端曾因列印成功勾號出現編碼錯誤，因此上述指令統一使用 `-X utf8`。

已完成離線整合與正式資料分步驗證；**新版完整 main.py 端到端執行及全新環境安裝仍待最後驗收**，詳細範圍見研究報告。

## 9. 研究限制與延伸閱讀

- 資料只涵蓋全球四類 Top 10 上榜項目，不代表 Netflix 全平台作品。
- `weekly_views` 不是獨立觀看人數；第一、二題採上榜項目－週平均。
- 缺少可靠的官方唯一作品 ID，同名電影與缺季度仍有識別限制。
- 第五題只描述符合五週條件的有效觀測區段，不代表完整上榜生命週期；相關不等於因果。
- 跨期比較須留意 2023 年排名方法變更、TV 片長變動及不完整年度，詳見完整報告。

延伸閱讀：

- [完整研究報告](docs/ANALYSIS_REPORT.md)：方法、正式數表、五張圖、敏感度與穩健性比較。
- [歷史除錯紀錄](DEBUGGING.md)：開發當時的錯誤診斷背景，並非目前未修正問題或新版資料摘要。
- [Netflix 官方資料](https://www.netflix.com/tudum/top10/data/all-weeks-global.xlsx)。
- [Netflix 官方 Top 10 方法說明](https://about.netflix.com/en/news/top-10-things-about-netflix-top-10)：閱讀時留意 2023 更新段落。
