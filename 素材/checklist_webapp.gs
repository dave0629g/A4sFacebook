/**
 * 小編 Checklist 進度 Web App（方案 B：不用服務帳號）
 *
 * 安裝（約 5 分鐘）：
 *   1) 開「票選活動_小編進度_checklist」試算表 → 擴充功能 → Apps Script
 *   2) 把本檔全文貼上，改下面 TOKEN 為你自己的隨機字串（要跟 Streamlit secrets 一致）
 *   3) 右上「部署 → 新增部署作業」→ 類型選「網頁應用程式」
 *        執行身分：我（你自己）
 *        誰可以存取：任何人
 *      → 部署 → 第一次會要授權（出現「未驗證」走進階→繼續→允許）→ 複製「網頁應用程式」網址（.../exec 結尾）
 *   4) 把網址與 TOKEN 填進 Streamlit App 的 Secrets（見 .streamlit/secrets.toml.範例）
 *
 *   之後若改了本程式，要「管理部署作業 → 編輯（鉛筆）→ 版本：新版本 → 部署」才會生效。
 */
const TOKEN = '___換成你自己的隨機字串___';   // 與 Streamlit secrets 的 checklist_token 一字不差
const TAB = '進度';

function _sheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();   // 本程式綁在進度試算表上
  let sh = ss.getSheetByName(TAB);
  if (!sh) { sh = ss.insertSheet(TAB); sh.appendRow(['task_id', 'done', 'ts', '任務']); }
  return sh;
}

function _json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// 讀進度：GET ?token=...
function doGet(e) {
  if (!e || (e.parameter.token || '') !== TOKEN) return _json({ error: 'bad token' });
  const rows = _sheet().getDataRange().getValues();
  const out = {};
  for (let i = 1; i < rows.length; i++) {
    const tid = rows[i][0], done = rows[i][1], ts = rows[i][2];
    if (tid && (done === true || String(done).toUpperCase() === 'TRUE')) {
      out[tid] = { done: true, ts: ts };
    }
  }
  return _json(out);
}

// 存進度：POST { token, progress:{tid:{done,ts}}, labels:{tid:文字} }
function doPost(e) {
  let body = {};
  try { body = JSON.parse(e.postData.contents); } catch (err) {}
  if ((body.token || '') !== TOKEN) return _json({ error: 'bad token' });
  const prog = body.progress || {}, labels = body.labels || {};
  const lock = LockService.getScriptLock();
  try { lock.waitLock(10000); } catch (err) { return _json({ error: 'busy' }); }
  try {
    const sh = _sheet();
    const rows = [['task_id', 'done', 'ts', '任務']];
    for (const tid in prog) {
      if (prog[tid] && prog[tid].done) rows.push([tid, 'TRUE', prog[tid].ts || '', labels[tid] || '']);
    }
    sh.clearContents();
    sh.getRange(1, 1, rows.length, 4).setValues(rows);
    return _json({ ok: true, count: rows.length - 1 });
  } finally {
    lock.releaseLock();
  }
}
