#!/usr/bin/env bash
# MAKE_EPISODE.sh — turn a sermon video into a tagged podcast MP3 with artwork.
#
# Usage:
#   ./MAKE_EPISODE.sh "/path/to/sermon.mp4" "Sunday Message — November 9, 2025" "ep03_2025-11-09_sunday-message"
#
# Args: 1=source video  2=episode title  3=output basename (no extension)
# Output lands in ./episodes/<basename>.mp3
set -euo pipefail

SRC="${1:?source video required}"
TITLE="${2:?episode title required}"
BASE="${3:?output basename required}"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ART="$DIR/art/jrm_podcast_cover_3000.png"
OUT="$DIR/episodes/$BASE.mp3"

ffmpeg -y -i "$SRC" -i "$ART" \
  -map 0:a:0 -map 1:v:0 -c:a libmp3lame -b:a 128k -ar 44100 -ac 2 \
  -c:v:1 mjpeg -disposition:v:0 attached_pic \
  -metadata title="$TITLE" \
  -metadata artist="Pastor Jesse Rich" \
  -metadata album="Jesse Rich Ministries" \
  -metadata genre="Religion & Spirituality" \
  -id3v2_version 3 \
  "$OUT"

echo "✅ Wrote $OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" | awk '{printf "   Length: %d min\n", $1/60}'
