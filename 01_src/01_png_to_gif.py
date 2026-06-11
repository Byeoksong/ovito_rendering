#!/usr/bin/env python3
"""Combine PNG images into an animated GIF."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image


def natural_key(path: Path) -> list[int | str]:
    """Sort filenames naturally, so frame_20.png comes before frame_100.png."""
    parts = re.split(r"(\d+)", path.name)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Combine PNG files into an animated GIF."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        default="99_TEST",
        help="Directory containing PNG files. Default: 99_TEST",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        default="*.png",
        help=(
            'PNG filename pattern, e.g. "slice_top_*.png". '
            "Ignored when --template, --start, --end, and --step are used. "
            "Default: *.png"
        ),
    )
    parser.add_argument(
        "-t",
        "--template",
        help=(
            'Frame filename template, e.g. "slice_top_{frame}.png". '
            "Use with --start, --end, and --step."
        ),
    )
    parser.add_argument(
        "--start",
        type=int,
        help="First frame number for template mode.",
    )
    parser.add_argument(
        "--end",
        type=int,
        help="Last frame number for template mode. This value is included.",
    )
    parser.add_argument(
        "--step",
        type=int,
        help="Frame interval for template mode.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="animation.gif",
        help="Output GIF filename. Default: animation.gif",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=10.0,
        help="Frames per second. Default: 10",
    )
    parser.add_argument(
        "--loop",
        type=int,
        default=0,
        help="GIF loop count. 0 means infinite loop. Default: 0",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    use_template = any(
        value is not None for value in (args.template, args.start, args.end, args.step)
    )

    if use_template:
        if None in (args.template, args.start, args.end, args.step):
            raise SystemExit(
                "Template mode requires --template, --start, --end, and --step."
            )
        if "{frame}" not in args.template:
            raise SystemExit('Template must contain "{frame}", e.g. slice_top_{frame}.png')
        if args.step <= 0:
            raise SystemExit("--step must be greater than 0.")
        if args.start > args.end:
            raise SystemExit("--start must be less than or equal to --end.")

        png_files = [
            input_dir / args.template.format(frame=frame)
            for frame in range(args.start, args.end + 1, args.step)
        ]
        missing_files = [path for path in png_files if not path.exists()]

        if missing_files:
            preview = "\n".join(str(path) for path in missing_files[:10])
            extra = "" if len(missing_files) <= 10 else f"\n... and {len(missing_files) - 10} more"
            raise SystemExit(f"Missing PNG files:\n{preview}{extra}")
    else:
        png_files = sorted(input_dir.glob(args.pattern), key=natural_key)

    if not png_files:
        raise SystemExit(f"No PNG files found: {input_dir / args.pattern}")

    duration_ms = int(1000 / args.fps)
    frames = []

    for png_file in png_files:
        with Image.open(png_file) as image:
            frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=args.loop,
        optimize=False,
    )

    print(f"Saved {output_path} with {len(frames)} frames.")


if __name__ == "__main__":
    main()
