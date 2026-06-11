#!/usr/bin/env zsh

INPUT="00_data/xdatcar_shift"
FRAME_INITIAL="2000"
FRAME_FINAL="2800"
FRAME_INTERVAL="50"
Z_MIN="-0.066"
Z_MAX="0.071"
REPEAT_A1="3"
REPEAT_A2="3"
REPEAT_A3="1"
FILE_NAME="03_results/05_slice/slice"
VIEW_CENTER_X="7.317801"
# VIEW_CENTER_Y="-1.82945025"
VIEW_CENTER_Y="-2.2"
VIEW_CENTER_Z="0"
VIEW_SIZE="6"
WIDTH="1600"
HEIGHT="1600"
ALPHA_INITIAL="0.4"
ALPHA_FINAL="0.4"

OUTPUT_DIR="$(dirname "$FILE_NAME")"
if [[ "$OUTPUT_DIR" != "." ]]; then
    mkdir -p "$OUTPUT_DIR"
fi

VIEW_OPTIONS=()
if [[ -n "$VIEW_SIZE" ]]; then
    VIEW_OPTIONS+=(--view-size "$VIEW_SIZE")
fi
if [[ -n "$VIEW_CENTER_X" && -n "$VIEW_CENTER_Y" && -n "$VIEW_CENTER_Z" ]]; then
    VIEW_OPTIONS+=(--view-center "$VIEW_CENTER_X" "$VIEW_CENTER_Y" "$VIEW_CENTER_Z")
fi

for FRAME in $(seq "$FRAME_INITIAL" "$FRAME_INTERVAL" "$FRAME_FINAL"); do
    ATOM_ALPHA="$(awk \
        -v frame="$FRAME" \
        -v initial="$FRAME_INITIAL" \
        -v final="$FRAME_FINAL" \
        -v alpha_initial="$ALPHA_INITIAL" \
        -v alpha_final="$ALPHA_FINAL" \
        'BEGIN {
            if (final == initial) {
                printf "%.6f", alpha_final
            } else {
                printf "%.6f", alpha_initial + (alpha_final - alpha_initial) * (frame - initial) / (final - initial)
            }
        }')"

    python 01_src/00_render_color_by_element.py "$INPUT" \
        -f "$FRAME" \
        --z-min "$Z_MIN" --z-max "$Z_MAX" --z-coordinate direct \
        -o "${FILE_NAME}_top_${FRAME}.png" \
        --repeat-a "$REPEAT_A1" "$REPEAT_A2" "$REPEAT_A3" \
        --camera top \
        --atom-alpha "$ATOM_ALPHA" \
        --width "$WIDTH" --height "$HEIGHT" \
        "${VIEW_OPTIONS[@]}" \
        --transparent-background \
        --hide-cell

    # python 01_src/00_render_color_by_element.py "$INPUT" \
    #     -f "$FRAME" \
    #     --z-min "$Z_MIN" --z-max "$Z_MAX" --z-coordinate direct \
    #     -o "${FILE_NAME}_front_${FRAME}.png" \
    #     --repeat-a "$REPEAT_A1" "$REPEAT_A2" "$REPEAT_A3" \
    #     --camera front \
    #     --atom-alpha "$ATOM_ALPHA" \
    #     --width "$WIDTH" --height "$HEIGHT" \
    #     "${VIEW_OPTIONS[@]}" \
    #     --transparent-background \
    #     --hide-cell
done
