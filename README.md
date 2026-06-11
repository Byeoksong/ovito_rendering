# OVITO Rendering Workflow

OVITO Python API를 이용해 atomistic trajectory의 특정 frame들을 PNG 이미지로 렌더링하고, 생성된 PNG들을 GIF 애니메이션으로 변환하는 작업용 repository입니다.

현재 workflow는 주로 XDATCAR 계열 trajectory를 대상으로 합니다.

## Repository Structure

```text
.
├── 00_data/              # local input data, ignored by git
├── 01_src/               # Python source code
│   ├── 00_render_color_by_element.py
│   ├── 01_png_to_gif.py
│   ├── 02_shift_coordinate.py
│   ├── 03_plot_traj.py
│   └── README.md
├── 02_script/            # shell workflow scripts
│   ├── 00_script.sh
│   └── 01_script_png_gif.sh
├── 03_results/           # generated PNG/GIF outputs, ignored by git
├── 99_archieve/          # archived/reference files, ignored by git
├── AGENTS.md
└── README.md
```

`00_data/`, `03_results/`, `99_archieve/`는 `.gitignore`에 포함되어 GitHub에는 업로드되지 않습니다.

## Requirements

Python에서 OVITO 모듈을 사용할 수 있어야 합니다.

GIF 변환에는 `Pillow`가 필요합니다.

```bash
pip install pillow
```

OVITO 설치는 사용하는 Python/conda 환경에 맞게 준비해야 합니다.

## Main Workflow

### 1. Prepare Input Data

입력 trajectory 파일은 로컬의 `00_data/` 아래에 둡니다.

예:

```text
00_data/XDATCAR
00_data/xdatcar_shift
```

이 디렉터리는 GitHub에 올라가지 않으므로, 다른 환경에서 실행하려면 데이터를 별도로 준비해야 합니다.

### 2. Render PNG Frames

`02_script/00_script.sh`의 설정값을 수정합니다.

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

실행:

```bash
zsh 02_script/00_script.sh
```

생성 파일 예:

```text
03_results/03_slice/slice_top_2000.png
03_results/03_slice/slice_front_2000.png
03_results/03_slice/slice_top_2005.png
03_results/03_slice/slice_front_2005.png
```

### 3. Convert PNG Frames to GIF

`02_script/01_script_png_gif.sh`의 설정값을 수정합니다.

```bash
RESULT_DIR="03_results/02_slice"
VIEW="front"
```

실행:

```bash
zsh 02_script/01_script_png_gif.sh
```

생성 파일 예:

```text
03_results/02_slice/00_slice_front.gif
```

## Key Scripts

### `01_src/00_render_color_by_element.py`

OVITO를 이용해 구조 파일 또는 trajectory의 특정 frame을 렌더링합니다.

주요 기능:

- 원소 종류에 따른 색상 지정
- 원소별 렌더링 radius 지정
- XDATCAR frame 선택
- `a1`, `a2`, `a3` lattice 방향 반복
- z 범위 filtering
- top/front/ortho/perspective camera 선택
- viewport 중심과 크기 조절
- lattice cell 선 숨김

단일 frame 렌더링 예:

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

색상은 코드 상단의 `ELEMENT_COLOR_MAP`에서 수정합니다. Hex color, RGB 0-255, RGB 0-1 형식을 사용할 수 있습니다.

```python
ELEMENT_COLOR_MAP = {
    "Li": "#FF0000",
    "N":  (77, 77, 77),
}
```

### `01_src/01_png_to_gif.py`

연속 PNG 파일을 frame 번호 순서대로 읽어 GIF로 변환합니다.

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

XDATCAR 계열 direct coordinate를 shift하여 `xdatcar_shift` 형태의 파일을 만드는 보조 스크립트입니다.

### `01_src/03_plot_traj.py`

Trajectory 분석 또는 시각화를 위한 보조 plotting 스크립트입니다.

## Notes

- Frame index는 0부터 시작합니다.
- `xdatcar_shift`처럼 lowercase 파일명은 OVITO가 단일 POSCAR처럼 읽는 경우가 있어, 렌더링 스크립트 내부에서 XDATCAR 이름으로 임시 symlink를 만들어 처리합니다.
- `--view-center`와 `--view-size`는 Cartesian 좌표 기준입니다. XDATCAR/POSCAR 계열에서는 일반적으로 Å 단위입니다.
- 자세한 script별 옵션 설명은 `01_src/README.md`를 참고하세요.

## Git Usage

작업 전 상태 확인:

```bash
git status
```

변경사항 저장:

```bash
git add .
git commit -m "Describe the change"
git push
```

커밋 전 변경사항 되돌리기:

```bash
git restore .
```

특정 파일만 되돌리기:

```bash
git restore 01_src/00_render_color_by_element.py
```
