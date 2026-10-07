#!/bin/bash
# bh-042: free (CC0) itch.io download through the page's own download flow. usage: itch_fetch.sh <project> <outdir>
P=$1; OUT=$2; J=$(mktemp); mkdir -p "$OUT"
PAGE=$(curl -s -c $J -b $J "https://quaternius.itch.io/$P")
CSRF=$(echo "$PAGE" | grep -oE 'name="csrf_token" value="[^"]+"' | head -1 | sed 's/.*value="//;s/"$//')
[ -z "$CSRF" ] && CSRF=$(echo "$PAGE" | grep -oE '"csrf_token":"[^"]+"' | head -1 | sed 's/.*:"//;s/"$//')
DL=$(curl -s -c $J -b $J -X POST -d "csrf_token=$CSRF" "https://quaternius.itch.io/$P/download_url" | grep -oE '"url":"[^"]+"' | sed 's/"url":"//;s/"$//;s/\//g')
echo "download page: $DL"
DPAGE=$(curl -s -c $J -b $J "$DL")
KEY=$(echo "$DL" | sed 's|.*/download/||')
CSRF2=$(echo "$DPAGE" | grep -oE 'name="csrf_token" value="[^"]+"' | head -1 | sed 's/.*value="//;s/"$//')
echo "$DPAGE" | grep -oE 'data-upload_id="[0-9]+"' | sed 's/[^0-9]//g' | sort -u > $J.ids
echo "$DPAGE" | grep -oE 'class="name" title="[^"]+"' > $J.names
cat $J.names
for U in $(cat $J.ids); do
  URL=$(curl -s -c $J -b $J -X POST -d "csrf_token=$CSRF2" "https://quaternius.itch.io/$P/file/$U?source=game_download&key=$KEY" | grep -oE '"url":"[^"]+"' | sed 's/"url":"//;s/"$//;s/\//g')
  echo "upload $U -> ${URL:0:80}"
  [ -n "$URL" ] && curl -sL -o "$OUT/upload_$U.bin" -D "$OUT/upload_$U.hdr" "$URL"
done
