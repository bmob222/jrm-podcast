#!/bin/bash
# migrate_audio_to_release.sh — move the 38 legacy podcast MP3s off GitHub Pages (hard 1 GB site cap, ~950 MB
# used) onto the existing GitHub Release 'audio' WITHOUT changing any GUID (guid = 'jrm-<file>' never depends on
# the host, so podcast apps simply re-point the enclosure; no duplicate episodes).
#
# Prepared Nov 6 2026 (T5). NOT RUN during the build — uploading release assets and pushing the feed publishes.
#
#   ./migrate_audio_to_release.sh --check    read-only: what would move, sizes, what is already on the Release
#   ./migrate_audio_to_release.sh --phase1   PUBLISHES: upload missing assets -> verify each (HEAD 200 + exact byte
#                                            length) -> write audio_release_manifest.json -> rebuild + validate the
#                                            feed (xmllint, same GUID set, every enclosure HEAD-checked) -> commit ->
#                                            push -> Podcast Index ping. Pages keeps serving the old copies meanwhile.
#   ./migrate_audio_to_release.sh --phase2 [--force]
#                                            >= 3 days after phase 1 (apps have re-read the feed): stop serving the
#                                            MP3s from Pages (git rm --cached audio/*.mp3 + .gitignore, local copies
#                                            moved to audio_release/), rebuild, commit, push. Site drops to a few MB.
# Needs: gh (authenticated: gh auth status), git, curl, python3, ffprobe, xmllint.
set -euo pipefail
cd "$(dirname "$0")"
REPO=bmob222/jrm-podcast
REL=https://github.com/$REPO/releases/download/audio
FEED=https://bmob222.github.io/jrm-podcast/feed.xml
MODE=${1:---check}
FORCE=${2:-}

die() { echo "ABORT: $*" >&2; exit 1; }

legacy_files() {   # MP3s the working-tree feed still serves from Pages
  python3 - <<'EOF'
import xml.etree.ElementTree as ET
for i in ET.parse("feed.xml").getroot().find("channel").findall("item"):
    u = i.find("enclosure").get("url")
    if "/jrm-podcast/audio/" in u:
        print(u.rsplit("/", 1)[1])
EOF
}

ASSETS=.release_assets.txt
load_assets() {    # one API call: "<name> <size>" per Release asset
  gh release view audio -R "$REPO" --json assets -q '.assets[] | "\(.name) \(.size)"' > "$ASSETS"
}
asset_size() {     # size of a Release asset by name, or empty
  awk -v n="$1" '$1==n {print $2}' "$ASSETS"
}

remote_len() {     # "<http code> <content-length>" after redirects (HEAD)
  curl -sIL --max-time 60 "$1" | tr -d '\r' | awk 'toupper($1) ~ /^HTTP/ {code=$2} tolower($1)=="content-length:" {cl=$2} END {print code, cl}'
}

verify_feed() {    # xmllint + same GUID set as the committed feed + every enclosure reachable with the exact length
  xmllint --noout feed.xml
  git show HEAD:feed.xml > .feed_head.xml
  python3 - <<'EOF'
import xml.etree.ElementTree as ET, sys
g = lambda p: sorted(i.findtext("guid") for i in ET.parse(p).getroot().find("channel").findall("item"))
old, new = g(".feed_head.xml"), g("feed.xml")
if old != new:
    print("GUID set changed:", sorted(set(old) ^ set(new))); sys.exit(1)
print("GUID set unchanged (%d items)" % len(new))
EOF
  rm -f .feed_head.xml
  python3 - <<'EOF' > .enclosures.txt
import xml.etree.ElementTree as ET
for i in ET.parse("feed.xml").getroot().find("channel").findall("item"):
    e = i.find("enclosure"); print(e.get("url"), e.get("length"))
EOF
  local bad=0
  while read -r url len; do
    read -r code cl < <(remote_len "$url")
    if [ "$code" != "200" ] || [ "$cl" != "$len" ]; then echo "  BAD $url -> $code $cl (want $len)"; bad=1; fi
  done < .enclosures.txt
  rm -f .enclosures.txt
  [ "$bad" = 0 ] || die "some enclosures are not reachable with the right length"
  echo "all enclosures OK"
}

preflight() {
  gh auth status >/dev/null 2>&1 || die "gh is not authenticated (gh auth login / gh auth setup-git)"
  git diff --quiet && git diff --cached --quiet || die "uncommitted changes to tracked files — commit or stash first"
  git fetch -q origin
  [ "$(git rev-list --count HEAD..@{u})" = "0" ] || die "local branch is behind origin — pull first"
}

case "$MODE" in
  --check)
    load_assets
    n=0; total=0; on_rel=0
    while read -r f; do
      [ -f "audio/$f" ] || die "audio/$f missing locally"
      s=$(stat -f%z "audio/$f"); n=$((n+1)); total=$((total+s))
      r=$(asset_size "$f" || true)
      if [ -n "$r" ]; then on_rel=$((on_rel+1)); [ "$r" = "$s" ] || echo "  SIZE MISMATCH on Release: $f ($r vs $s)"; fi
    done < <(legacy_files)
    echo "legacy Pages MP3s in the feed: $n ($((total/1048576)) MiB); already on the Release: $on_rel"
    rm -f "$ASSETS"
    echo "Pages site tree: $(git ls-files -z | xargs -0 stat -f%z 2>/dev/null | awk '{s+=$1} END {printf "%.0f MiB", s/1048576}')"
    ;;
  --phase1)
    preflight
    files=$(legacy_files)
    [ -n "$files" ] || die "nothing to migrate (feed has no Pages enclosures)"
    load_assets
    for f in $files; do
      s=$(stat -f%z "audio/$f")
      r=$(asset_size "$f" || true)
      if [ -z "$r" ]; then
        echo "upload $f ($s bytes)"; gh release upload audio "audio/$f" -R "$REPO"
      elif [ "$r" != "$s" ]; then
        die "$f exists on the Release with a different size ($r vs $s) — resolve by hand"
      else
        echo "already on the Release: $f"
      fi
      read -r code cl < <(remote_len "$REL/$f")
      [ "$code" = "200" ] && [ "$cl" = "$s" ] || die "$REL/$f -> $code $cl (want $s)"
    done
    rm -f "$ASSETS"
    python3 - "$files" <<'EOF'
import json, os, sys, datetime
files = sys.argv[1].split()
m = {"migrated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
     "note": "legacy MP3s served from the GitHub Release 'audio'; GUIDs unchanged",
     "files": {f: os.path.getsize(os.path.join("audio", f)) for f in files}}
json.dump(m, open("audio_release_manifest.json", "w"), indent=1); print("manifest:", len(files), "files")
EOF
    python3 build_feed.py
    verify_feed
    git add audio_release_manifest.json feed.xml
    git commit -qm "Podcast audio: serve the legacy MP3s from the 'audio' Release (GUIDs unchanged)"
    git push -q origin HEAD
    curl -s --max-time 20 "https://api.podcastindex.org/api/1.0/hub/pubnotify?url=$FEED" || true; echo
    echo "PHASE 1 DONE. Run --phase2 in >= 3 days (after Spotify/Apple have re-read the feed)."
    ;;
  --phase2)
    preflight
    [ -f audio_release_manifest.json ] || die "run --phase1 first"
    python3 - "$FORCE" <<'EOF' || exit 1
import json, sys, datetime
m = json.load(open("audio_release_manifest.json"))
age = datetime.datetime.now().astimezone() - datetime.datetime.fromisoformat(m["migrated_at"])
if age.days < 3 and sys.argv[1] != "--force":
    sys.exit("ABORT: phase 1 was only %s ago — wait 3 days or pass --force" % age)
EOF
    if git show HEAD:feed.xml | grep -q "jrm-podcast/audio/"; then die "committed feed still points at Pages audio/"; fi
    mkdir -p audio_release
    for f in $(python3 -c "import json; print(' '.join(json.load(open('audio_release_manifest.json'))['files']))"); do
      if git ls-files --error-unmatch "audio/$f" >/dev/null 2>&1; then git rm -q --cached "audio/$f"; fi
      if [ -f "audio/$f" ] && [ ! -f "audio_release/$f" ]; then mv "audio/$f" "audio_release/$f"; fi
    done
    grep -qx 'audio/\*.mp3' .gitignore || printf 'audio/*.mp3\n' >> .gitignore
    python3 build_feed.py
    verify_feed
    git add .gitignore feed.xml
    git commit -qm "Pages: stop hosting podcast MP3s (served from the 'audio' Release since phase 1)"
    git push -q origin HEAD
    echo "PHASE 2 DONE. Pages redeploys in a few minutes; then $FEED must still list every episode and"
    echo "https://bmob222.github.io/jrm-podcast/audio/ep01_2025-09-07_sunday-message.mp3 should return 404."
    ;;
  *) echo "usage: $0 --check | --phase1 | --phase2 [--force]"; exit 2 ;;
esac
