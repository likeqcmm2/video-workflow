"""Build the negative test project: the smoke project with six classic defects planted.
Each defect cost the reference production real time; preflight must catch every one."""
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
(HERE / "custom_gfx.py").write_text('''from PIL import ImageDraw
from vf.gfx.core import C, F, canvas, text


def g_overflow(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    text(d, (1500, 300), "この説明は長すぎて画面の右端からはみ出してしまう", F("sans", 40), C.TEXT, "la")
    text(d, (200, 950), "字幕の位置に重なる文字", F("sans", 40), C.TEXT, "la")
    return im
''')
s = (HERE / "script.md").read_text()
for a, b in [
    ("VIS: gfx:ring | title=接合部の模式図", "VIS: gfx:overflow"),                                   # text overflow
    ("VIS: CLIP @10.0", "VIS: CLIP @12.0"),                                                           # runs into fade
    ("VIS: img:assets/img/portrait.jpg | credit=写真：テスト | lt=", "VIS: img:assets/img/portrait.jpg | lt="),  # no credit
    ("VIS: gfx:bars | spec=flights | step=2", "VIS: cm:Does not exist.jpg"),                         # missing asset
    ("NAR: 損傷は何度も見つかっていました。", "NAR: 損傷は何度も見つかっていたのです。"),               # text changed after TTS
    ("VIS: CLIP @1.0 | stamp", "VIS: CLIP @7.9 | stamp"),                                            # in-point on a cut
]:
    assert a in s, a
    s = s.replace(a, b)
(HERE / "script.md").write_text(s)
print("negative project ready")
