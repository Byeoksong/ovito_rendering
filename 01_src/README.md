# `00_render_color_by_element.py`

`render_color_by_element.py`는 OVITO Python API를 이용해 구조 파일 또는 trajectory 파일의 특정 frame을 PNG 이미지로 렌더링하는 스크립트입니다.

각 atom의 색은 이웃 원자가 아니라 atom 자신의 원소 종류(`Particle Type`)를 기준으로 정해집니다. 색상은 파일 안의 `ELEMENT_COLOR_MAP`에서 수정할 수 있습니다.

```python
ELEMENT_COLOR_MAP = {
    "Li": (1.00, 0.00, 0.00),
    "N":  (0.10, 0.20, 1.00),
}
```

Li와 N의 렌더링 반지름은 `ELEMENT_RADIUS_MAP`에서 수정합니다.

```python
ELEMENT_RADIUS_MAP = {
    "Li": 1.0,
    "N":  0.7,
}
```

## Basic Usage

단일 frame 렌더링:

```bash
python render_color_by_element.py xdatcar_shift \
  -f 2000 \
  -o slice_top_2000.png \
  --camera top
```

Top view와 front view를 각각 저장하려면 `--camera`와 `-o`를 바꿔 두 번 실행합니다.

```bash
python render_color_by_element.py xdatcar_shift -f 2000 --camera top   -o slice_top_2000.png
python render_color_by_element.py xdatcar_shift -f 2000 --camera front -o slice_front_2000.png
```

## Options

- `input`: 입력 구조 또는 trajectory 파일입니다. 예: `XDATCAR`, `xdatcar_shift`, `POSCAR`, `xyz`, LAMMPS dump 등.
- `-o`, `--output`: 저장할 PNG 파일명입니다. 기본값은 `element_colored.png`입니다.
- `-f`, `--frame`: 렌더링할 frame index입니다. 첫 frame은 `0`입니다.
- `--width`: 이미지 가로 pixel 수입니다.
- `--height`: 이미지 세로 pixel 수입니다.
- `--camera`: 카메라 방향입니다. 가능한 값은 `perspective`, `ortho`, `top`, `front`입니다.
- `--repeat-a A1 A2 A3`: lattice vector `a1`, `a2`, `a3` 방향으로 periodic structure를 반복합니다.
- `--hide-cell`: lattice box 선을 숨깁니다.
- `--z-min`: 표시할 z 범위의 최소값입니다.
- `--z-max`: 표시할 z 범위의 최대값입니다.
- `--z-coordinate`: `--z-min`, `--z-max`의 좌표 기준입니다. `cartesian` 또는 `direct`를 사용할 수 있습니다.
- `--view-center X Y Z`: 렌더링 viewport의 중심입니다. Cartesian 좌표 기준입니다.
- `--view-size`: orthographic viewport의 화면 크기입니다. 작을수록 확대됩니다.

## Periodic Repetition

XDATCAR/POSCAR의 lattice를 기준으로 주기적 반복 구조를 보여주려면 `--repeat-a`를 사용합니다.

```bash
python render_color_by_element.py xdatcar_shift \
  -f 2000 \
  --repeat-a 3 3 1 \
  --camera top \
  -o repeated_top_2000.png
```

위 예시는 `a1` 방향 3번, `a2` 방향 3번, `a3` 방향 1번으로 구조를 확장합니다.

## Z Range Filtering

특정 z 범위에 있는 atom만 남기고 렌더링할 수 있습니다.

Direct coordinate 기준:

```bash
python render_color_by_element.py xdatcar_shift \
  -f 2000 \
  --z-min -0.0625 \
  --z-max 0.0625 \
  --z-coordinate direct \
  -o slice_top_2000.png
```

Cartesian coordinate 기준:

```bash
python render_color_by_element.py structure.xyz \
  --z-min 5.0 \
  --z-max 10.0 \
  --z-coordinate cartesian \
  -o z_slice.png
```

`--z-coordinate direct`는 simulation cell이 있는 파일에서만 사용할 수 있습니다.

## Viewport Control

`--view-center`와 `--view-size`는 atom을 삭제하지 않고 카메라/viewport 영역만 조절합니다. `plt.xlim`, `plt.ylim`처럼 특정 부분만 확대해서 보고 싶을 때 사용합니다.

```bash
python render_color_by_element.py xdatcar_shift \
  -f 2000 \
  --camera top \
  --view-center 0 0 0 \
  --view-size 12 \
  -o zoomed_top_2000.png
```

`--view-center`와 `--view-size`는 `top`, `front`, `ortho` 같은 orthographic camera에서 사용하는 옵션입니다. `perspective` camera와 함께 사용하면 에러가 납니다.

단위는 입력 파일의 Cartesian 좌표 단위입니다. XDATCAR/POSCAR 계열에서는 일반적으로 Å입니다.

`--view-size`는 화면의 세로 방향 크기입니다. 예를 들어 `--width 1400 --height 1400 --view-size 12`이면 대략 12 Å x 12 Å 영역을 봅니다. 가로/세로 pixel 비율이 다르면 가로 방향 실제 범위도 그 비율만큼 달라집니다.

## Example Used by `script.sh`

현재 workflow에서는 `script.sh`가 여러 frame에 대해 아래와 같은 명령을 반복 실행합니다.

```bash
python render_color_by_element.py "$INPUT" \
  -f "$FRAME" \
  --z-min "$Z_MIN" --z-max "$Z_MAX" --z-coordinate direct \
  -o "${FILE_NAME}_top_${FRAME}.png" \
  --repeat-a "$REPEAT_A1" "$REPEAT_A2" "$REPEAT_A3" \
  --camera top \
  --width "$WIDTH" --height "$HEIGHT" \
  "${VIEW_OPTIONS[@]}" \
  --hide-cell
```

`script.sh`에서 `FRAME_INITIAL`, `FRAME_FINAL`, `FRAME_INTERVAL`을 지정하면 여러 frame의 PNG가 자동 생성됩니다.

## XDATCAR File Name Note

OVITO는 XDATCAR trajectory를 파일명 패턴에 민감하게 인식할 수 있습니다. 예를 들어 `XDATCAR`는 여러 frame으로 읽히지만, 같은 형식의 파일이라도 `xdatcar_shift`처럼 lowercase 이름이면 단일 POSCAR frame처럼 읽힐 수 있습니다.

`render_color_by_element.py`는 이 문제를 피하기 위해 파일명에 `xdatcar`가 포함되어 있으면 임시로 `XDATCAR_...` 이름의 symlink를 만들어 OVITO가 trajectory로 읽도록 처리합니다.

또한 `-f`, `--frame` 값이 실제 frame 범위를 벗어나면 에러를 냅니다. 예를 들어 8023 frames가 있는 trajectory는 사용할 수 있는 frame index가 `0`부터 `8022`까지입니다.



# `01_png_to_gif.py`

이 디렉터리는 OVITO 렌더링 스크립트로 여러 PNG 프레임을 만들고, 생성된 PNG 파일들을 GIF 애니메이션으로 합치는 작업을 위한 코드입니다.

## Files

- `script.sh`: 여러 frame에 대해 `render_color_by_element.py`를 실행하여 PNG 이미지를 생성합니다.
- `render_color_by_element.py`: OVITO를 이용해 지정한 frame을 렌더링합니다.
- `png_to_gif.py`: PNG 이미지들을 파일명 순서대로 정렬한 뒤 GIF 파일로 합칩니다.

## Requirements

GIF 생성에는 `Pillow`가 필요합니다.

```bash
pip install pillow
```

OVITO 렌더링 스크립트를 실행하려면 Python에서 OVITO 모듈을 사용할 수 있어야 합니다.

## 1. Generate PNG Frames

`script.sh`의 설정값을 필요에 맞게 수정합니다.

```bash
INPUT="xdatcar_shift"
FRAME_INITIAL="2000"
FRAME_FINAL="2800"
FRAME_INTERVAL="10"
FILE_NAME="99_TEST/slice"
```

실행:

```bash
zsh script.sh
```

현재 설정에서는 아래와 같은 파일들이 생성됩니다.

```text
99_TEST/slice_top_2000.png
99_TEST/slice_top_2010.png
...
99_TEST/slice_front_2000.png
99_TEST/slice_front_2010.png
...
```

## 2. Combine PNG Files into GIF

Top view PNG 파일들을 GIF로 만들기:

```bash
python png_to_gif.py \
  -i 99_TEST \
  -t 'slice_top_{frame}.png' \
  --start 2000 \
  --end 2800 \
  --step 10 \
  -o 99_TEST/slice_top.gif \
  --fps 10
```

Front view PNG 파일들을 GIF로 만들기:

```bash
python png_to_gif.py \
  -i 99_TEST \
  -t 'slice_front_{frame}.png' \
  --start 2000 \
  --end 2800 \
  --step 10 \
  -o 99_TEST/slice_front.gif \
  --fps 10
```

## `png_to_gif.py` Options

Frame 범위를 직접 지정하는 방식:

```bash
python png_to_gif.py \
  --input-dir 99_TEST \
  --template 'slice_top_{frame}.png' \
  --start 2000 \
  --end 2800 \
  --step 10 \
  --output 99_TEST/slice_top.gif \
  --fps 10 \
  --loop 0
```

- `-i`, `--input-dir`: PNG 파일이 들어 있는 폴더입니다. 기본값은 `99_TEST`입니다.
- `-t`, `--template`: frame 번호가 들어갈 파일명 형식입니다. 반드시 `{frame}`을 포함해야 합니다.
- `--start`: 시작 frame 번호입니다.
- `--end`: 마지막 frame 번호입니다. 이 값도 GIF에 포함됩니다.
- `--step`: frame 간격입니다.
- `-o`, `--output`: 저장할 GIF 파일 경로입니다. 기본값은 `animation.gif`입니다.
- `--fps`: 초당 프레임 수입니다. 값이 클수록 GIF가 빠르게 재생됩니다. 기본값은 `10`입니다.
- `--loop`: GIF 반복 횟수입니다. `0`이면 무한 반복입니다. 기본값은 `0`입니다.
- `-p`, `--pattern`: 기존 glob 패턴 방식입니다. 예: `slice_top_*.png`

## Notes

`--template`, `--start`, `--end`, `--step`을 사용하면 지정한 frame 번호 순서대로 파일을 읽습니다. 예를 들어 `--start 2000 --end 2800 --step 10`은 `2000, 2010, 2020, ..., 2800` 순서로 GIF를 만듭니다.

`--pattern` 방식을 사용할 수도 있습니다. 이 경우 `png_to_gif.py`는 파일명 안의 숫자를 기준으로 자연 정렬합니다. 예를 들어 `slice_top_2010.png`가 `slice_top_2000.png` 뒤에 오도록 정렬됩니다.

Top view와 front view를 섞지 않으려면 반드시 `slice_top_*.png` 또는 `slice_front_*.png`처럼 패턴을 지정해서 실행하는 것이 좋습니다.

