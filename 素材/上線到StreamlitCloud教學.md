# 把小編 Checklist 上線到 Streamlit Cloud（含 Google 試算表存進度）

目標：給小編一個固定網址、隨時可開的待辦網頁；他的每次點擊存進一個 **Google 試算表**，重啟不掉，你和 Claude 都讀得到。

> 為什麼要 Google 試算表？Streamlit Cloud 的硬碟是暫存的，App 一休眠/重啟，存在伺服器上的點擊就歸零、也沒人讀得到。把進度寫進你自己的 Google 試算表才耐久、才看得到。

全程約 15 分鐘，照下面五步做。

---

## 第 1 步｜開一個 Google 試算表

1. 到 [sheets.new](https://sheets.new) 開一個空白試算表，命名「票選活動_小編進度」
2. 看網址：`https://docs.google.com/spreadsheets/d/`**`這一段就是試算表 ID`**`/edit`
3. 把這個 ID 記下來（等下要填）。分頁不用自己建，程式第一次寫入會自動建「進度」分頁。

## 第 2 步｜建一個 Google 服務帳號＋金鑰

「服務帳號」是一個讓程式代替你寫試算表的機器人帳號。

1. 到 [console.cloud.google.com](https://console.cloud.google.com) → 上方建立或選一個專案
2. 搜尋並進入 **「Google Sheets API」** → 按 **啟用**
   （程式只用到 Sheets API 就夠；若日後出現 403／SpreadsheetNotFound，再回來一併啟用「Google Drive API」即可）
3. 左側「IAM 與管理」→ **「服務帳戶」** → **建立服務帳戶** → 取名如 `checklist-bot` → 一路「完成」（角色可留空，我們用試算表共用來授權）
4. 點進剛建的服務帳戶 → 上方 **「金鑰」** → **新增金鑰 → 建立新的金鑰 → JSON** → 會下載一個 `.json` 檔（**這就是金鑰，別外流、別 commit**）
5. 複製服務帳戶的 email（長得像 `checklist-bot@專案.iam.gserviceaccount.com`）

## 第 3 步｜把試算表分享給服務帳號

1. 回到第 1 步的 Google 試算表 → 右上 **「共用」**
2. 貼上第 2 步那個服務帳戶 email → 權限選 **「編輯者」** → 傳送
   （會說無法寄通知，沒關係，照樣生效）

## 第 4 步｜部署到 Streamlit Cloud

repo 已經在 GitHub（`dave0629g/A4sFacebook`），直接部署：

1. 到 [share.streamlit.io](https://share.streamlit.io) → 用 GitHub 登入、授權
2. **Create app → Deploy a public app from GitHub**
3. 填：
   - **Repository**：`dave0629g/A4sFacebook`
   - **Branch**：`main`
   - **Main file path**：`streamlit_app.py`
4. 點 **Advanced settings → Secrets**，把下面整段貼進去（值換成你的；格式照 `.streamlit/secrets.toml.範例`）：

   ```toml
   progress_sheet_id = "第1步記下的試算表 ID"

   [gcp_service_account]
   # 把第 2 步下載的 JSON 各欄位照填；private_key 連同 \n 整段照貼
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "checklist-bot@專案.iam.gserviceaccount.com"
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."
   ```
5. 按 **Deploy**，等 1–2 分鐘。成功後會得到網址 `https://xxxx.streamlit.app`

## 第 5 步｜把網址給小編

把那條 `.streamlit.app` 網址傳給小編就好。他在手機或電腦打開、點方框，進度就寫進你的 Google 試算表。左側可調字級（大／特大／超大）。

---

## 進度怎麼看

- **最直接**：打開第 1 步那個 Google 試算表，看「進度」分頁（含 task_id、done、時間、任務文字）。
- **要看整理過的**：在你電腦放一份同樣的 `.streamlit/secrets.toml`、`pip3 install gspread google-auth`，跑 `python3 素材/update.py`，`素材/狀態.md` 會多出「小編自報進度」。
- **給 Claude 看**：把試算表連結貼給我，我用 Google Drive 讀進度。

## 安全提醒

- 服務帳號 JSON、secrets **絕不要 commit**（`.gitignore` 已擋 `.streamlit/secrets.toml` 與 `*service_account*.json`）。
- 試算表只存「勾了沒＋時間＋任務文字」，沒有任何填答者個資。
- 怕金鑰外流可隨時到 Google Cloud Console 把那把金鑰刪掉、重建。

## 出問題時

- **網頁顯示「進度存放：本機檔」而不是「Google 試算表」**：secrets 沒設好或試算表沒分享給服務帳號 email；對一下第 2–4 步。
- **Deploy 失敗、找不到套件**：確認用的是 repo 根目錄的 `requirements.txt`（已含 gspread、google-auth）。
- **權限錯誤（PermissionError / 403）**：第 3 步的試算表共用 email 要跟 secrets 裡的 `client_email` 完全一致、且是「編輯者」。
