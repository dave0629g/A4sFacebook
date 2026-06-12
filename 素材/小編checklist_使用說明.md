# 小編 Checklist 網頁 — 使用說明

一個給小編用的網頁待辦清單：**大字、高對比、可調字級、做完點一下方框就好**。點擊會即時記錄、關掉網頁也不會掉；搭檔和 `update.py` 都讀得到。

> 進度存哪裡會**自動切換**：本機自己跑 → 存 `素材/小編進度.json`；部署到 Streamlit Cloud → 存 **Google 試算表**（見下面做法 3）。網頁左下角會顯示目前用哪個。

## 它包含什麼

- `小編任務.yaml`：任務內容（要改任務就改這份，網頁立刻更新）
- `小編checklist.py`：Streamlit 網頁程式
- `progress_store.py`：進度存取（本機 json／Google 試算表自動切換）
- `小編進度.json`：本機模式的點擊紀錄（自動產生，不進 git）

## 在自己電腦先跑起來

> 以下指令都在**專案根目錄 `A4sFacebook/`** 執行（不要先 `cd 素材`，否則路徑會變成 `素材/素材/…`）。

```bash
pip3 install -r 素材/requirements.txt        # 第一次才要
streamlit run 素材/小編checklist.py
```

瀏覽器會自動開 `http://localhost:8501`。左側可調「字級」（大／特大／超大）。

## 怎麼讓「遠端的小編」也能用

小編在別的地方、要點得到這個網頁，三種做法，**推薦第 1 種**（小編的點擊會存在你電腦上、你和 Claude 都讀得到）：

### 1）你電腦跑、開一條臨時網址給小編（最推薦）

先裝好其中一個通道工具（擇一）：

```bash
brew install cloudflared      # 方案 cloudflared（推薦，免註冊）
brew install ngrok            # 方案 ngrok（需註冊取得 token）
# localtunnel 免安裝，直接用 npx 即可
```

再開兩個終端機（都在專案根目錄）：

```bash
# 終端機 A：把網頁跑起來
streamlit run 素材/小編checklist.py --server.port 8501

# 終端機 B：開一條公開網址（用上面裝好的那個）
cloudflared tunnel --url http://localhost:8501
# 或  npx localtunnel --port 8501
# 或  ngrok http 8501
```

把跳出來的網址（像 `https://xxxx.trycloudflare.com`）傳給小編，他用手機或電腦打開就能點。
**好處**：小編每次點擊都寫進你電腦的 `素材/小編進度.json`，你跑 `python3 素材/update.py` 就會把他的進度併進 `素材/狀態.md`，Claude 也讀得到。你的電腦要開著、網頁要跑著。

### 2）同一個 Wi-Fi（最省事，但要同網域）

跑起來後看終端機印的 `Network URL`（像 `http://172.20.10.2:8501`），同一個 Wi-Fi 下小編直接開那個就行。

### 3）部署到 Streamlit Community Cloud（小編隨時可開，固定網址）⭐

程式已內建：部署上雲、設好 Google 試算表 secrets 後，**點擊會自動存進你的 Google 試算表**（耐重啟、你和 Claude 都讀得到）。Main file path 填 **`streamlit_app.py`**。
完整一步步教學（建試算表、服務帳號、設 secrets、部署）見 **`素材/上線到StreamlitCloud教學.md`**。
網頁左下角會顯示「進度存放：Google 試算表（雲端）」代表接通成功；若顯示「本機檔」就是 secrets 還沒設好。

## 進度怎麼流回來

```
小編在網頁點方框  →  寫入 小編進度.json（本機）或 Google 試算表（雲端）
                      ↓
你跑 python3 素材/update.py（雲端模式需本機也放一份 secrets.toml）
                      ↓
素材/狀態.md 多出「小編自報進度」段（已點完幾項、最近完成時間）
```

雲端模式也可直接開 Google 試算表「進度」分頁看，或把連結貼給 Claude 讀。

## 注意

- 小編**只用這個網頁打勾**，不用碰 repo、不用改任何檔案。
- 執行產生的截圖、照片、影片**不從這個網頁上傳**，走原本管道（共用資料夾／LINE 相簿），見 `LINE相簿同步教學.md`。
- 要改任務文字／新增任務：改 `素材/小編任務.yaml`（保持每個 `id` 不重複），存檔後網頁重新整理就更新。
