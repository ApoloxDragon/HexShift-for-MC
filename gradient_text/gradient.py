from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class ColorStop:
    position: float  # 0..1
    color: Tuple[int, int, int]  # (r,g,b) 0..255

    @staticmethod
    def from_hex(position: float, hex_color: str) -> "ColorStop":
        return ColorStop(position=position, color=hex_to_rgb(hex_color))


def clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    s = h.strip().lstrip('#')
    if len(s) not in (3, 6):
        raise ValueError(f"Invalid hex color: {h}")
    if len(s) == 3:
        s = ''.join(ch * 2 for ch in s)
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    return r, g, b


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"{r:02X}{g:02X}{b:02X}"


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_rgb(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    return (
        int(round(_lerp(a[0], b[0], t))),
        int(round(_lerp(a[1], b[1], t))),
        int(round(_lerp(a[2], b[2], t))),
    )


def normalize_stops(stops: List[ColorStop]) -> List[ColorStop]:
    if not stops:
        # fallback to white
        return [ColorStop(0.0, (255, 255, 255)), ColorStop(1.0, (255, 255, 255))]
    # Clamp and sort
    clamped = [ColorStop(clamp01(s.position), s.color) for s in stops]
    clamped.sort(key=lambda s: s.position)
    # Ensure 0 and 1 exist by padding
    if clamped[0].position > 0.0:
        clamped.insert(0, ColorStop(0.0, clamped[0].color))
    if clamped[-1].position < 1.0:
        clamped.append(ColorStop(1.0, clamped[-1].color))
    return clamped


def sample_gradient(stops: List[ColorStop], t: float, wrap: bool = True) -> Tuple[int, int, int]:
    """
    Sample a color from gradient defined by ordered stops at normalized position t.
    If wrap is True, t wraps around (mod 1).
    """
    if wrap:
        t = t % 1.0
    else:
        t = clamp01(t)
    s = normalize_stops(stops)
    # Find segment
    for i in range(1, len(s)):
        if t <= s[i].position:
            left = s[i - 1]
            right = s[i]
            span = max(1e-8, right.position - left.position)
            local_t = (t - left.position) / span
            return _lerp_rgb(left.color, right.color, local_t)
    return s[-1].color


def per_letter_gradient_frames(
    text: str,
    stops: List[ColorStop],
    num_frames: int,
    shift_mode: str = "wrap",  # 'wrap' or 'pingpong'
    shift_per_frame: float | None = None,
) -> List[str]:
    """
    Generate per-letter shifting gradient frames for the given text.

    Returns a list of strings where each character is prefixed with '&#RRGGBB'.
    """
    if num_frames <= 0:
        raise ValueError("num_frames must be > 0")
    n = len(text)
    if n == 0:
        return [""] * num_frames

    # Default shift: one character step over n frames.
    if shift_per_frame is None:
        shift_per_frame = 1.0 / n

    # Precompute positions for letters (0..1 across text)
    # Use (i / max(1, n-1)) to span endpoints; this gives nice edge colors.
    denom = max(1, n - 1)

    frames: List[str] = []

    def phase_for_frame(f: int) -> float:
        if shift_mode == "wrap":
            return f * shift_per_frame
        elif shift_mode == "pingpong":
            # Go 0->1 and back 1->0 over num_frames-1 steps
            cycle = (num_frames - 1) * 2 if num_frames > 1 else 1
            k = f % cycle
            up = k if k <= (num_frames - 1) else cycle - k
            return (up / max(1, num_frames - 1))
        else:
            raise ValueError("shift_mode must be 'wrap' or 'pingpong'")

    for f in range(num_frames):
        phase = phase_for_frame(f)
        parts: List[str] = []
        for i, ch in enumerate(text):
            t = (i / denom) + phase
            rgb = sample_gradient(stops, t, wrap=True)
            parts.append(f"&#{rgb_to_hex(rgb)}{ch}")
        frames.append("".join(parts))
    return frames


def per_letter_gradient_frames_multi(
    text: str,
    stops_list: List[List[ColorStop]],
    num_frames: int,
    shift_mode: str = "wrap",
    shift_per_frame: float | None = None,
) -> List[str]:
    """
    Like per_letter_gradient_frames but allows 1..N gradients. For each frame f,
    choose stops_list[f % len(stops_list)] and render. This lets you pick 1-10 gradients
    and cycle through them across frames.
    """
    if not stops_list:
        raise ValueError("stops_list must contain at least one gradient")
    n = len(text)
    if n == 0:
        return [""] * max(1, num_frames)
    if num_frames <= 0:
        raise ValueError("num_frames must be > 0")

    # Default shift: one character step over n frames.
    if shift_per_frame is None:
        shift_per_frame = 1.0 / n

    denom = max(1, n - 1)

    def phase_for_frame(f: int) -> float:
        if shift_mode == "wrap":
            return f * shift_per_frame
        elif shift_mode == "pingpong":
            cycle = (num_frames - 1) * 2 if num_frames > 1 else 1
            k = f % cycle
            up = k if k <= (num_frames - 1) else cycle - k
            return (up / max(1, num_frames - 1))
        else:
            raise ValueError("shift_mode must be 'wrap' or 'pingpong'")

    frames: List[str] = []
    m = len(stops_list)
    for f in range(num_frames):
        phase = phase_for_frame(f)
        stops = stops_list[f % m]
        parts: List[str] = []
        for i, ch in enumerate(text):
            t = (i / denom) + phase
            rgb = sample_gradient(stops, t, wrap=True)
            parts.append(f"&#{rgb_to_hex(rgb)}{ch}")
        frames.append("".join(parts))
    return frames


def frames_to_yaml(
    frames: List[str],
    change_interval_ms: int = 200,
    root_key: str = "web",
    list_key: str = "texts",
) -> str:
    """Format frames as a YAML snippet matching the user's example."""
    # Simple YAML emitter to avoid external deps. We'll quote each string with single quotes
    # and escape single quotes by doubling (not typically present here), preserve &'#'.
    lines = [f"{root_key}:", f"  change-interval: {int(change_interval_ms)}", f"  {list_key}:"]
    for s in frames:
        y = s.replace("'", "''")
        lines.append(f"  - '{y}'")
    return "\n".join(lines) + "\n"


__all__ = [
    "ColorStop",
    "hex_to_rgb",
    "rgb_to_hex",
    "normalize_stops",
    "sample_gradient",
    "per_letter_gradient_frames",
    "per_letter_gradient_frames_multi",
    "frames_to_yaml",
]
