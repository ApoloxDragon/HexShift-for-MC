from gradient_text import ColorStop, per_letter_gradient_frames, frames_to_yaml

text = "play.minenetwork.com"
colors = [
    ColorStop.from_hex(0.0, "#3B28CC"),
    ColorStop.from_hex(0.5, "#3E7FF5"),
    ColorStop.from_hex(1.0, "#71AAF6"),
]
frames = per_letter_gradient_frames(text, colors, num_frames=2, shift_mode="wrap")
y = frames_to_yaml(frames, change_interval_ms=200, root_key="web", list_key="texts")
print(y)

