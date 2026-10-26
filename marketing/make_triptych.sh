#!/usr/bin/env sh
# Builds 02_glance_triptych.png from the three close-up renders (any resolution).
# Run inside: nix shell nixpkgs#imagemagick --command sh make_triptych.sh
set -e
cd "$(dirname "$0")"
F=DejaVu-Sans; FB=DejaVu-Sans-Bold
W=$(magick identify -format %w 02_glance_green.png)
S=$((W / 800))   # scale text with the render width
[ "$S" -lt 1 ] && S=1
label() {  # file  temp  caption  colour  out
  magick "$1" \
    \( -size "${W}x$((170 * S))" xc:"#0b1214" \
       -font "$FB" -pointsize $((54 * S)) -fill "$4" -gravity north -annotate +0+$((22 * S)) "$2" \
       -font "$F" -pointsize $((30 * S)) -fill "#c9d4d6" -gravity north -annotate +0+$((102 * S)) "$3" \) \
    -append "$5"
}
label 02_glance_blue.png  "below 24 °C" "too cold"   "#5b8cff" _t_blue.png
label 02_glance_green.png "24 – 27 °C"  "just right" "#47e07a" _t_green.png
label 02_glance_red.png   "above 27 °C" "too warm"   "#ff5a3c" _t_red.png
magick _t_blue.png _t_green.png _t_red.png +append \
  \( -size "$((3 * W))x$((150 * S))" xc:"#0b1214" -font "$FB" -pointsize $((58 * S)) -fill white -gravity center \
     -annotate +0+0 "Your tank's temperature. Readable from across the room." \) \
  +swap -append 02_glance_triptych.png
rm -f _t_blue.png _t_green.png _t_red.png
echo "wrote 02_glance_triptych.png"
