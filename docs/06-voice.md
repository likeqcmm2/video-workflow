# Phase 6 — Voice-over (Gemini TTS) with back-transcription check

Start only after `vf count` shows GATE: PASS and the stamp line exists.

```bash
$VF tts                      # all scenes, 4 parallel workers, resumable; background job
$VF tts-report               # mean / min similarity, worst scenes
$VF tts S214 S305            # regenerate selected scenes
$VF tts-accept S314          # a take you verified is right although ASR spelled it differently
```
Per scene: one TTS call (`voice.tts_model`, `voice.voice`) → wav → ASR transcription (`voice.asr_models`,
first that answers) → similarity of normalised texts. Up to `voice.attempts` takes; the best is kept.
Results: `out/vo/<id>.wav` + `.json` (text, asr, sim, dur, asr_model).

## Rules (each learned in production)
- **Send only the narration.** A style instruction placed in the text ("read calmly…") was sometimes read
  aloud; all 229 scenes had to be regenerated. The voice's default documentary delivery was right.
- Numbers, dates and units are spelled out automatically from the digits in NAR (`engine/vf/textproc.py`:
  Japanese kanji numerals; other languages via num2words). Subtitles keep the digits.
- Mispronunciations: add a reading in `project.yaml voice.readings` (katakana for foreign names, hiragana for
  misread kanji, e.g. `{"NASA": "ナサ", "Oリング": "オーリング"}`) or a full override for one scene in
  `tts_overrides.yaml` (`S214: "<exact TTS text>"`). Re-run only those scenes.
- ASR refusal (`BlockedReason.OTHER`) or empty answer → the next ASR model is used automatically; a refusal is
  not a bad take.
- Similarity < 0.93: read `text` vs `asr` in the json. Kanji/kana spelling differences only → `tts-accept`.
  Missing or wrong words → fix and regenerate. < 0.80 is always an error in preflight.
- Changing NAR after TTS makes the voice stale; preflight reports it.
- Record the total voice duration (tts output / `vf stats`) in PROGRESS.md and the report.

## API shape (for reference — the engine already does this)
```python
from google import genai
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
it = client.interactions.create(model="gemini-3.8-flash-tts",
    input=[{"type": "user_input", "content": [{"type": "text", "text": text}]}],
    response_format={"type": "audio"}, generation_config={"speech_config": [{"voice": "Arlo"}]})
wav_bytes = base64.b64decode(it.output_audio.data)            # 24 kHz mono WAV
r = client.models.generate_content(model="gemini-3.8-flash",
    contents=[types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"), "<verbatim transcription prompt>"])
```
