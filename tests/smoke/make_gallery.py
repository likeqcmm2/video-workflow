"""Render every library template with sample data -> docs/gfx-gallery.jpg (run inside tests/smoke)."""
from PIL import Image, ImageDraw

from vf import config
from vf import gfx
from vf.media import _font

config.load()
S = [
    ("title", {"text": "チャレンジャー号爆発事故", "kicker": "1 9 8 6 . 1 . 2 8", "sub": "打ち上げ73秒後の空中分解"}),
    ("quote", {"text": "「あれは爆発する」", "attr": "ボブ・イーベリング（技術者）"}),
    ("textcard", {"text": "マロイの説明", "sub": "発言は「文脈を無視して切り取られた」"}),
    ("term", {"term": "「逸脱の常態化」", "en": "Normalization of Deviance", "note": "ダイアン・ヴォーン（1996年）"}),
    ("bars", {"spec": "flights", "step": "3"}),
    ("timeline", {"spec": "events"}),
    ("scatter", {"spec": "pts"}),
    ("line", {"title": "乗員室の軌跡", "x_range": "0,180", "y_range": "0,20", "y_ticks": "0,10,20", "y_fmt": "{:g}km",
              "x_ticks": "0,60,120,180", "x_fmt": "{:g}s",
              "points": ";".join(f"{x}|{(14 + 6 * (1 - ((90 - x) / 17) ** 2)) if x < 90 else max(0.0, 20 - ((x - 90) / 75) ** 2 * 20):.2f}"
                                 for x in range(73, 166, 2)), "marks": "73|14|73秒 分解|accent;165|0|約2分45秒後 海面へ|text",
              "draw": "0.1"}),
    ("compare", {"title": "事故の確率", "left_label": "技術者", "left_value": "約1/100", "right_label": "管理職",
                 "right_value": "1/100,000", "right_note": "毎日打ち上げて300年に1度", "grid": "1"}),
    ("gauge", {"min": "-20", "max": "30", "tick": "10", "unit": "℃", "value": "2.2", "label": "打ち上げ時の気温 約2℃",
               "sub": "それまでで最も寒い", "color": "accent", "ref": "11.7|これまでの最低"}),
    ("calendar", {"title": "1986年1月 打ち上げ日程", "cells": "22;23;24;25;26;27;28", "top": "1月",
                  "marks": "1|延期|x;2|延期|x;4|延期|x;6|中止|xa|ハッチ;7|打ち上げ|box"}),
    ("clocks", {"clocks": "フロリダ|1月28日 午前11時38分|11:38;日本|1月29日 午前1時38分|1:38"}),
    ("map", {"region": "us48", "highlight": "Utah;Alabama;Florida", "caption": "3か所を結んだ電話会議",
             "points": "ut|-112.2|41.6|ユタ州|サイオコール社|30|-20;al|-86.6|34.6|アラバマ州|マーシャル|40|-95;fl|-80.6|28.5|フロリダ州|ケネディ|40|30",
             "links": "ut-al;al-fl;ut-fl"}),
    ("map", {"region": "JPN,KOR,CHN,PRK,TWN", "bbox": "120,24,146,46", "highlight": "Japan",
             "points": "tk|139.7|35.7|東京||30|-20", "caption": "region=ISO3 list"}),
    ("document", {"lines": "MORTON THIOKOL, INC.\\N\\N31 July 1985\\N\\NSUBJECT: O-Ring Erosion\\N\\N  The result would be a catastrophe",
                  "caption": "ボイジョリーのメモ", "sub": "1985年7月31日 ／ 文面の一部を再現", "highlight": "7-7"}),
    ("list", {"title": "委員会の勧告", "items": "設計の見直し;管理体制の見直し;危険の分析;安全監督部門の設置", "highlight": "4",
              "numbering": "roman"}),
    ("hierarchy", {"title": "打ち上げ審査の階層", "levels": "Ⅰ|NASA本部;Ⅱ|計画管理;Ⅲ|マーシャル;Ⅳ|サイオコール社",
                   "break_after": "2", "break_label": "ここから上には伝わらず"}),
    ("boxes", {"title": "最終判断の4人", "items": "メイソン|上級副社長;ウィギンズ|副社長;キルミンスター|副社長;ランド|技術担当",
               "note": "技術者は投票から外された", "verdict": "結論：打ち上げに賛成"}),
    ("names", {"caption": "1985年 日本人宇宙飛行士候補", "names": "毛利 衛;向井 千秋;土井 隆雄", "sub": "搭乗予定：1988年", "step": "2"}),
    ("counter", {"value": "7735000", "prefix": "$", "label": "和解金の総額", "sub": "4家族"}),
    ("ranking", {"rank": "3", "title": "コロンビア号", "sub": "2003年2月1日"}),
    ("chapter", {"num": "第4章", "title": "73秒"}),
]
tw, th = 480, 270
cols = 4
rows = (len(S) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + 24)), "white")
d = ImageDraw.Draw(sheet)
f = _font(18)
for i, (name, p) in enumerate(S):
    im = gfx.render(name, p, 3.5 if name != "chapter" else 1.8, 6.0).resize((tw, th), Image.LANCZOS)
    x, y = (i % cols) * tw, (i // cols) * (th + 24)
    sheet.paste(im, (x, y))
    d.text((x + 4, y + th + 2), f"gfx:{name}", fill="black", font=f)
sheet.save("../../docs/gfx-gallery.jpg", quality=80)
print("docs/gfx-gallery.jpg", sheet.size)
