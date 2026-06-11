# OVITO Rendering Workflow

This repository contains a small OVITO-based workflow for rendering atomistic trajectory frames as PNG images and converting the generated PNG sequence into GIF animations.

The current workflow is mainly designed for VASP `XDATCAR`-style trajectory files.

## Repository Structure

```text
.
├── 00_data/              # Local input data, ignored by git
├── 01_src/               # Python source code
│   ├── 00_render_color_by_element.py
│   ├── 01_png_to_gif.py
│   ├── 02_shift_coordinate.py
│   ├── 03_plot_traj.py
│   └── README.md
├── 02_script/            # Shell workflow scripts
│   ├── 00_script.sh
│   └── 01_script_png_gif.sh
├── 03_results/           # Generated PNG/GIF outputs, ignored by git
├── 99_archieve/          # Archived/reference files, ignored by git
├── AGENTS.md
└── README.md
```

The following directories are intentionally ignored by git:

- `00_data/`
- `03_results/`
- `99_archieve/`

Input data and generated outputs should be managed locally.

## Requirements

The rendering scripts require the OVITO Python module.

GIF generation requires `Pillow`.

```bash
pip install pillow
```

Install OVITO in the Python or conda environment used to run the scripts.

## Workflow

### 1. Prepare Input Data

Place input structure or trajectory files under `00_data/`.

Examples:

```text
00_data/XDATCAR
00_data/xdatcar_shift
```

Because `00_data/` is ignored by git, data files must be prepared separately on each machine.

### 2. Render PNG Frames

Edit the variables in `02_script/00_script.sh`.

```bash
INPUT="00_data/xdatcar_shift"
FRAME_INITIAL="2000"
FRAME_FINAL="2800"
FRAME_INTERVAL="5"
Z_MIN="-0.066"
Z_MAX="0.07"
REPEAT_A1="3"
REPEAT_A2="3"
REPEAT_A3="1"
FILE_NAME="03_results/03_slice/slice"
```

Run:

```bash
zsh 02_script/00_script.sh
```

Example output files:

```text
03_results/03_slice/slice_top_2000.png
03_results/03_slice/slice_front_2000.png
03_results/03_slice/slice_top_2005.png
03_results/03_slice/slice_front_2005.png
```

### 3. Convert PNG Frames to GIF

Edit the variables in `02_script/01_script_png_gif.sh`.

```bash
RESULT_DIR="03_results/02_slice"
VIEW="front"
```

Run:

```bash
zsh 02_script/01_script_png_gif.sh
```

Example output:

```text
03_results/02_slice/00_slice_front.gif
```

## Main Scripts

### `01_src/00_render_color_by_element.py`

Renders one frame of a structure or trajectory using the OVITO Python API.

Main features:

- Element-based atom coloring
- Per-element rendering radius
- Per-element transparency or frame-dependent global atom alpha
- XDATCAR frame selection
- Periodic repetition along lattice vectors `a1`, `a2`, and `a3`
- z-range filtering
- `top`, `front`, `ortho`, and `perspective` camera modes
- Manual viewport center and size control
- Optional simulation cell hiding
- Transparent PNG background by default

Single-frame rendering example:

```bash
python 01_src/00_render_color_by_element.py 00_data/xdatcar_shift \
  -f 2000 \
  --camera top \
  --repeat-a 3 3 1 \
  --z-min -0.066 --z-max 0.07 --z-coordinate direct \
  --view-center 7.317801 -2.2 0 \
  --view-size 6 \
  --hide-cell \
  -o 03_results/example_top_2000.png
```

Element colors are configured in `ELEMENT_COLOR_MAP` near the top of the script. Hex colors, RGB 0-255 tuples, and RGB 0-1 tuples are supported.

```python
ELEMENT_COLOR_MAP = {
    "Li": "#FF0000",
    "N":  (77, 77, 77),
}
```

Element radii are configured in `ELEMENT_RADIUS_MAP`.

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

Tachyon rendering style is configured in the renderer script. These values can be toggled in code without changing CLI options.

```python
RENDER_AMBIENT_OCCLUSION = True
RENDER_SHADOWS = True
RENDER_ANTIALIASING = True
```

For frame-dependent fade-in rendering, pass `--atom-alpha`. `0.0` is invisible and `1.0` is fully opaque.

```bash
python 01_src/00_render_color_by_element.py 00_data/xdatcar_shift \
  -f 2000 \
  --camera top \
  --atom-alpha 0.5 \
  -o 03_results/example_alpha_2000.png
```

### `01_src/01_png_to_gif.py`

Reads PNG files in frame-number order and writes a GIF animation.

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

### `01_src/02_shift_coordinate.py`

Helper script for shifting direct coordinates from an XDATCAR-style trajectory and writing an `xdatcar_shift`-style output file.

### `01_src/03_plot_traj.py`

Helper script for trajectory analysis or plotting.

## Notes

- Frame indices are zero-based.
- `--view-center` and `--view-size` use Cartesian coordinates. For VASP `XDATCAR`/`POSCAR` files, this is typically in angstrom.
- `--view-size` controls the vertical size of the orthographic viewport. The horizontal range depends on the image aspect ratio.
- PNG output uses a transparent background by default. Use `--opaque-background` to render a white background instead.
- Lowercase filenames such as `xdatcar_shift` may be detected by OVITO as a single POSCAR-like structure. The renderer handles this by creating a temporary `XDATCAR_...` symlink internally.
- Detailed script-level documentation is available in `01_src/README.md`.

## Git Usage

Check the working tree:

```bash
git status
```

Commit and push changes:

```bash
git add .
git commit -m "Describe the change"
git push
```

Discard uncommitted changes:

```bash
git restore .
```

Restore one file:

```bash
git restore 01_src/00_render_color_by_element.py
```
