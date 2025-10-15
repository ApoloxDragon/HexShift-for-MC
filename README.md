# HexShift For Minecraft

Minecraft per-letter shifting gradient generator with GUI, presets, and CLI.

What this provides
- A core generator that colors each character with a hex color and shifts the gradient smoothly per frame.
- A Tkinter GUI to configure: text, number of lines/frames, color stops (with a color picker), positions, shift mode, interval, YAML keys.
- Supports 1–10 gradients at once (tabs). Each tab is a gradient; frames cycle through tabs.
- Local presets: Save, Load, and Delete your configurations (stored on disk).
- A CLI for quick generation from the terminal.

Quick start (Windows)
1) GUI (recommended)
   - Run:
     
     ```bat
     python -m gradient_text.app
     ```
   - Configure:
     - Text: e.g. play.minenetwork.com
     - Lines (frames): how many lines to output in YAML
     - Change interval (ms): your animation interval
     - Shift mode: wrap (loop) or pingpong (forward/back)
     - Shift per frame (optional): leave empty for auto (≈ 1/len(text))
     - Gradient tabs (1–10): Click “Add Gradient Tab” to create more gradients. Each tab has its own color stops. Frames cycle through tabs.
     - Gradient stops: Add/Edit/Remove colors; use Distribute positions to spread evenly.
   - Presets:
     - Save as… to save your current setup (text, keys, frames, stops in all tabs).
     - Load to apply a saved preset.
     - Delete to remove a preset.
     - Presets are stored locally at:
       - Windows: %APPDATA%\gradient_text\presets.json
       - Other OS: ~/.gradient_text/presets.json
   - Click Generate YAML, then Copy or Save.

2) CLI
   - Single gradient example (quotes are important around the colors in Windows shells):
     
     ```bat
     python gradient_text_cli.py --text play.minenetwork.com --colors "#3B28CC" "#3E7FF5" "#63A2F8" "#71AAF6" --frames 48 --interval 200 --mode wrap --out out.yml
     ```
   - Multiple gradients from CLI (frames cycle across gradients in order):
     
     ```bat
     python gradient_text_cli.py --text play.minenetwork.com ^
       --colors-set "#3B28CC" "#3E7FF5" "#63A2F8" "#71AAF6" ^
       --colors-set "#FF7A7A" "#FFD37A" "#7AFFB2" ^
       --frames 48 --interval 200 --out out.yml
     ```
   - Using a saved preset (created via the GUI):
     
     ```bat
     python gradient_text_cli.py --preset "My Ocean Blue" --out out.yml
     ```
   - Options:
     - --positions 0 0.5 1 ... to pin stops; otherwise they are distributed evenly (applies to --colors only).
     - --root-key web --list-key texts to change the YAML keys.
     - --shift-per-frame 0.05 to override the amount of gradient movement per frame.

About the output
- Each character is prefixed with the hex color in the format &#RRGGBB, e.g. '&#3B28CCp'.
- The YAML structure:
  
  ```yaml
  web:
    change-interval: 200
    texts:
    - '&#3B28CCp&#3C37D3l...'
    - '...'
  ```

Advanced notes
- Gradient stops are blended linearly in RGB across the text width.
- The gradient phase advances per frame to create the shifting effect.
- Shift mode wrap loops around; pingpong moves forward then back.
- With multiple gradient tabs or --colors-set, frame f uses gradient (f mod number_of_gradients).

Related tools
- Birdflop RGB tool (great for experimenting with colors and gradients): https://www.birdflop.com/resources/rgb/

Troubleshooting
- If you see no output in some consoles, redirect to a file and open it with a text editor:
  
  ```bat
  python gradient_text_cli.py --text play.minenetwork.com --colors "#3B28CC" "#3E7FF5" --frames 5 --out out.yml
  type out.yml
  ```
- Tkinter GUI requires a desktop session (won't work in a headless console).

License

This project is licensed under the GNU AGPL-3.0-or-later.

- Full text: see the LICENSE file in this repository.
- Summary: You may use, modify, and share this software under the AGPL-3.0 terms. If you modify it and make it available for others to use over a network, you must provide the Corresponding Source to those users as required by AGPL §13.
- Contributions are accepted under the same license.

Notice
- This project was coded with ChatGPT.
