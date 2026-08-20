## 1. runtime 出現 0 導致資料品質測試失敗

### 錯誤現象

執行基本測試：
```powershell
python -m tests.test_analysis
```
在 `test_data_quality()` 執行資料品質檢查時發生 `AssertionError`。

原本的測試條件為：
```python
assert (df["runtime"].dropna() > 0).all(), "runtime 有效資料應大於 0"
```
這個測試會先使用 `dropna()` 排除缺失值，再檢查所有有效的 `runtime` 是否都大於 0。

---

### Traceback 重點

Traceback 顯示錯誤發生在：
```text
tests/test_analysis.py
```
並且是在 `test_data_quality()` 中檢查 `runtime` 的 `assert` 條件時失敗。

因此可以判斷：

1. 問題不是 NaN，因為測試已經使用 `dropna()` 排除缺失值。
2. 至少有一筆有效的 `runtime` 數值小於或等於 0。
3. 需要進一步檢查實際資料內容。

---

### 檢查方式

使用以下程式找出異常的 `runtime`：
```python
from scripts.analyze_data import load_data

df = load_data()
invalid_runtime = df[
    df["runtime"].notna() & (df["runtime"] <= 0)
]
print("runtime <= 0 的筆數：", len(invalid_runtime))
print(invalid_runtime)
```

檢查結果：
```text
runtime <= 0 的筆數：167
```

其中可以看到例如：
```text
2026-08-02
TV (Non-English)
The Apartment Job
The Apartment Job: Limited Series
runtime = 0.0
weekly_views = 1700000.0
```

這表示資料中確實存在 `runtime = 0.0` 的紀錄。

---

### 錯誤原因

`runtime` 代表作品片長，因此正常情況下應該大於 0。
但原始 Netflix 資料中存在部分 `runtime = 0.0` 的資料，共找到 167 筆。
這些 0 並不是合理的作品片長，比較適合視為缺失或無效資料。

因此原本的測試本身沒有錯，而是資料清洗階段尚未處理 `runtime <= 0` 的異常值，造成：
```python
(df["runtime"].dropna() > 0).all()
```
回傳 `False`，進而產生 `AssertionError`。

---

### 修正方式

在 `clean_data.py` 的資料清洗流程中加入條件，將 `runtime <= 0` 的資料轉換為缺失值。

```python
df.loc[df["runtime"] <= 0, "runtime"] = pd.NA
```

完成清洗後重新產生處理後資料，再執行：
```powershell
python -m tests.test_analysis
```
修正後，`runtime` 的有效資料皆大於 0，資料品質測試即可正常通過。

---

### 除錯流程

這次的除錯流程為：

```text
執行基本測試
→ 發生 AssertionError
→ 查看 Traceback
→ 找到 test_data_quality() 的 runtime 檢查
→ 確認 dropna() 已排除 NaN
→ 推測資料中存在 runtime <= 0
→ 篩選異常資料
→ 發現共有 167 筆 runtime <= 0
→ 確認其中存在 runtime = 0.0
→ 修改 clean_data.py 處理異常值
→ 重新產生清洗資料
→ 再次執行測試
→ 測試通過
```

### 除錯心得

原本的程式已經使用 `dropna()`，因此可以先排除 NaN 是直接原因，再透過篩選資料找出真正不符合條件的數值。
最後確認問題來自原始資料中的 `runtime = 0.0`，並回頭在資料清洗階段處理。
這也讓我了解測試的用途不只是確認程式能不能執行，也可以協助發現資料清洗流程中遺漏的異常資料。




## 2. 將 mean() 誤寫成 maen()，造成 AttributeError

### 錯誤現象

在進行第四題「Netflix 每週總觀看時數趨勢」分析時，程式執行到年度平均觀看時數計算時發生錯誤。

Traceback：
```text
Traceback (most recent call last):

  File "c:\Projects\netflix-analysis\scripts\analyze_data.py", line 147, in <module>

    yearly_avg_hours = weekly_trend.groupby(weekly_trend.index.year).maen()

  File "C:\Projects\netflix-analysis\.venv\Lib\site-packages\pandas\core\groupby\groupby.py", line 1115, in __getattr__

    raise AttributeError(
        f"'{type(self).__name__}' object has no attribute '{attr}'"
    )

AttributeError: 'SeriesGroupBy' object has no attribute 'maen'
```

---

### Traceback 解讀

首先從 Traceback 最後一行查看實際錯誤類型：
```text
AttributeError: 'SeriesGroupBy' object has no attribute 'maen'
```

`AttributeError` 表示目前這個物件沒有名稱為 `maen` 的屬性或方法。

錯誤訊息中：
```text
has no attribute 'maen'
```

判斷問題出現在 `.maen()`。

---

### 錯誤原因

原本要使用 Pandas 的平均值方法：
```python
mean()
```

但程式碼誤打成：
```python
maen()
```

因此：
```python
weekly_trend.groupby(weekly_trend.index.year)
```

產生的 `SeriesGroupBy` 物件找不到 `maen()` 這個方法，Python 因此拋出 `AttributeError`。
這是方法名稱的拼字錯誤。

---

### 修正方式

將錯誤的：
```python
.maen()
```

修改為：
```python
.mean()
```

重新執行程式後，即可正常計算各年度的平均每週總觀看時數。

---

### 除錯流程

```text
執行 analyze_data.py
→ 程式發生 AttributeError
→ 從 Traceback 最後一行確認錯誤類型
→ 發現 mean() 拼錯成 maen()
→ 修正為 mean()
→ 重新執行程式
→ 年度平均觀看時數正常計算
```

### 除錯心得

這次錯誤讓我練習如何利用 Traceback 快速找到問題。
閱讀 Traceback 時，可以先從最後一行確認錯誤類型與錯誤訊息，再往上找到自己撰寫的程式檔案與行數。
這次最後一行直接指出：

```text
'SeriesGroupBy' object has no attribute 'maen'
```

因此可以優先檢查 `maen` 這個方法名稱，最後發現只是將 Pandas 的 `mean()` 拼錯。


