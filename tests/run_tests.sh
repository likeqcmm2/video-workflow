#!/usr/bin/env bash
# Engine self-test (no API keys needed: uses placeholder voice).  bash tests/run_tests.sh
# 1) smoke: synthetic assets -> every stage -> video.mp4 must pass `vf qa`
# 2) negative: six planted defects -> `vf preflight` must fail and name every one
set -euo pipefail
cd "$(dirname "$0")"
VF="$(pwd)/../scripts/vf"
export VF_ALLOW_FAKE=1
echo "== smoke"
cd smoke
python3 make_fixtures.py
rm -rf out
$VF count --stamp >/dev/null
$VF tts --fake >/dev/null
$VF media scan assets/video/clip.mp4
$VF preflight
$VF render all
$VF audio >/dev/null
$VF final
$VF qa
$VF sheets all --every 3 >/dev/null
$VF stats >/dev/null
$VF sources
echo "== change detection"
test -z "$(PYTHONPATH=../../engine python3 -c 'from vf import render, config; config.load(); print(" ".join(render.changed()))')" \
  || { echo "FAIL: chapters stale right after rendering"; exit 1; }
cd ..
echo "== negative"
cd negative
python3 make.py
if $VF preflight > preflight.out 2>&1; then echo "FAIL: preflight passed on a broken project"; exit 1; fi
for needle in "narration changed after TTS" "Commons file not downloaded" "sits on a cut/black" "no on-screen credit" \
              "footage too short" "outside safe area" "subtitle zone"; do
  grep -q "$needle" preflight.out || { echo "FAIL: preflight missed: $needle"; exit 1; }
done
echo "ALL TESTS PASSED"
