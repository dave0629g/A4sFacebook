#!/usr/bin/env python3
"""產生 素材/佔位/ 底下所有佔位圖片、影片、音檔。

用法（在 repo 根目錄執行）：
    python3 素材/make_placeholders.py

需求：
- Pillow（pip3 install pillow）
- 中文字型：~/Library/Fonts/NotoSansCJKtc-*.otf（macOS 沒有的話改 FONT_* 路徑）
- ffmpeg（沒有就跳過影片/音檔，只產圖片）

佔位檔只是「這個位置會有東西」的視覺提示，圖片/影片都印有「佔位 PLACEHOLDER」浮水印，
絕不可能誤發。真正要交件時，把實品丟進 素材/收件匣/ 或本機原圖資料夾，再跑 update.py。
"""
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '佔位')
FONT_BOLD = os.path.expanduser('~/Library/Fonts/NotoSansCJKtc-Bold.otf')
FONT_REG = os.path.expanduser('~/Library/Fonts/NotoSansCJKtc-Regular.otf')

COLORS = {
    '截圖': '#5B7DB1', '照片': '#6B9E78', '圖卡': '#B08A5B',
    '證明': '#9A6A8A', '範本': '#888888',
}


def dashed_rect(draw, box, color, width=4, dash=18, gap=12):
    x0, y0, x1, y1 = box
    def seg(p0, p1, horizontal):
        length = (p1[0] - p0[0]) if horizontal else (p1[1] - p0[1])
        pos = 0
        while pos < length:
            end = min(pos + dash, length)
            if horizontal:
                draw.line([(p0[0] + pos, p0[1]), (p0[0] + end, p0[1])], fill=color, width=width)
            else:
                draw.line([(p0[0], p0[1] + pos), (p0[0], p0[1] + end)], fill=color, width=width)
            pos = end + gap
    seg((x0, y0), (x1, y0), True)
    seg((x0, y1), (x1, y1), True)
    seg((x0, y0), (x0, y1), False)
    seg((x1, y0), (x1, y1), False)


def make_png(path, size, kind, title, lines):
    w, h = size
    img = Image.new('RGBA', size, '#ECEEF0')
    draw = ImageDraw.Draw(img)
    bar_h = max(14, h // 50)
    draw.rectangle([0, 0, w, bar_h], fill=COLORS.get(kind, '#888888'))

    wm_size = max(60, w // 9)
    wm_font = ImageFont.truetype(FONT_BOLD, wm_size)
    wm = Image.new('RGBA', (w * 2, wm_size * 2), (0, 0, 0, 0))
    ImageDraw.Draw(wm).text((0, 0), '佔位 PLACEHOLDER 佔位', font=wm_font, fill=(120, 125, 130, 40))
    wm = wm.rotate(24, expand=True)
    img.alpha_composite(wm, (-w // 4, h // 6))

    m = max(20, w // 50)
    dashed_rect(draw, (m, m + bar_h, w - m, h - m), '#B0533E', width=max(3, w // 350))

    tag_font = ImageFont.truetype(FONT_BOLD, max(22, w // 38))
    tag = f'【佔位{kind}】實品未到'
    tb = draw.textbbox((0, 0), tag, font=tag_font)
    pad = 14
    draw.rectangle([m + 24, m + bar_h + 24, m + 24 + (tb[2] - tb[0]) + pad * 2,
                    m + bar_h + 24 + (tb[3] - tb[1]) + pad * 2], fill='#B0533E')
    draw.text((m + 24 + pad, m + bar_h + 24 + pad - tb[1]), tag, font=tag_font, fill='#FFFFFF')

    title_font = ImageFont.truetype(FONT_BOLD, max(34, w // 18))
    tb = draw.textbbox((0, 0), title, font=title_font)
    ty = h * 0.32
    draw.text(((w - (tb[2] - tb[0])) / 2, ty), title, font=title_font, fill='#33373B')

    body_font = ImageFont.truetype(FONT_REG, max(24, w // 36))
    line_h = body_font.size * 1.65
    y = ty + (tb[3] - tb[1]) + line_h * 1.2
    for line in lines:
        draw.text((w * 0.1, y), line, font=body_font, fill='#4A4F54')
        y += line_h

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.convert('RGB').save(path)
    print('PNG ', os.path.relpath(path))


def make_video(path, title, lines):
    if not shutil.which('ffmpeg'):
        print('skip（無 ffmpeg）', os.path.relpath(path)); return
    text = title + '\n\n' + '\n'.join(lines)
    with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(text); txt = f.name
    vf = (f"drawtext=fontfile={FONT_BOLD}:textfile={txt}:fontcolor=0xEDEEF0:fontsize=44:"
          "line_spacing=18:x=(w-text_w)/2:y=(h-text_h)/2,"
          f"drawtext=fontfile={FONT_BOLD}:text='佔位 PLACEHOLDER':fontcolor=0xB0533E:fontsize=30:x=24:y=24")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error',
                    '-f', 'lavfi', '-i', 'color=c=0x3A4450:s=1280x720:d=4:r=24',
                    '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-vf', vf, '-shortest',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', path], check=True)
    os.unlink(txt); print('MP4 ', os.path.relpath(path))


def make_audio(path):
    if not shutil.which('ffmpeg'):
        print('skip（無 ffmpeg）', os.path.relpath(path)); return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error',
                    '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3', '-af', 'volume=0.15',
                    '-metadata', 'title=佔位音檔 PLACEHOLDER（本活動目前無音檔需求）',
                    '-c:a', 'aac', path], check=True)
    print('M4A ', os.path.relpath(path))


P = lambda *parts: os.path.join(ROOT, *parts)

# ── 01 KPI 基準（6/12 晚）─────────────────────────────────────
make_png(P('01_KPI基準_0612晚', '佔位_Meta洞察30天淨增截圖.png'), (1280, 800), '截圖',
         'Meta 洞察「追蹤者」30 天淨增截圖',
         ['期限：6/12（五）今晚——當晚不存，之後補不回來',
          '路徑：Meta Business Suite → 洞察報告 → 追蹤者',
          '用途：KPI 公式的自然成長基準（平均日增 × 19 天）',
          '實品：丟 素材/收件匣/ 或存共用資料夾，跑 update.py'])

# ── 03 第一波照片（6/14 審片 → 6/15 上架）────────────────────
for i in (1, 2, 3):
    make_png(P('03_第一波照片_0614審片', f'佔位_演出照_{i:02d}.png'), (1200, 800), '照片',
             f'第一波演出照（佔位 {i}/3）',
             ['期限：6/14 送團員群組審片（24 小時）→ 6/15 上相簿',
              '內容：演出＋謝幕精選，實際 25–30 張',
              '審片戒律：不用單一觀眾特寫；兒童入鏡先抽掉',
              '原圖：存 ~/A4s音樂會素材原圖/第一波_演出謝幕/（不進 git）'])

# ── 04 第二波照片（6/20 審片 → 6/21 上線）────────────────────
for i in (1, 2, 3):
    make_png(P('04_第二波照片_0621', f'佔位_花絮照_{i:02d}.png'), (1200, 800), '照片',
             f'第二波花絮照（佔位 {i}/3）',
             ['期限：6/20 送審（留 24 小時）→ 6/21 上線',
              '內容：彩排、幕後、觀眾席與大合照 10–20 張',
              '用途：FB 貼文 2.5＋LINE 訊息 13 的「找自己」誘因',
              '原圖：存 ~/A4s音樂會素材原圖/第二波_彩排幕後觀眾席/（不進 git）'])

# ── 06 抽獎存證（6/26）───────────────────────────────────────
for i in (1, 2, 3, 4, 5):
    make_png(P('06_抽獎存證_0626', f'佔位_轉盤截圖_正取{i}.png'), (1280, 720), '截圖',
             f'wheelofnames 截圖：正取 {i}/5',
             ['期限：6/26（五）抽獎當下，≥2 位幹部見證',
              '規則：中獎彈窗出現「先截圖、再按 Remove」',
              '公開：6/27（六）20:00 隨開獎貼文發布（顯示暱稱，',
              '　　　個資告知已揭露此用途）'])
for i in (1, 2):
    make_png(P('06_抽獎存證_0626', f'佔位_轉盤截圖_備取{i}.png'), (1280, 720), '截圖',
             f'wheelofnames 截圖：備取 {i}/2',
             ['期限：6/26（五）抽獎當下（第 6、7 輪）',
              '規則：同正取——先截圖、再按 Remove',
              '用途：6/30 後逾期未領獎時依序遞補的依據'])
make_video(P('06_抽獎存證_0626', '佔位_抽獎全程錄影.mp4'),
           '佔位影片：抽獎全程錄影',
           ['6/26（五）手機錄下整個抽獎過程，不可中斷',
            '僅留存自證——不公開發布（本活動不發布任何影片）',
            '實品：僅存共用資料夾，不進 git'])

# ── 07 開獎素材（6/27 20:00）─────────────────────────────────
make_png(P('07_開獎素材_0627', '佔位_前三名揭曉圖卡.png'), (1080, 1080), '圖卡',
         '前三名揭曉圖卡',
         ['期限：6/27（六）20:00 開獎貼文用',
          '做法：Canva 照片＋文字，約 10 分鐘',
          '內容：第 1～3 名曲名（完整排名永不公開）',
          '實品：丟 素材/收件匣/，跑 update.py'])

# ── 08 領獎與結案（6/27–7/1）─────────────────────────────────
make_png(P('08_領獎與結案_0627-0701', '佔位_領獎合影_01.png'), (1200, 800), '照片',
         '領獎合影（自願、非必收）',
         ['期限：6/27–6/30 領獎時',
          '出示「追蹤中」畫面合影＝純自願，不影響領獎',
          '刊登前必須先有本人私訊同意（見同意截圖）',
          '實品：僅存共用資料夾，不進 git'])
make_png(P('08_領獎與結案_0627-0701', '佔位_刊登同意截圖_01.png'), (750, 1334), '截圖',
         '刊登同意私訊截圖',
         ['每刊登 1 位＝1 張同意截圖',
          '問法：「請問可以把這張領獎合照',
          '放在我們的結案貼文嗎？」',
          '私訊截圖含未遮蔽姓名，',
          '【僅存共用資料夾，絕不進 git】'])

# ── 09 獎品與合規存證 ────────────────────────────────────────
make_png(P('09_獎品與合規存證', '佔位_入場券票面價證明.png'), (1200, 800), '證明',
         '入場券票面價證明',
         ['期限：6/13 前（前置檢查第 2 項）',
          '形式：票面照片或售票頁截圖',
          '用途：確認 ≤NT$1,000（稅務級距認定以票面價為準）',
          '超過 NT$1,000：先讀 04 的稅務段落再開跑'])
make_png(P('09_獎品與合規存證', '佔位_USB市價證明.png'), (1200, 800), '證明',
         '30週年紀念 USB 市價／發票證明',
         ['期限：6/13 前（前置檢查第 2 項）',
          '形式：購入發票照片或市價網頁截圖',
          '用途：確認 ≤NT$1,000（稅務級距認定）',
          '同時確認：兩種獎品各備足 5 份'])

# ── 範本（要新增佔位檔時複製改名用）──────────────────────────
make_png(P('範本', '佔位_橫式圖範本_1200x630.png'), (1200, 630), '範本',
         '橫式圖佔位範本（FB 連結圖比例）',
         ['複製本檔改名使用，或改 make_placeholders.py 重產',
          '尺寸：1200×630（FB 動態貼文橫圖建議比例）'])
make_png(P('範本', '佔位_方形圖卡範本_1080x1080.png'), (1080, 1080), '範本',
         '方形圖卡佔位範本',
         ['複製本檔改名使用', '尺寸：1080×1080（IG／FB 方形圖卡）'])
make_video(P('範本', '佔位_影片範本.mp4'),
           '佔位影片範本', ['複製改名使用；1280×720、4 秒、含靜音音軌'])
make_audio(P('範本', '佔位_音檔範本.m4a'))

print('完成。佔位檔在 素材/佔位/')
