import argparse
import os
import tempfile
import numpy as np

import warnings
warnings.filterwarnings('ignore', message='.*OVITO.*PyPI')

from ovito.io import import_file
from ovito.modifiers import ReplicateModifier
from ovito.vis import Viewport, TachyonRenderer

# Element -> color. Use either "#RRGGBB", RGB 0~255, or RGB 0~1.
ELEMENT_COLOR_MAP = {
    "Li": "#2680E3",
    "N":  "#858585",
}

DEFAULT_COLOR = "#B3B3B3"

# Element -> atomic radius used for rendering
ELEMENT_RADIUS_MAP = {
    "Li": 0.4,
    "N":  0.2,
}

# Element -> transparency used for rendering. 0.0 is opaque, 1.0 is invisible.
ELEMENT_TRANSPARENCY_MAP = {
    "Li": 0.0,
    "N":  0.0,
}

DEFAULT_TRANSPARENCY = 0.0

# Tachyon rendering style. Toggle these values in code as needed.
RENDER_AMBIENT_OCCLUSION = True           # Adds contact shading between nearby/overlapping atoms to emphasize depth.
RENDER_AMBIENT_OCCLUSION_BRIGHTNESS = 0.8 # Controls ambient occlusion brightness; lower values make shaded regions darker.
RENDER_AMBIENT_OCCLUSION_SAMPLES = 20     # Number of ambient occlusion samples; higher values reduce noise but render slower.
RENDER_SHADOWS = True                     # Enables cast shadows from direct lighting; may be less useful with transparent backgrounds.
RENDER_ANTIALIASING = True                # Smooths jagged pixel edges around atoms.
RENDER_ANTIALIASING_SAMPLES = 20          # Number of antialiasing samples; higher values smooth edges more but render slower.
RENDER_DIRECT_LIGHT = True                # Enables directional lighting, making spheres look more three-dimensional.
RENDER_DIRECT_LIGHT_INTENSITY = 1.0       # Strength of direct lighting; higher values increase highlights and contrast.


def normalize_color(color):
    if isinstance(color, str):
        hex_color = color.strip()
        if hex_color.startswith("#"):
            hex_color = hex_color[1:]
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color: {color}")
        try:
            return tuple(int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        except ValueError as exc:
            raise ValueError(f"Invalid hex color: {color}") from exc

    if len(color) != 3:
        raise ValueError(f"RGB color must have 3 components: {color}")

    rgb = tuple(float(component) for component in color)
    if any(component < 0 for component in rgb):
        raise ValueError(f"RGB color values must be non-negative: {color}")

    if any(component > 1 for component in rgb):
        if any(component > 255 for component in rgb):
            raise ValueError(f"RGB 0~255 color values cannot exceed 255: {color}")
        return tuple(component / 255.0 for component in rgb)

    return rgb


def validate_transparency(transparency):
    value = float(transparency)
    if value < 0.0 or value > 1.0:
        raise ValueError(f"Transparency must be between 0.0 and 1.0: {transparency}")
    return value


def validate_alpha(alpha):
    value = float(alpha)
    if value < 0.0 or value > 1.0:
        raise ValueError(f"Alpha must be between 0.0 and 1.0: {alpha}")
    return value


def import_structure_file(path: str):
    basename = os.path.basename(path)
    tempdir = None

    # OVITO recognizes XDATCAR trajectories by case-sensitive filename patterns.
    # A shifted copy named "xdatcar_shift" would otherwise be read as one POSCAR frame.
    if "xdatcar" in basename.lower() and not basename.startswith("XDATCAR"):
        tempdir = tempfile.TemporaryDirectory()
        aliased_path = os.path.join(tempdir.name, f"XDATCAR_{basename}")
        os.symlink(os.path.abspath(path), aliased_path)
        path = aliased_path

    return import_file(path), tempdir


def build_cell_visibility_modifier(show_cell: bool):
    def modify(frame, data):
        if data.cell is not None:
            data.cell_.vis.enabled = show_cell
            data.cell_.vis.render_cell = show_cell

    return modify


def build_z_range_filter(z_min: float | None, z_max: float | None, coordinate: str):
    def modify(frame, data):
        particles = data.particles
        if particles is None:
            raise RuntimeError("No particles found in the input file.")

        positions = np.asarray(particles.positions)

        if coordinate == "cartesian":
            z_values = positions[:, 2]
        elif coordinate == "direct":
            if data.cell is None:
                raise RuntimeError("Direct coordinate filtering requires a simulation cell.")

            positions_h = np.column_stack((positions, np.ones(particles.count)))
            reduced_positions = positions_h @ np.asarray(data.cell.inverse).T
            z_values = reduced_positions[:, 2]
        else:
            raise RuntimeError(f"Unknown z-coordinate mode: {coordinate}")

        keep = np.ones(particles.count, dtype=bool)
        if z_min is not None:
            keep &= z_values >= z_min
        if z_max is not None:
            keep &= z_values <= z_max

        delete_indices = np.nonzero(~keep)[0]
        if len(delete_indices) > 0:
            data.particles_.delete_indices(delete_indices)

    return modify


def build_modifier(atom_alpha: float | None = None):
    def modify(frame, data):
        particles = data.particles
        if particles is None:
            raise RuntimeError("No particles found in the input file.")

        if 'Particle Type' not in particles:
            raise RuntimeError("This dataset does not contain a 'Particle Type' property.")

        type_ids = np.asarray(particles['Particle Type'])
        n = particles.count

        # Map type id -> type name
        type_id_to_name = {}
        for t in data.particles_.particle_types_.types_:
            type_id_to_name[t.id] = t.name
            if t.name in ELEMENT_RADIUS_MAP:
                t.radius = ELEMENT_RADIUS_MAP[t.name]

        colors = np.empty((n, 3), dtype=float)
        transparencies = np.empty(n, dtype=float)
        alpha = validate_alpha(atom_alpha) if atom_alpha is not None else None

        for i in range(n):
            type_name = type_id_to_name.get(int(type_ids[i]), None)
            colors[i] = normalize_color(ELEMENT_COLOR_MAP.get(type_name, DEFAULT_COLOR))
            if alpha is None:
                transparencies[i] = validate_transparency(
                    ELEMENT_TRANSPARENCY_MAP.get(type_name, DEFAULT_TRANSPARENCY)
                )
            else:
                transparencies[i] = 1.0 - alpha

        # Overwrite/create visual properties
        data.particles_.create_property('Color', data=colors)
        data.particles_.create_property('Transparency', data=transparencies)

    return modify


def set_manual_view(vp: Viewport, center: tuple[float, float, float] | None, size: float | None):
    if center is not None:
        camera_dir = np.array(vp.camera_dir, dtype=float, copy=True)
        camera_dir_norm = np.linalg.norm(camera_dir)
        if camera_dir_norm == 0:
            raise RuntimeError("The viewport camera direction vector has zero length.")
        camera_dir /= camera_dir_norm

        old_camera_pos = np.array(vp.camera_pos, dtype=float, copy=True)
        center_pos = np.asarray(center, dtype=float)
        depth = np.dot(old_camera_pos - center_pos, camera_dir)
        vp.camera_pos = center_pos + depth * camera_dir

    if size is not None:
        vp.fov = size


def build_renderer():
    renderer = TachyonRenderer()
    renderer.ambient_occlusion = RENDER_AMBIENT_OCCLUSION
    renderer.ambient_occlusion_brightness = RENDER_AMBIENT_OCCLUSION_BRIGHTNESS
    renderer.ambient_occlusion_samples = RENDER_AMBIENT_OCCLUSION_SAMPLES
    renderer.shadows = RENDER_SHADOWS
    renderer.antialiasing = RENDER_ANTIALIASING
    renderer.antialiasing_samples = RENDER_ANTIALIASING_SAMPLES
    renderer.direct_light = RENDER_DIRECT_LIGHT
    renderer.direct_light_intensity = RENDER_DIRECT_LIGHT_INTENSITY
    return renderer


def main():
    parser = argparse.ArgumentParser(
        description="Render a structure colored by each atom's element type."
    )
    parser.add_argument("input", help="Input structure/trajectory file (xyz, POSCAR, XDATCAR, LAMMPS dump, etc.)")
    parser.add_argument("-o", "--output", default="element_colored.png", help="Output PNG filename")
    parser.add_argument("-f", "--frame", type=int, default=0, help="Frame index for trajectories")
    parser.add_argument("--width", type=int, default=1800, help="Image width in pixels")
    parser.add_argument("--height", type=int, default=1400, help="Image height in pixels")
    parser.add_argument("--camera", choices=["perspective", "ortho", "top", "front"], default="perspective")
    parser.add_argument(
        "--atom-alpha",
        type=float,
        default=None,
        help="Global atom opacity for this render. 0.0 is invisible, 1.0 is opaque. Overrides ELEMENT_TRANSPARENCY_MAP.",
    )
    parser.add_argument(
        "--transparent-background",
        dest="transparent_background",
        action="store_true",
        default=True,
        help="Render the PNG with a transparent background. This is the default.",
    )
    parser.add_argument(
        "--opaque-background",
        dest="transparent_background",
        action="store_false",
        help="Render the PNG with an opaque white background.",
    )
    parser.add_argument(
        "--view-center",
        type=float,
        nargs=3,
        metavar=("X", "Y", "Z"),
        default=None,
        help="Cartesian point at the center of the rendered view",
    )
    parser.add_argument(
        "--view-size",
        type=float,
        default=None,
        help="Orthographic view size in Cartesian units. Smaller values zoom in.",
    )
    parser.add_argument(
        "--repeat-a",
        type=int,
        nargs=3,
        metavar=("A1", "A2", "A3"),
        default=(1, 1, 1),
        help="Number of periodic repetitions along lattice vectors a1, a2, and a3",
    )
    parser.add_argument("--hide-cell", action="store_true", help="Hide the simulation cell/lattice box lines")
    parser.add_argument("--z-min", type=float, default=None, help="Minimum z value to keep")
    parser.add_argument("--z-max", type=float, default=None, help="Maximum z value to keep")
    parser.add_argument(
        "--z-coordinate",
        choices=["cartesian", "direct"],
        default="cartesian",
        help="Coordinate system for --z-min/--z-max. Use 'direct' for reduced cell coordinates.",
    )
    args = parser.parse_args()

    if args.z_min is not None and args.z_max is not None and args.z_min > args.z_max:
        parser.error("--z-min must be smaller than or equal to --z-max")
    if args.atom_alpha is not None and (args.atom_alpha < 0.0 or args.atom_alpha > 1.0):
        parser.error("--atom-alpha must be between 0.0 and 1.0")
    repeat_a1, repeat_a2, repeat_a3 = args.repeat_a
    if repeat_a1 < 1 or repeat_a2 < 1 or repeat_a3 < 1:
        parser.error("--repeat-a values must be positive integers")

    pipeline, input_tempdir = import_structure_file(args.input)
    if args.frame < 0 or args.frame >= pipeline.num_frames:
        parser.error(f"--frame must be between 0 and {pipeline.num_frames - 1}; input has {pipeline.num_frames} frame(s)")

    if repeat_a1 > 1 or repeat_a2 > 1 or repeat_a3 > 1:
        pipeline.modifiers.append(
            ReplicateModifier(
                num_x=repeat_a1,
                num_y=repeat_a2,
                num_z=repeat_a3,
                adjust_box=True,
            )
        )
    if args.z_min is not None or args.z_max is not None:
        pipeline.modifiers.append(build_z_range_filter(args.z_min, args.z_max, args.z_coordinate))
    pipeline.modifiers.append(build_modifier(atom_alpha=args.atom_alpha))
    if args.hide_cell:
        pipeline.modifiers.append(build_cell_visibility_modifier(show_cell=False))

    # Put pipeline into the scene so the viewport can render it
    pipeline.add_to_scene()

    vp = Viewport()
    if args.camera == "perspective":
        vp.type = Viewport.Type.Perspective
    elif args.camera == "ortho":
        vp.type = Viewport.Type.Ortho
    elif args.camera == "top":
        vp.type = Viewport.Type.Top
    elif args.camera == "front":
        vp.type = Viewport.Type.Front

    vp.zoom_all(size=(args.width, args.height))
    if args.view_center is not None or args.view_size is not None:
        if vp.is_perspective_projection:
            parser.error("--view-center and --view-size are intended for orthographic cameras: ortho, top, or front")
        set_manual_view(vp, args.view_center, args.view_size)

    vp.render_image(
        filename=args.output,
        size=(args.width, args.height),
        frame=args.frame,
        renderer=build_renderer(),
        background=(1, 1, 1),
        alpha=args.transparent_background,
    )

    print(f"Saved image to: {args.output}")
    if input_tempdir is not None:
        input_tempdir.cleanup()


if __name__ == "__main__":
    main()
