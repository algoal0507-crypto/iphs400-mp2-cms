#!/bin/sh
# Make the web copies of the site photos from the untouched originals.
#
#   sh scripts/make_web_images.sh
#
# Needs macOS `sips` (it ships with macOS; no Python dependency is added). The
# results are committed in assets/images/web/, so `cms publish` and anyone cloning
# the repo do not need this script. The originals in assets/images/ are never
# modified. They are phone screenshots, so each crop below only cuts pixels away
# (no scaling of one axis, so nothing is stretched): the screenshot controls at the
# edges (sound icon, scroll handle, status bars) are outside the crop.
#
# crop = HEIGHT WIDTH OFFSET_Y OFFSET_X, measured on the original.
set -eu
cd "$(dirname "$0")/.."
SRC=assets/images
OUT=assets/images/web
TMP=$(mktemp -d)
mkdir -p "$OUT"

make() {  # name original height width offset_y offset_x width...
  name=$1; src=$2; h=$3; w=$4; oy=$5; ox=$6; shift 6
  sips -c "$h" "$w" --cropOffset "$oy" "$ox" "$SRC/$src" --out "$TMP/$name.png" >/dev/null
  for width in "$@"; do
    sips -s format jpeg -s formatOptions 82 --resampleWidth "$width" "$TMP/$name.png" \
      --out "$OUT/$name-$width.jpg" >/dev/null
  done
}

# IMG_8489: the tray of tacos. Bottom 50 px cut (circular control at the lower right).
make home       IMG_8489.jpg 1456 1206   0 0 480 800 1200
# IMG_8452: the taco on its plate. Top 290 px (bowls) and bottom 123 px (sound icon) cut.
make menu       IMG_8452.jpg 1190 1206 290 0 480 800 1200
# portrait.png: top 20 px (bar), bottom 63 px (control), right 30 px (scroll handle) cut.
make our-story  portrait.png 1330 1176  20 0 480 800 1176

rm -rf "$TMP"
ls -l "$OUT"
