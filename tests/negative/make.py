"""Build a negative test project with planted defects that preflight must identify."""
import shutil
from pathlib import Path

HERE = Path(__file__).parent
SMOKE = HERE.parent / "smoke"
for f in ("project.yaml", "graphics.yaml", "script.md"):
    shutil.copy(SMOKE / f, HERE / f)
for d in ("assets", "out"):
    if (HERE / d).exists():
        shutil.rmtree(HERE / d)
    shutil.copytree(SMOKE / d, HERE / d)
(HERE / "custom_gfx.py").write_text((SMOKE / "custom_gfx.py").read_text() + '''

def g_overflow(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    text(d, (1500, 300), "この説明は長すぎて画面の右端からはみ出してしまう", F("text", 40), C.TEXT, "la")
    text(d, (200, 950), "字幕の位置に重なる文字", F("text", 40), C.TEXT, "la")
    return im
''')
y = (HERE / "project.yaml").read_text()
for a, b in [("  motion: {still_zoom: 0.08, video_push: 0.03}\n", ""),                                  # design decision missing
             ('stamp: {font: "Noto Sans JP Medium",', 'stamp: {font: "Noto Sans XX",'),    # font not installed
             ("real_pct: {min: 20, max: 70}", "real_pct: {min: 85, max: 95}")]:            # film outside its range
    assert a in y, a
    y = y.replace(a, b)
(HERE / "project.yaml").write_text(y)
s = (HERE / "script.md").read_text()
for a, b in [
    ("VIS: gfx:map", "VIS: gfx:overflow"),                                                       # text overflow
    ("VIS: CLIP @10.0", "VIS: CLIP @12.0"),                                                       # runs into fade
    ("VIS: img:assets/img/portrait.jpg | credit=写真：テスト | lt=", "VIS: img:assets/img/portrait.jpg | lt="),  # no credit
    ("VIS: gfx:bars | spec=flights", "VIS: cm:Does not exist.jpg"),                              # missing asset
    ("NAR: シャトルは三つの州を結ぶ会議で判断されました。", "NAR: シャトルは三つの州を結ぶ会議で判断されたのです。"),  # text changed after TTS
    ("VIS: CLIP @1.0 | stamp", "VIS: CLIP @7.9 | stamp"),                                        # in-point on a cut
]:
    assert a in s, a
    s = s.replace(a, b)
(HERE / "script.md").write_text(s)
print("negative project ready")
