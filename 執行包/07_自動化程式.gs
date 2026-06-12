/**
 * 福爾摩沙不惑之聲「演後票選 × 抽獎」自動化程式
 * 使用方式見《08_自動化使用說明.md》：
 * 建一個新的 Google 試算表 → 擴充功能 → Apps Script → 全文貼上 → 儲存
 * → 重新整理試算表 → 上方出現「🎵 票選活動」選單，依序點選即可。
 */

// ════════════ 設定區（開跑前只需要改這裡；引號逗號規則見 08 安裝第 4 步） ════════════
const CONFIG = {
  CONCERT_NAME: '《走找青春》',              // 音樂會名稱（含書名號，會直接串進表單標題）
  SONGS: [                                   // 本場 23 首曲目，照節目單順序（建表之後就不可再改）
    // I. 國王歌手伴我成長
    'You Are the New Day 你是嶄新的一天',
    'Come Again, Sweet Love 再來吧，甜蜜的愛正在邀請',
    'Lullaby, My Sweet Little Baby 睡吧，我親愛的小寶貝',
    'Il bianco e dolce cigno 銀白而優雅的天鵝',
    'Fine Knacks for Ladies 給女士們的精緻小玩意',
    'Say, Love, If Ever Thou Didst Find 告訴我，愛神',
    'The Silver Swan 銀白天鵝',
    'Fair Phyllis I saw 我曾見美麗的菲莉絲',
    // II. 少年不識愁滋味
    'Vincent 文森',
    'Yesterday Once More 昨日再現',
    '河邊春夢',
    '你是我所有的回憶',
    '聽泉',
    '橄欖樹',
    // III. 如果可以重來
    '少年時代',
    '手紙～拝啓 十五の君へ',
    '島唄',
    // IV. 青春未曾消逝，只是蛻變為另一種詮釋
    '世界恬靜落來的時',
    '紅田嬰',
    '糖ㄅㄅ',
    '頭擺的妳',
    '走找青春',
    '青春嶺',
  ],
  MEMBERS: [                                 // 全體團員 39 位（第 3 題下拉選單用）
    // ⚠️ 個資去識別化：真實名單不放公開 repo。
    // 請開啟本機的「執行包/LOCAL_私密資料.md」（或向幹部索取），
    // 把整段 MEMBERS 區塊取代掉下面三行佔位符。
    '【團員1】', '【團員2】', '【團員3】',
  ],
  CLOSE_AT: '2026-06-25 21:00',              // 自動關閉時間，格式固定 YYYY-MM-DD HH:mm（台灣時間）
  CLOSE_TEXT: '6/25（四）晚上 9:00',          // 對外顯示的截止文字（要跟 CLOSE_AT 一致）
  ANNOUNCE_TEXT: '6/27（六）晚上 8 點',       // 對外顯示的開獎文字
  // ⚠️ 時程整體平移時，CLOSE_AT、CLOSE_TEXT、ANNOUNCE_TEXT 三個要一起改
  RULES_URL: '【辦法短網址】',                // 活動辦法 Google 文件短網址（先做 01 的步驟 0 才有得填）
  PAGE_URL: 'https://www.facebook.com/a4ssingers',
  CONTACT_EMAIL: 'a4ssingers@gmail.com',
  WEIGHT_FIRST: 2,                           // 計分：第一喜歡
  WEIGHT_SECOND: 1,                          // 計分：第二喜歡
  WINNERS: 5,                                // 正取
  BACKUPS: 2,                                // 備取
};

// 題目標題（建表與讀取共用；改了會對不上資料，沒事別動）
const Q = {
  VOTE: '本場音樂會，你最喜歡的兩首曲子是？',
  NICK: '你的暱稱或 FB 顯示名稱',
  INVITER: '邀請你來聽音樂會的團員是？',
  CONTACT: 'Email 或手機（僅用於中獎聯絡）',
  FEEDBACK: '想對我們說的話（選填）',
  PUBLISH_OK: '聽後感刊登同意（選填）',
  FOLLOW: '你追蹤我們的粉絲專頁了嗎？',
  NEXT_EMAIL: '想第一時間收到下次演出資訊嗎？留下 Email（選填）',
  PDPA: '個人資料蒐集同意',
  MINOR: '未滿 18 歲填答者請勾選（選填）',
};
const RANK1 = '第一喜歡';
const RANK2 = '第二喜歡';

// ════════════ 選單 ════════════
function onOpen() {
  SpreadsheetApp.getUi().createMenu('🎵 票選活動')
    .addItem('① 建立表單', 'step1_buildForm')
    .addItem('② 設定自動關閉', 'step2_scheduleClose')
    .addItem('③ 更新進度報表（活動期間隨時可按）', 'step3_progress')
    .addItem('④ 截止後整理＋計票', 'step4_finalize')
    .addItem('⑤ 產生轉盤名單／備用抽獎', 'step5_draw')
    .addItem('⑥ 結案：轉存Email＋清除個資', 'step6_cleanup')
    .addToUi();
}

// ════════════ ① 建立表單 ════════════
function step1_buildForm() {
  const ui = SpreadsheetApp.getUi();
  if (PropertiesService.getScriptProperties().getProperty('FORM_ID')) {
    ui.alert('表單已建立過。若要重建，請依序做完三步再按一次①：\n' +
      '1. 擴充功能→Apps Script→專案設定→指令碼屬性→刪除 FORM_ID\n' +
      '2. 在舊的「表單回應」分頁標籤按右鍵→「取消連結表單」→ 再刪除該分頁（不刪的話，之後統計會讀到舊資料）\n' +
      '3. 到 forms.google.com 把舊表單移到垃圾桶');
    return;
  }
  const desc =
    '謝謝你來聽我們的音樂會！邀請你花 1 分鐘，選出本場你最喜歡的兩首曲子——得票最高的曲子，將列入我們下次演出的安可候選曲目。\n\n' +
    '完成曲目票選並送出表單即可參加抽獎（曲目票選全空白者恕不具抽獎資格），我們將抽出 ' + CONFIG.WINNERS + ' 位幸運得主（另抽備取 ' + CONFIG.BACKUPS + ' 位），獎品每人擇一：A. 本團自得獎日起一年內任一場音樂會入場券一張；B. 福爾摩沙合唱團《30週年音樂會》紀念 USB 一個。本團團員及其同住家屬可投票，但不參與抽獎。\n\n' +
    '⏰ 截止：' + CONFIG.CLOSE_TEXT + '\n' +
    '🎁 開獎：' + CONFIG.ANNOUNCE_TEXT + ' 於本團粉絲專頁公布 → ' + CONFIG.PAGE_URL + '\n' +
    '📜 完整活動辦法：' + CONFIG.RULES_URL + '\n\n' +
    '【依個人資料保護法第 8 條告知】\n' +
    '1. 蒐集者：福爾摩沙不惑之聲合唱團（下稱本團）。\n' +
    '2. 蒐集目的：本次票選統計、抽獎執行、得獎通知、獎品交付；如您留下「下次演出通知」Email，另包含本團演出資訊之寄送；如您勾選同意刊登，另包含聽後感之引用刊登。\n' +
    '3. 個資類別：暱稱／FB 名稱、聯絡方式（Email 或手機）與填答內容；中獎者如獎品市值超過 NT$1,000，將另行蒐集姓名、身分證統一編號與戶籍地址以依法辦理稅務申報。\n' +
    '4. 利用期間／地區／對象：一般填答資料利用至活動結束後 30 日，未中獎者資料將於活動結束後 30 日內刪除；利用地區為台灣，利用對象為本團。您的暱稱將顯示於公開之抽獎畫面截圖，得獎名單（姓名部分遮蔽）將公布於本團粉絲專頁；中獎者稅務資料將依法提供稅捐稽徵機關，並保存至申報完成後 5 年。如您留下「下次演出通知」Email，即表示同意本團將該 Email 用於寄送演出資訊並保存至您通知停止為止（可隨時要求刪除），不受前述 30 日期限限制；經您同意刊登之聽後感與領獎照片將刊登於粉絲專頁，至您通知撤回為止。\n' +
    '5. 您得依個資法第 3 條行使查詢、閱覽、複製、補充更正、停止蒐集處理利用及刪除等權利，聯絡方式：粉專私訊或 ' + CONFIG.CONTACT_EMAIL + '。\n' +
    '6. 您可自由選擇是否提供；不提供必填欄位將無法參加票選與抽獎；中獎者不提供稅務申報所需資料者，視同放棄領獎，由備取遞補。\n' +
    '7. 未滿 18 歲者請先取得法定代理人同意。\n\n' +
    '本活動由福爾摩沙不惑之聲合唱團主辦，與 Facebook（Meta）無關，並非由其贊助、支持或管理；參加者並同意完全免除 Facebook（Meta）就本活動之一切責任。主辦單位保留修改、暫停或終止本活動之權利，異動將於粉絲專頁公告。';

  // 2026/6/30 後 API 建立的表單預設「未發布」（Google 官方既定改版日），第二參數明確指定發布
  const form = FormApp.create(
    '福爾摩沙不惑之聲' + CONFIG.CONCERT_NAME + '演後票選 × 好禮抽獎',
    /* isPublished= */ true
  );
  form.setDescription(desc);
  form.setCollectEmail(false);
  form.setLimitOneResponsePerUser(false); // 不強迫登入 Google（避免卡死 LINE/Messenger 內建瀏覽器）
  form.setConfirmationMessage(
    '投票完成，謝謝你！🎉\n得獎名單與票選結果將於 ' + CONFIG.ANNOUNCE_TEXT + ' 在我們的粉專公布——演出照片這幾天也會陸續放上去，來找找你的身影：\n👉 ' +
    CONFIG.PAGE_URL + '\n（追蹤粉專＋按讚貼文，開獎才不會錯過！）'
  );

  form.addGridItem().setTitle(Q.VOTE)
    .setHelpText('曲目依節目單順序排列。請「恰好」勾選兩首：一首第一喜歡、一首第二喜歡。若只勾一首，將僅計入第一喜歡。未勾選任何曲目者無法參加抽獎。')
    .setRows(CONFIG.SONGS).setColumns([RANK1, RANK2])
    .setValidation(
      FormApp.createGridValidation()
        .setHelpText('每個名次只能選一首曲子')
        .requireLimitOneResponsePerColumn()
        .build()
    );
  form.addTextItem().setTitle(Q.NICK).setHelpText('對獎與公布得獎名單用').setRequired(true);
  form.addListItem().setTitle(Q.INVITER)
    .setChoiceValues(CONFIG.MEMBERS.concat(['我自己來的／從粉專看到'])).setRequired(true);
  form.addTextItem().setTitle(Q.CONTACT).setRequired(true);
  form.addParagraphTextItem().setTitle(Q.FEEDBACK)
    .setHelpText('精彩的留言我們可能以暱稱引用刊登於粉專——同意刊登才需勾下一題。');
  form.addCheckboxItem().setTitle(Q.PUBLISH_OK)
    .setChoiceValues(['我同意本團以暱稱引用我的聽後感刊登於粉絲專頁']);
  form.addMultipleChoiceItem().setTitle(Q.FOLLOW)
    .setHelpText('粉專在這裡 → ' + CONFIG.PAGE_URL + ' （追蹤不是參加條件，也不影響中獎與領獎資格；領獎時若你願意，歡迎出示「追蹤中」畫面一起合影留念 😄）')
    .setChoiceValues(['已經追蹤了！', '我這就去追蹤（先送出表單，送出後的感謝頁就有粉專連結，才不會漏填）', '還沒，先不用'])
    .setRequired(true);
  form.addTextItem().setTitle(Q.NEXT_EMAIL);
  form.addCheckboxItem().setTitle(Q.PDPA)
    .setChoiceValues(['我已閱讀並同意表單開頭之個資告知事項']).setRequired(true);
  form.addCheckboxItem().setTitle(Q.MINOR)
    .setChoiceValues(['我已取得法定代理人同意參加本活動並提供個人資料']);

  if (!form.isPublished()) form.setPublished(true); // 保險：確保表單可作答
  form.setDestination(FormApp.DestinationType.SPREADSHEET, SpreadsheetApp.getActiveSpreadsheet().getId());
  PropertiesService.getScriptProperties().setProperty('FORM_ID', form.getId());

  ui.alert('✅ 表單建好了！（「每欄僅限一則回應」與「發布」已由程式自動設定）\n\n' +
    '還有 2 件請手動完成：\n\n' +
    '1. 打開表單編輯頁，確認右上「發布」狀態為可作答，取得「回覆者連結」拿去縮短網址\n' +
    '2. 用手機 LINE/Messenger 實測一次再開放\n\n' +
    '表單編輯頁：' + form.getEditUrl() + '\n填答連結：' + form.getPublishedUrl());
}

// ════════════ ② 自動關閉 ════════════
function step2_scheduleClose() {
  const at = new Date(CONFIG.CLOSE_AT.replace(' ', 'T') + ':00+08:00');
  if (isNaN(at) || at < new Date()) {
    SpreadsheetApp.getUi().alert('CLOSE_AT 設定有誤或已過期：' + CONFIG.CLOSE_AT);
    return;
  }
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'closeForm_') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('closeForm_').timeBased().at(at).create();
  SpreadsheetApp.getUi().alert('✅ 已排程：' + CONFIG.CLOSE_AT + ' 自動關閉表單。\n（Google 觸發器可能延遲數分鐘、只晚不早；幹部仍設一個鬧鐘核對）');
}

function closeForm_() {
  const id = PropertiesService.getScriptProperties().getProperty('FORM_ID');
  if (!id) return;
  const form = FormApp.openById(id);
  form.setAcceptingResponses(false);
  form.setCustomClosedFormMessage('票選已於 ' + CONFIG.CLOSE_TEXT + ' 截止，謝謝參與！' + CONFIG.ANNOUNCE_TEXT + ' 粉專開獎見 → ' + CONFIG.PAGE_URL);
}

// ════════════ 共用 ════════════
function responseSheet_() {
  const sheets = SpreadsheetApp.getActiveSpreadsheet().getSheets();
  for (var i = 0; i < sheets.length; i++) {
    if (sheets[i].getFormUrl()) return sheets[i]; // 官方 API：有連結表單的分頁就是回覆表
  }
  throw new Error('找不到表單回覆工作表（請先執行「① 建立表單」，且至少要有 1 筆回覆）');
}

function readResponses_() {
  const sheet = responseSheet_();
  const data = sheet.getDataRange().getValues();
  const headers = data[0].map(String);
  const col = function (title) {
    for (var i = 0; i < headers.length; i++) if (headers[i].indexOf(title) === 0) return i;
    throw new Error('回覆表找不到欄位：「' + title + '」。表單題目可能被手動改過，請改回原文字再執行。');
  };
  const idx = {
    nick: col(Q.NICK), inviter: col(Q.INVITER), contact: col(Q.CONTACT),
    feedback: col(Q.FEEDBACK), publishOk: col(Q.PUBLISH_OK), follow: col(Q.FOLLOW),
    email: col(Q.NEXT_EMAIL),
  };
  const songCols = {};
  CONFIG.SONGS.forEach(function (song) {
    var h = Q.VOTE + ' [' + song + ']'; // 連動工作表方格題標頭固定格式：「題目 [列名]」，精確比對最安全
    for (var i = 0; i < headers.length; i++) {
      if (headers[i] === h) { songCols[song] = i; break; }
    }
  });
  const missing = CONFIG.SONGS.filter(function (s) { return songCols[s] === undefined; });
  if (missing.length) {
    throw new Error('回覆表找不到這些曲目的欄位（建表後改過 CONFIG.SONGS 或表單題目？）：' + missing.join('、'));
  }
  const rows = [];
  for (var r = 1; r < data.length; r++) {
    var votes = {};
    Object.keys(songCols).forEach(function (song) {
      var v = String(data[r][songCols[song]]).trim();
      if (v === RANK1 || v === RANK2) votes[song] = v;
    });
    rows.push({
      ts: data[r][0],
      nick: String(data[r][idx.nick] || '').trim(),
      inviter: String(data[r][idx.inviter] || '').trim(),
      contact: String(data[r][idx.contact] || '').trim(),
      feedback: String(data[r][idx.feedback] || '').trim(),
      publishOk: String(data[r][idx.publishOk] || '').trim() !== '',
      follow: String(data[r][idx.follow] || '').trim(),
      email: String(data[r][idx.email] || '').trim(),
      votes: votes,
    });
  }
  return rows;
}

function exclusions_() {
  // 「排除名單」分頁：A 欄＝暱稱、B 欄＝類型（「測試」或「團員家屬」）。沒有此分頁則自動建立。
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName('排除名單');
  if (!sh) {
    sh = ss.insertSheet('排除名單');
    sh.getRange(1, 1, 1, 2).setValues([['暱稱', '類型（測試／團員家屬）']]);
    return { test: Object.create(null), member: Object.create(null) };
  }
  const out = { test: Object.create(null), member: Object.create(null) };
  sh.getDataRange().getValues().slice(1).forEach(function (r) {
    var nick = String(r[0]).trim().toLowerCase();
    if (!nick) return;
    if (String(r[1]).indexOf('測試') !== -1) out.test[nick] = true;
    else out.member[nick] = true;
  });
  return out;
}

function writeSheet_(name, rows) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(name);
  if (sh) sh.clear(); else sh = ss.insertSheet(name);
  if (rows.length) sh.getRange(1, 1, rows.length, rows[0].length).setValues(rows);
  return sh;
}

// ════════════ ③ 進度報表 ════════════
function step3_progress() {
  const rows = readResponses_();
  const ex = exclusions_();
  const live = rows.filter(function (x) { return !ex.test[x.nick.toLowerCase()]; });
  const byInviter = {};
  live.forEach(function (x) {
    if (!byInviter[x.inviter]) byInviter[x.inviter] = [];
    byInviter[x.inviter].push(x.nick);
  });
  const followYes = live.filter(function (x) { return x.follow.indexOf('還沒') === -1; }).length;
  const out = [
    ['更新時間', new Date()],
    ['總填答數（含重複，已扣測試）', live.length],
    ['自我聲明已追蹤／這就去追蹤', followYes + '（' + (live.length ? Math.round(followYes * 100 / live.length) : 0) + '%）'],
    ['留 Email 訂閱下次演出', live.filter(function (x) { return x.email; }).length],
    ['', ''],
    ['邀請團員', '已填者暱稱（6/18 提醒用：私訊各團員他自己的這一列）'],
  ];
  Object.keys(byInviter).sort().forEach(function (k) {
    out.push([k + '（' + byInviter[k].length + '）', byInviter[k].join('、')]);
  });
  writeSheet_('進度', out);
  SpreadsheetApp.getUi().alert('✅ 「進度」分頁已更新。');
}

// ════════════ ④ 截止後整理＋計票 ════════════
function step4_finalize() {
  const ui = SpreadsheetApp.getUi();
  const rows = readResponses_();
  const ex = exclusions_();
  if (Object.keys(ex.test).length + Object.keys(ex.member).length === 0) {
    const go = ui.alert('「排除名單」還是空的',
      '測試回覆和團員家屬都還沒填進「排除名單」分頁。\n直接繼續的話，測試資料會混進計票與公開抽獎畫面。\n\n確定真的不需要排除任何人，直接繼續？',
      ui.ButtonSet.YES_NO);
    if (go !== ui.Button.YES) return;
  }
  const summary = { 原始: rows.length, 測試: 0, 重複: 0, 無效票: 0, 需人工: 0, 迴避: 0 };

  var live = rows.filter(function (x) {
    if (ex.test[x.nick.toLowerCase()]) { summary.測試++; return false; }
    return true;
  });

  // 去重：暱稱＋聯絡方式相同者取最後一筆
  const seen = {};
  live.forEach(function (x) {
    var key = x.nick.toLowerCase() + '|' + x.contact.toLowerCase();
    if (!seen[key] || x.ts > seen[key].ts) {
      if (seen[key]) summary.重複++;
      seen[key] = x;
    } else summary.重複++;
  });
  live = Object.keys(seen).map(function (k) { return seen[k]; });

  // 有效性檢查
  const valid = [], manual = [];
  live.forEach(function (x) {
    const songs = Object.keys(x.votes);
    const firsts = songs.filter(function (s) { return x.votes[s] === RANK1; });
    const seconds = songs.filter(function (s) { return x.votes[s] === RANK2; });
    if (songs.length === 0) { summary.無效票++; return; }            // 全空白＝無效，不入計票不入抽獎
    if (firsts.length > 1 || seconds.length > 1) {                    // 方格驗證失效時才會發生
      summary.需人工++; manual.push(x); return;
    }
    if (songs.length === 1 && seconds.length === 1) {                 // 活動規則：只勾一首一律「僅計入第一喜歡」
      x.votes[songs[0]] = RANK1;
    }
    valid.push(x);
  });

  // 計票
  const score = {};
  CONFIG.SONGS.forEach(function (s) { score[s] = { f: 0, s: 0 }; });
  valid.forEach(function (x) {
    Object.keys(x.votes).forEach(function (song) {
      if (x.votes[song] === RANK1) score[song].f++;
      else score[song].s++;
    });
  });
  const tally = CONFIG.SONGS.map(function (s) {
    return [s, score[s].f, score[s].s, score[s].f * CONFIG.WEIGHT_FIRST + score[s].s * CONFIG.WEIGHT_SECOND];
  }).sort(function (a, b) { return b[3] - a[3] || b[1] - a[1]; });   // 同加權分者，第一喜歡票數多者在前
  writeSheet_('計票結果', [['曲目', RANK1 + '票數', RANK2 + '票數', '加權分（' + CONFIG.WEIGHT_FIRST + '/' + CONFIG.WEIGHT_SECOND + '；同分以第一喜歡票數多者在前）']].concat(tally));

  // 抽獎池（有效者扣除團員家屬）
  const pool = valid.filter(function (x) {
    if (ex.member[x.nick.toLowerCase()]) { summary.迴避++; return false; }
    return true;
  });
  const poolRows = [['編號', '暱稱', '填答時間', '邀請團員', '聯絡方式']];
  pool.forEach(function (x, i) { poolRows.push([i + 1, x.nick, x.ts, x.inviter, x.contact]); });
  writeSheet_('抽獎池', poolRows);

  // 需人工判定清單
  if (manual.length) {
    writeSheet_('需人工判定', [['暱稱', '填答時間', '說明']].concat(manual.map(function (x) {
      return [x.nick, x.ts, '同一名次勾了多首（方格驗證可能失效）。認定有效者：手動補進「抽獎池」最後一列（編號接續），其票數也要手動加進「計票結果」。補完之後不要再按④，會把手動修改全部洗掉'];
    })));
  }

  // 已同意刊登的聽後感（與投票有效性無關，從去重後全名單取）
  const fb = live.filter(function (x) { return x.feedback && x.publishOk; });
  writeSheet_('聽後感_可刊登', [['暱稱', '聽後感']].concat(fb.map(function (x) { return [x.nick, x.feedback]; })));

  const joined = valid.length + manual.length;
  writeSheet_('整理摘要', [
    ['項目', '數量'],
    ['原始回覆', summary.原始], ['剔除：測試', summary.測試], ['剔除：重複（取最後一筆）', summary.重複],
    ['剔除：無效票（票選全空白）', summary.無效票], ['需人工判定', summary.需人工],
    ['【參加人數】（貼文 4/5 用：去重有效填答人數；含需人工判定 ' + summary.需人工 + ' 筆，認定剔除後請以修正後數字為準）', joined],
    ['剔除：團員家屬（不入抽獎池）', summary.迴避], ['抽獎池人數', pool.length],
  ]);
  ui.alert('✅ 整理完成。請依序檢查：整理摘要 → 需人工判定（如有）→ 計票結果 → 抽獎池。\n⚠️ 人工補過資料後就不要再按④，會整份重寫。');
}

// ════════════ ⑤ 轉盤名單／備用抽獎 ════════════
function step5_draw() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const pool = ss.getSheetByName('抽獎池');
  if (!pool) { SpreadsheetApp.getUi().alert('請先執行「④ 截止後整理」'); return; }
  const data = pool.getDataRange().getValues().slice(1);
  if (data.length < CONFIG.WINNERS + CONFIG.BACKUPS) {
    SpreadsheetApp.getUi().alert('抽獎池人數不足（' + data.length + ' 人）'); return;
  }
  // 轉盤名單：一人一列，整欄複製才不會被剪貼簿加上引號
  const wheelRows = [['選取下面整欄複製，貼到 wheelofnames.com（一格一人）']];
  data.forEach(function (r) { wheelRows.push([r[0] + '-' + r[1]]); });
  writeSheet_('轉盤名單', wheelRows);

  // 備用亂數抽獎（轉盤無法使用時才用；過程截圖存證）
  const shuffled = data.slice();
  for (var i = shuffled.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var t = shuffled[i]; shuffled[i] = shuffled[j]; shuffled[j] = t;
  }
  const out = [['身分', '編號', '暱稱', '填答時間', '邀請團員']];
  for (var k = 0; k < CONFIG.WINNERS + CONFIG.BACKUPS; k++) {
    out.push([k < CONFIG.WINNERS ? '正取' + (k + 1) : '備取' + (k - CONFIG.WINNERS + 1),
      shuffled[k][0], shuffled[k][1], shuffled[k][2], shuffled[k][3]]);
  }
  out.push(['（備用抽獎時間）', new Date(), '', '', '']);
  writeSheet_('備用抽獎結果', out);
  SpreadsheetApp.getUi().alert('✅ 已產生：\n・「轉盤名單」→ 整欄複製貼到 wheelofnames.com 公開抽（主要方式，操作照 04 第二節：2 位幹部見證、全程錄影、每輪先截圖再按 Remove）\n・「備用抽獎結果」→ 轉盤無法用時的備案，每按一次重抽一次');
}

// ════════════ ⑥ 結案 ════════════
function step6_cleanup() {
  const ui = SpreadsheetApp.getUi();
  if (PropertiesService.getScriptProperties().getProperty('CLEANED_AT')) {
    ui.alert('已執行過結案清理。為避免把「演出通知名單」覆寫成空白，不再重複執行。');
    return;
  }
  const ok = ui.alert('結案前確認',
    '執行後將：\n1. 把訂閱 Email 轉存到「演出通知名單」\n2. 清除回覆表中的暱稱、聯絡方式、聽後感、Email 欄（票選資料保留供統計）\n3. 刪除「進度」「抽獎池」「轉盤名單」「需人工判定」「聽後感_可刊登」分頁（聽後感素材將一併刪除，請確認結案貼文已完成）\n4. 自動刪除表單端（forms.google.com）的全部回覆\n\n⚠️ 中獎者的領獎與稅務資料請先另外抄存！確定執行？',
    ui.ButtonSet.YES_NO);
  if (ok !== ui.Button.YES) return;

  // 1. Email 轉存（去重）
  const rows = readResponses_();
  const emails = {};
  rows.forEach(function (x) { if (x.email && x.email.indexOf('@') !== -1) emails[x.email.toLowerCase()] = true; });
  writeSheet_('演出通知名單', [['Email（已同意接收演出資訊，保留至取消為止）']]
    .concat(Object.keys(emails).map(function (e) { return [e]; })));

  // 2. 清除回覆表個資欄
  const sheet = responseSheet_();
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0].map(String);
  [Q.NICK, Q.CONTACT, Q.FEEDBACK, Q.NEXT_EMAIL].forEach(function (title) {
    for (var i = 0; i < headers.length; i++) {
      if (headers[i].indexOf(title) === 0 && sheet.getLastRow() > 1) {
        sheet.getRange(2, i + 1, sheet.getLastRow() - 1, 1).clearContent();
      }
    }
  });

  // 3. 刪除工作分頁
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  ['進度', '抽獎池', '轉盤名單', '需人工判定', '聽後感_可刊登'].forEach(function (n) {
    var sh = ss.getSheetByName(n);
    if (sh) ss.deleteSheet(sh);
  });

  // 4. 刪除表單端（forms.google.com）回覆
  const fid = PropertiesService.getScriptProperties().getProperty('FORM_ID');
  if (fid) FormApp.openById(fid).deleteAllResponses();

  PropertiesService.getScriptProperties().setProperty('CLEANED_AT', new Date().toISOString());
  ui.alert('✅ 結案完成（表單端回覆已自動刪除）。記得：\n・結案貼文宣告個資已刪除\n・中獎者稅務資料（如有）保存至申報完成後 5 年\n・做乾淨副本後刪除本檔（試算表「版本紀錄」仍留有個資，見 08 限制 7）');
}
