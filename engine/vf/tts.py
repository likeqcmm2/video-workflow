"""Voice-over: one Gemini TTS call per scene + ASR back-transcription check. Resumable.

Rules learned the hard way (docs/06-voice.md):
  * Send ONLY the narration text. Style instructions inside the text are sometimes READ ALOUD.
  * Verify every scene by transcribing it back; retry up to voice.attempts; keep the best take.
  * If the main ASR model refuses (BlockedReason / empty), fall back to the next model in
    voice.asr_models. A refusal is not a bad take.
  * Mispronounced words: add a reading in project.yaml voice.readings (katakana/hiragana for ja)
    or a per-scene override in tts_overrides.yaml, then re-run only those scenes.
Outputs: out/vo/<scene>.wav + out/vo/<scene>.json {text, asr, sim, dur, asr_model, attempt}
"""
import base64
import difflib
import json
import os
import subprocess
import sys
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from . import config
from .scriptfmt import parse
from .textproc import normalize_for_compare, to_tts

VO = Path("out/vo")

ASR_PROMPT = {
    "ja": "この音声を一字一句そのまま日本語で書き起こしてください。数字は漢数字で書いてください。書き起こしのみを出力してください。",
    "zh": "请逐字转写这段音频。只输出转写文本。",
    "ko": "이 음성을 한 글자도 빠짐없이 그대로 받아 적어 주세요. 받아 적은 텍스트만 출력하세요.",
}
ASR_DEFAULT = "Transcribe this audio verbatim in its original language. Write numbers as words. Output only the transcript."


def _client():
    from google import genai
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is not set. Add it to the environment's secrets/variables "
                         "(never paste it into chat or commit it).")
    return genai.Client(api_key=key)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(p)]))


def tts(client, text, out_path, retries=4):
    v = config.load()["voice"]
    for a in range(retries):
        try:
            it = client.interactions.create(
                model=v["tts_model"],
                input=[{"type": "user_input", "content": [{"type": "text", "text": text}]}],
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": v["voice"]}]},
            )
            Path(out_path).write_bytes(base64.b64decode(it.output_audio.data))
            return out_path
        except Exception as e:  # network / quota / transient
            print(f"  tts retry {a}: {str(e)[:160]}", flush=True)
            time.sleep(5 * (a + 1))
    raise RuntimeError("TTS failed after retries")


def asr(client, path):
    from google.genai import types
    cfg = config.load()
    prompt = ASR_PROMPT.get(cfg["language"], ASR_DEFAULT)
    audio = Path(path).read_bytes()
    for model in cfg["voice"]["asr_models"]:
        for a in range(3):
            try:
                r = client.models.generate_content(model=model, contents=[
                    types.Part.from_bytes(data=audio, mime_type="audio/wav"), prompt])
                if r.text and r.text.strip():
                    return r.text.strip(), model
                break          # empty / blocked -> next model, not a retry of the same one
            except Exception as e:
                print(f"  asr {model} retry {a}: {str(e)[:120]}", flush=True)
                time.sleep(4 * (a + 1))
    return "", None


def sim(a, b):
    return difflib.SequenceMatcher(None, normalize_for_compare(a), normalize_for_compare(b)).ratio()


def _overrides():
    p = Path("tts_overrides.yaml")
    return (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}


def fake_wav(path, seconds, sr=24000):
    """Silent placeholder (engine tests only - preflight refuses to render with fakes)."""
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"\x00\x00" * int(seconds * sr))


def run(ids=None, redo=False, fake=False):
    cfg = config.load()
    v = cfg["voice"]
    VO.mkdir(parents=True, exist_ok=True)
    scenes, _ = parse()
    ovr = _overrides()
    todo = [s for s in scenes if not ids or s["id"] in ids]
    client = None if fake else _client()

    def job(s):
        sid = s["id"]
        text = ovr.get(sid) or to_tts(s["nar"])
        wav, js = VO / f"{sid}.wav", VO / f"{sid}.json"
        if js.exists() and not redo and not (ids and sid in ids):
            rec = json.loads(js.read_text())
            if rec.get("text") == text and wav.exists():
                return rec
        if fake:
            secs = max(1.5, len(text) / (7.0 if config.is_cjk() else 15.0))
            fake_wav(wav, secs)
            rec = {"id": sid, "text": text, "asr": "", "sim": 0.0, "dur": round(secs, 3), "fake": True}
            js.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
            return rec
        best = None
        for attempt in range(v["attempts"]):
            tmp = VO / f"{sid}.try.wav"
            tts(client, text, tmp)
            heard, model = asr(client, tmp)
            sc = sim(text, heard) if heard else 0.0
            rec = {"id": sid, "text": text, "asr": heard, "asr_model": model, "sim": round(sc, 3),
                   "attempt": attempt}
            if best is None or sc > best["sim"]:
                best = rec
                os.replace(tmp, wav)
            if sc >= v["min_similarity"]:
                break
        if Path(VO / f"{sid}.try.wav").exists():
            os.remove(VO / f"{sid}.try.wav")
        best["dur"] = round(dur(wav), 3)
        js.write_text(json.dumps(best, ensure_ascii=False, indent=1))
        print(f"{sid} sim={best['sim']} dur={best['dur']}", flush=True)
        return best

    with ThreadPoolExecutor(v["workers"]) as ex:
        res = list(ex.map(job, todo))
    low = [(r["id"], r["sim"]) for r in res if not r.get("fake") and r["sim"] < v["min_similarity"]]
    total = sum(r["dur"] for r in res)
    print(f"DONE {len(res)} scenes, total voice {total:.1f}s ({int(total // 60)}:{total % 60:04.1f}); "
          f"below {v['min_similarity']}: {low}")
    print("Check each low scene: listen-free review = compare text vs asr in out/vo/<id>.json; "
          "fix with voice.readings or tts_overrides.yaml, then: vf tts <ids>")
    return res


def report():
    rows = [json.loads(p.read_text()) for p in sorted(VO.glob("*.json"))]
    if not rows:
        print("no voice yet")
        return
    sims = [r["sim"] for r in rows if not r.get("fake")]
    total = sum(r["dur"] for r in rows)
    print(f"{len(rows)} scenes, voice {total:.1f}s, mean sim {sum(sims) / max(1, len(sims)):.3f}, "
          f"min {min(sims) if sims else 0}")
    for r in sorted(rows, key=lambda r: r["sim"])[:8]:
        print(f"  {r['id']} sim={r['sim']} model={r.get('asr_model')}")


if __name__ == "__main__":
    run(sys.argv[1:] or None)
