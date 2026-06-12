# 讓雲端 checklist 把進度存進 Google 試算表（方案 B：不用服務帳號）

App 已經部署在 **https://a4sfacebook.streamlit.app/**。
現在要讓小編的點擊**寫進你的 Google 試算表**（耐重啟、你和 Claude 都讀得到）。方案 B 用一段 Apps Script 當寫入口，**不需要 Google 服務帳號**，約 5 分鐘。

> 原理：網頁把點擊 POST 到一條 Apps Script 網址，Apps Script 以「你」的身分把資料寫進進度試算表。一組 token 防止別人亂打。

進度試算表已建好，ID＝`1g7pnlAxo-gN3VEa52yrjBB9nZDhMtalSC0eu3gmgQ9Y`。

---

## 第 1 步｜貼上 Apps Script

1. 開「**票選活動_小編進度_checklist**」試算表 → 上方 **擴充功能 → Apps Script**
2. 把 `素材/checklist_webapp.gs` 全文貼進去（取代原本的 `myFunction`）
3. 把第一行的 `TOKEN` 改成你自己的隨機字串（例如 `uZBCc7b-Ul--2qSYkSgHvnLi`，自己挑一組也行）。**記住這組 token，第 3 步要用。**
4. 按 💾 儲存

## 第 2 步｜部署成網頁應用程式

1. 右上 **部署 → 新增部署作業**
2. 齒輪選類型 **「網頁應用程式」**
3. 設定：
   - 執行身分：**我（你自己）**
   - 誰可以存取：**任何人**
4. 按 **部署** → 第一次會要授權（出現「Google 尚未驗證」→ 左下「進階」→「前往…（不安全）」→「允許」，這是自寫程式的正常流程）
5. 複製 **「網頁應用程式」網址**（長得像 `https://script.google.com/macros/s/AKfy.../exec`）

## 第 3 步｜把網址與 token 填進 Streamlit Secrets

1. 到 [share.streamlit.io](https://share.streamlit.io) → 你的 app（a4sfacebook）→ 右下 **⋮ → Settings → Secrets**
2. 貼上（兩個值換成你的；token 要跟 .gs 裡一字不差）：

   ```toml
   checklist_webapp_url = "你第 2 步複製的 .../exec 網址"
   checklist_token = "你第 1 步設的那組隨機字串"
   ```
3. **Save** → App 會自動重啟

## 第 4 步｜確認接通

打開 https://a4sfacebook.streamlit.app/ ，左下角應顯示 **「進度存放：Google 試算表（Apps Script）」**。
隨便點一個方框 → 回「票選活動_小編進度_checklist」試算表，會看到「進度」分頁多了一列。成功！

之後把網址傳給小編就好，他點的每一下都會進這份試算表。

---

## 進度怎麼看

- **最直接**：開「票選活動_小編進度_checklist」試算表的「進度」分頁。
- **整理過的**：本機放一份同樣的 `.streamlit/secrets.toml`，跑 `python3 素材/update.py`，`素材/狀態.md` 會多出「小編自報進度」。
- **給 Claude 看**：把試算表連結貼給我即可。

## 出問題時

- **左下顯示「本機檔」而不是「Apps Script」**：secrets 沒存好，或 `checklist_webapp_url` 拼錯。
- **點了沒進試算表 / App 報錯**：多半是兩邊 token 不一致，或 Apps Script 部署的「誰可以存取」沒設成「任何人」。
- **改了 .gs 沒效果**：要「管理部署作業 → 編輯 → 版本：新版本 → 部署」，沿用舊版不會更新。
- **想更安全**：token 就是密碼，別外流；要換就兩邊一起改。

## 安全提醒

- token、Apps Script 網址別 commit 進 git（secrets 已被 `.gitignore` 擋）。
- 試算表只存「勾了沒＋時間＋任務文字」，沒有任何填答者個資。

---

## （備案）方案 A：服務帳號直連

若想改用 gspread 直連（不經 Apps Script），把 `requirements.txt` 的 `gspread`、`google-auth` 取消註解，secrets 改填 `progress_sheet_id` 與 `[gcp_service_account]`（見 `.streamlit/secrets.toml.範例` 下半）。程式會自動偵測採用。一般用方案 B 就夠了。
