#!/usr/bin/env bash
# Download test sequences from the Xiph.org derf collection into data/videos/.
# Check each clip's copyright note on https://media.xiph.org/video/derf/ before using it in the public demo.
set -u
BASE="https://media.xiph.org/video/derf/y4m"
OUT="$(dirname "$0")/../data/videos"
mkdir -p "$OUT"

CLIPS=(
  FourPeople_1280x720_60.y4m      # 720p video-conferencing (preferred, if hosted)
  Johnny_1280x720_60.y4m
  KristenAndSara_1280x720_60.y4m
  akiyo_cif.y4m                   # CIF talking-head fallbacks
  news_cif.y4m
  mother_daughter_cif.y4m
)

for c in "${CLIPS[@]}"; do
  if [ -f "$OUT/$c" ]; then echo "have   $c"; continue; fi
  if curl -fsSL -o "$OUT/$c" "$BASE/$c"; then echo "got    $c"; else rm -f "$OUT/$c"; echo "MISSING $c"; fi
done
