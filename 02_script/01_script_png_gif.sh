#!/usr/bin/env zsh

RESULT_DIR="03_results/02_slice"
# VIEW="top"
VIEW="front"

python3 ./01_src/01_png_to_gif.py \
  -i "$RESULT_DIR" \
  -t "slice_${VIEW}_{frame}.png" \
  --start 2000 \
  --end 2800 \
  --step 5 \
  -o "$RESULT_DIR/00_slice_${VIEW}.gif" \
  --fps 10
