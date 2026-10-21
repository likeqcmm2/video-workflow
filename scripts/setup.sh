#!/usr/bin/env bash
# One-time environment setup. Idempotent; safe to re-run.
#   bash scripts/setup.sh [language ...]      e.g.  bash scripts/setup.sh ja
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

need() { command -v "$1" >/dev/null 2>&1; }
if ! need ffmpeg || ! need ffprobe; then
  echo "[setup] installing ffmpeg"; (apt-get update -qq && apt-get install -y -qq ffmpeg) >/dev/null
fi
FILTERS="$(ffmpeg -hide_banner -filters 2>/dev/null || true)"
case "$FILTERS" in *" ass "*) ;; *) echo "[setup] WARNING: ffmpeg has no libass 'ass' filter - subtitles cannot be burned";; esac

echo "[setup] python packages"
python3 -m pip install -q -r requirements.txt 2>&1 | grep -v -i "warning: running pip" || true
python3 -m pip install -q --no-deps num2words 2>&1 | grep -v -i "warning: running pip" || true   # its CLI dep docopt fails to build on new Pythons
need yt-dlp || python3 -m pip install -q yt-dlp 2>&1 | grep -v -i "warning: running pip" || true

echo "[setup] fonts"
python3 scripts/fetch_fonts.py "${@:-ja}"

echo "[setup] Natural Earth (public domain) map data"
mkdir -p vendor/geo
for f in ne_50m_admin_0_countries ne_50m_admin_1_states_provinces_lakes; do
  if [ ! -f "vendor/geo/$f.shp" ]; then
    curl -sSfL -o "vendor/geo/$f.zip" "https://naciscdn.org/naturalearth/50m/cultural/$f.zip"
    (cd vendor/geo && python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall('.')" "$f.zip" && rm -f "$f.zip")
  fi
done

chmod +x scripts/vf
echo "[setup] env check"
scripts/vf doctor || true
