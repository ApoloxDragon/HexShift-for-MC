from __future__ import annotations

import argparse
import sys
from typing import List

from gradient_text import (
    ColorStop,
    per_letter_gradient_frames,
    per_letter_gradient_frames_multi,
    frames_to_yaml,
)
from gradient_text import presets as presets_mgr


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate per-letter shifting gradient YAML for Minecraft text.")

    # Two modes: preset mode or manual mode
    g = p.add_mutually_exclusive_group()
    g.add_argument("--preset", help="Name of a saved preset (created in the GUI)")
    g.add_argument("--colors", nargs="+", help="Hex color stops like #3B28CC #3E7FF5 ... left->right (single gradient)")

    # Multi-gradient via CLI: repeatable sets
    p.add_argument("--colors-set", nargs="+", action="append", help="Provide a gradient as a list of hex colors; repeat this flag up to 10 times for multiple gradients")

    # Shared/common options
    p.add_argument("--positions", nargs="*", type=float, help="Optional positions (0..1) for --colors only. If omitted, distributed evenly.")
    p.add_argument("--text", help="Text to color, e.g. play.example.com")
    p.add_argument("--frames", type=int, default=48, help="Number of frames/lines to output")
    p.add_argument("--interval", type=int, default=200, help="change-interval in ms")
    p.add_argument("--mode", choices=["wrap", "pingpong"], default="wrap", help="Shift mode")
    p.add_argument("--shift-per-frame", type=float, default=None, help="Optional shift per frame in 0..1; default 1/len(text)")
    p.add_argument("--root-key", default="web", help="YAML root key")
    p.add_argument("--list-key", default="texts", help="YAML list key")
    p.add_argument("--out", default="-", help="Output file path or '-' for stdout")
    return p.parse_args(argv)


def _build_stops_from_colors(colors: List[str], positions: List[float] | None = None) -> List[ColorStop]:
    pos = positions or []
    if pos and len(pos) != len(colors):
        raise ValueError("--positions must have same length as --colors")
    if not pos:
        if len(colors) == 1:
            pos = [0.0]
        else:
            pos = [i / (len(colors) - 1) for i in range(len(colors))]
    return [ColorStop.from_hex(p, c) for p, c in zip(pos, colors)]


def main(argv: List[str] | None = None) -> int:
    ns = parse_args(argv or sys.argv[1:])

    if ns.preset:
        data = presets_mgr.get_preset(ns.preset)
        if not data:
            print(f"Error: preset '{ns.preset}' not found", file=sys.stderr)
            return 2
        text = data.get("text")
        if not text:
            print("Error: preset missing text", file=sys.stderr)
            return 2
        frames = int(data.get("frames", ns.frames))
        interval = int(data.get("interval", ns.interval))
        mode = data.get("shift_mode", ns.mode)
        spf = data.get("shift_per_frame", ns.shift_per_frame)
        root_key = data.get("root_key", ns.root_key)
        list_key = data.get("list_key", ns.list_key)
        grads_data = data.get("gradients", [])
        if not grads_data:
            print("Error: preset has no gradients", file=sys.stderr)
            return 2
        stops_list = []
        for g in grads_data[:10]:
            stops = []
            for stop in g:
                positions = float(stop.get("position", 0.0))
                color = str(stop.get("color"))
                stops.append(ColorStop.from_hex(positions, color))
            stops_list.append(stops)
        frames_out = per_letter_gradient_frames_multi(
            text=text,
            stops_list=stops_list,
            num_frames=max(1, frames),
            shift_mode=mode,
            shift_per_frame=spf,
        )
        y = frames_to_yaml(
            frames_out,
            change_interval_ms=max(1, interval),
            root_key=root_key,
            list_key=list_key,
        )
    else:
        # Manual mode
        text = ns.text
        if not text:
            print("Error: --text is required (or use --preset)", file=sys.stderr)
            return 2
        stops_list: List[List[ColorStop]] = []
        if ns.colors:
            stops_list.append(_build_stops_from_colors(ns.colors, ns.positions))
        if ns.colors_set:
            for color_set in ns.colors_set:
                stops_list.append(_build_stops_from_colors(color_set, None))
        if not stops_list:
            print("Error: provide --colors or --colors-set (or use --preset)", file=sys.stderr)
            return 2
        frames_out = per_letter_gradient_frames_multi(
            text=text,
            stops_list=stops_list,
            num_frames=max(1, ns.frames),
            shift_mode=ns.mode,
            shift_per_frame=ns.shift_per_frame,
        )
        y = frames_to_yaml(
            frames_out,
            change_interval_ms=max(1, ns.interval),
            root_key=ns.root_key,
            list_key=ns.list_key,
        )

    if ns.out == "-":
        sys.stdout.write(y)
    else:
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write(y)
        print(f"Wrote {len(y.splitlines())} lines to {ns.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
