# Source Scripts

This document describes the Python scripts in `01_src/`.

## `00_render_color_by_element.py`

`00_render_color_by_element.py` renders one frame of a structure or trajectory using the OVITO Python API.

Atoms are colored by their own element type, not by nearest-neighbor information. Element colors are configured in `ELEMENT_COLOR_MAP` near the top of the script.

```python
ELEMENT_COLOR_MAP = {
    "Li": "#2680E3",
    "N":  "#858585",
}
```

The color map accepts three formats:

- Hex color: `"#2680E3"`
- RGB 0-255 tuple: `(38, 128, 227)`
- RGB 0-1 tuple: `(0.15, 0.50, 0.89)`

Element rendering radii are configured in `ELEMENT_RADIUS_MAP`.

```python
ELEMENT_RADIUS_MAP = {
    "Li": 0.8,
    "N":  0.5,
}
```

Atom transparency is configured in `ELEMENT_TRANSPARENCY_MAP`. `0.0` is fully opaque and `1.0` is invisible.

```python
ELEMENT_TRANSPARENCY_MAP = {
    "Li": 0.0,
    "N":  0.0,
}
```

### Basic Usage

Render a single frame:

```bash
python 01_src/00_render_color_by_element.py 00_data/xdatcar_shift \
  -f 2000 \
  -o 03_results/example_top_2000.png \
  --camera top
```

Render both top and front views by running the command twice with different camera and output options:

```bash
python 01_src/00_render_color_by_element.py 00_data/xdatcar_shift -f 2000 --camera top   -o 03_results/slice_top_2000.png
python 01_src/00_render_color_by_element.py 00_data/xdatcar_shift -f 2000 --camera front -o 03_results/slice_front_2000.png
```

### Options

- `input`: Input structure or trajectory file. Examples: `XDATCAR`, `xdatcar_shift`, `POSCAR`, `xyz`, LAMMPS dump.
- `-o`, `--output`: Output PNG file path. Default: `element_colored.png`.
- `-f`, `--frame`: Frame index to render. Frame numbering starts at `0`.
- `--width`: Image width in pixels.
- `--height`: Image height in pixels.
- `--camera`: Camera mode. Choices: `perspective`, `ortho`, `top`, `front`.
- `--transparent-background`: Render PNG with a transparent background. This is the default.
- `--opaque-background`: Render PNG with an opaque white background.
- `--repeat-a A1 A2 A3`: Repeat the structure along lattice vectors `a1`, `a2`, and `a3`.
- `--hide-cell`: Hide simulation cell/lattice box lines.
- `--z-min`: Minimum z value to keep.
- `--z-max`: Maximum z value to keep.
- `--z-coordinate`: Coordinate system for `--z-min` and `--z-max`. Choices: `cartesian`, `direct`.
- `--view-center X Y Z`: Cartesian point at the center of the rendered view.
- `--view-size`: Orthographic viewport size. Smaller values zoom in.

### Periodic Repetition

Use `--repeat-a` to show periodic repetitions based on the lattice vectors.

```bash
python 01_src/00_render_color_by_element.py 00_data/xdatcar_shift \
  -f 2000 \
  --repeat-a 3 3 1 \
  --camera top \
  -o 03_results/repeated_top_2000.png
```

This example repeats the structure 3 times along `a1`, 3 times along `a2`, and 1 time along `a3`.

### Z Range Filtering

Use `--z-min` and `--z-max` to keep only atoms within a selected z range.

Direct coordinate example:

```bash
python 01_src/00_render_color_by_element.py 00_data/xdatcar_shift \
  -f 2000 \
  --z-min -0.0625 \
  --z-max 0.0625 \
  --z-coordinate direct \
  -o 03_results/slice_top_2000.png
```

Cartesian coordinate example:

```bash
python 01_src/00_render_color_by_element.py structure.xyz \
  --z-min 5.0 \
  --z-max 10.0 \
  --z-coordinate cartesian \
  -o 03_results/z_slice.png
```

`--z-coordinate direct` requires a simulation cell.

### Viewport Control

`--view-center` and `--view-size` adjust the camera/viewport without deleting atoms. This is useful when you want to zoom into a specific region, similar in spirit to setting plot limits.

```bash
python 01_src/00_render_color_by_element.py 00_data/xdatcar_shift \
  -f 2000 \
  --camera top \
  --view-center 0 0 0 \
  --view-size 12 \
  -o 03_results/zoomed_top_2000.png
```

These options are intended for orthographic cameras: `top`, `front`, and `ortho`. They are not compatible with `perspective`.

Units are Cartesian coordinate units from the input file. For VASP `XDATCAR`/`POSCAR` files, this is typically angstrom.

`--view-size` controls the vertical size of the orthographic viewport. The horizontal range depends on the image aspect ratio.

### Background Transparency

PNG images are rendered with a transparent background by default.

```bash
python 01_src/00_render_color_by_element.py 00_data/xdatcar_shift \
  -f 2000 \
  --camera top \
  -o 03_results/transparent.png
```

Use `--opaque-background` when a white opaque background is needed.

```bash
python 01_src/00_render_color_by_element.py 00_data/xdatcar_shift \
  -f 2000 \
  --camera top \
  --opaque-background \
  -o 03_results/opaque.png
```

### Example Used by `02_script/00_script.sh`

The main shell workflow repeatedly runs the renderer for a frame range.

```bash
python 01_src/00_render_color_by_element.py "$INPUT" \
  -f "$FRAME" \
  --z-min "$Z_MIN" --z-max "$Z_MAX" --z-coordinate direct \
  -o "${FILE_NAME}_top_${FRAME}.png" \
  --repeat-a "$REPEAT_A1" "$REPEAT_A2" "$REPEAT_A3" \
  --camera top \
  --width "$WIDTH" --height "$HEIGHT" \
  "${VIEW_OPTIONS[@]}" \
  --transparent-background \
  --hide-cell
```

Set `FRAME_INITIAL`, `FRAME_FINAL`, and `FRAME_INTERVAL` in `02_script/00_script.sh` to generate a PNG sequence.

### XDATCAR Filename Note

OVITO may detect XDATCAR trajectories based on filename patterns. For example, `XDATCAR` is read as a trajectory, while a same-format lowercase file such as `xdatcar_shift` may be read as a single POSCAR-like structure.

`00_render_color_by_element.py` handles this by creating a temporary `XDATCAR_...` symlink internally when the input filename contains `xdatcar`.

The script also validates the requested frame index. For example, a trajectory with 8023 frames accepts frame indices from `0` to `8022`.

## `01_png_to_gif.py`

`01_png_to_gif.py` combines a sequence of PNG files into a GIF animation.

### Requirements

GIF generation requires `Pillow`.

```bash
pip install pillow
```

### Basic Usage

Create a GIF from top-view PNG files:

```bash
python 01_src/01_png_to_gif.py \
  -i 03_results/03_slice \
  -t "slice_top_{frame}.png" \
  --start 2000 \
  --end 2800 \
  --step 5 \
  -o 03_results/03_slice/00_slice_top.gif \
  --fps 10
```

Create a GIF from front-view PNG files:

```bash
python 01_src/01_png_to_gif.py \
  -i 03_results/03_slice \
  -t "slice_front_{frame}.png" \
  --start 2000 \
  --end 2800 \
  --step 5 \
  -o 03_results/03_slice/00_slice_front.gif \
  --fps 10
```

### Options

- `-i`, `--input-dir`: Directory containing PNG files.
- `-t`, `--template`: Filename template containing `{frame}`.
- `--start`: First frame number.
- `--end`: Last frame number. This frame is included.
- `--step`: Frame interval.
- `-o`, `--output`: Output GIF file path.
- `--fps`: Frames per second. Larger values make the GIF play faster.
- `--loop`: Number of GIF loops. `0` means infinite looping.
- `-p`, `--pattern`: Glob pattern mode, e.g. `slice_top_*.png`.

When `--template`, `--start`, `--end`, and `--step` are used, files are read in the exact frame-number order. For example, `--start 2000 --end 2800 --step 5` reads `2000, 2005, 2010, ... 2800`.

The `--pattern` mode uses natural sorting based on numbers in filenames.

## `02_shift_coordinate.py`

Helper script for shifting direct coordinates from an XDATCAR-style trajectory and writing an `xdatcar_shift`-style output file.

## `03_plot_traj.py`

Helper script for trajectory analysis or plotting.
