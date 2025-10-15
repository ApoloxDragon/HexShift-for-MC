from __future__ import annotations

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from .gradient import (
    ColorStop,
    per_letter_gradient_frames_multi,
    frames_to_yaml,
)
from . import gradient as gradient_core
from . import presets as presets_mgr


@dataclass
class StopRow:
    position_var: tk.StringVar
    color_var: tk.StringVar


class GradientTextApp(ttk.Frame):
    MAX_GRADIENTS = 10

    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.master.title("HexShift – Minecraft Per-Letter Gradient Generator")
        self.master.geometry("1100x780")
        self.pack(fill=tk.BOTH, expand=True)

        # State
        self.text_var = tk.StringVar(value="play.minenetwork.com")
        self.frames_var = tk.IntVar(value=48)
        self.interval_var = tk.IntVar(value=200)
        self.shift_mode_var = tk.StringVar(value="wrap")
        self.shift_per_frame_var = tk.StringVar(value="")  # empty means auto
        self.root_key_var = tk.StringVar(value="web")
        self.list_key_var = tk.StringVar(value="texts")

        self.preview_frame_index = tk.IntVar(value=0)

        # Gradients notebook with multiple Treeviews
        self.notebook: ttk.Notebook
        self.gradients_trees: List[ttk.Treeview] = []

        # Presets
        self.preset_combo_var = tk.StringVar()

        self._build_ui()
        self._add_default_tabs()
        self._update_preview()

    # UI construction
    def _build_ui(self):
        # Top controls
        controls = ttk.LabelFrame(self, text="Configuration")
        controls.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        # Text row
        ttk.Label(controls, text="Text:").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        text_entry = ttk.Entry(controls, textvariable=self.text_var, width=60)
        text_entry.grid(row=0, column=1, columnspan=6, sticky="we", padx=4, pady=4)

        # Frames and interval
        ttk.Label(controls, text="Lines (frames):").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        ttk.Spinbox(controls, from_=1, to=5000, textvariable=self.frames_var, width=8).grid(row=1, column=1, sticky="w", padx=4, pady=4)

        ttk.Label(controls, text="Change interval (ms):").grid(row=1, column=2, sticky="w", padx=4, pady=4)
        ttk.Spinbox(controls, from_=10, to=60000, increment=10, textvariable=self.interval_var, width=10).grid(row=1, column=3, sticky="w", padx=4, pady=4)

        ttk.Label(controls, text="Shift mode:").grid(row=1, column=4, sticky="w", padx=4, pady=4)
        mode_cb = ttk.Combobox(controls, values=["wrap", "pingpong"], textvariable=self.shift_mode_var, state="readonly", width=10)
        mode_cb.grid(row=1, column=5, sticky="w", padx=4, pady=4)

        ttk.Label(controls, text="Shift per frame (0..1, empty=auto):").grid(row=1, column=6, sticky="w", padx=4, pady=4)
        ttk.Entry(controls, textvariable=self.shift_per_frame_var, width=12).grid(row=1, column=7, sticky="w", padx=4, pady=4)

        # YAML keys
        ttk.Label(controls, text="Root key:").grid(row=2, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(controls, textvariable=self.root_key_var, width=12).grid(row=2, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(controls, text="List key:").grid(row=2, column=2, sticky="w", padx=4, pady=4)
        ttk.Entry(controls, textvariable=self.list_key_var, width=12).grid(row=2, column=3, sticky="w", padx=4, pady=4)

        # Presets row
        presets_row = ttk.LabelFrame(self, text="Presets")
        presets_row.pack(side=tk.TOP, fill=tk.X, padx=8, pady=4)
        ttk.Label(presets_row, text="Preset:").grid(row=0, column=0, padx=4, pady=4)
        self.preset_combo = ttk.Combobox(presets_row, textvariable=self.preset_combo_var, values=presets_mgr.list_preset_names(), width=40, state="readonly")
        self.preset_combo.grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(presets_row, text="Load", command=self._on_load_preset).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(presets_row, text="Save as...", command=self._on_save_preset).grid(row=0, column=3, padx=4, pady=4)
        ttk.Button(presets_row, text="Delete", command=self._on_delete_preset).grid(row=0, column=4, padx=4, pady=4)
        ttk.Button(presets_row, text="Refresh", command=self._refresh_preset_list).grid(row=0, column=5, padx=4, pady=4)

        # Gradients editor (multi)
        gradients_frame = ttk.LabelFrame(self, text="Gradients (1-10). Each tab is a gradient; frames will cycle through tabs.")
        gradients_frame.pack(side=tk.TOP, fill=tk.BOTH, padx=8, pady=8, expand=True)

        self.notebook = ttk.Notebook(gradients_frame)
        self.notebook.grid(row=0, column=0, columnspan=1, sticky="nsew")
        gradients_frame.rowconfigure(0, weight=1)
        gradients_frame.columnconfigure(0, weight=1)

        tab_btns = ttk.Frame(gradients_frame)
        tab_btns.grid(row=1, column=0, sticky="w")
        ttk.Button(tab_btns, text="Add Gradient Tab", command=self._on_add_gradient_tab).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(tab_btns, text="Remove Current Tab", command=self._on_remove_current_gradient_tab).grid(row=0, column=1, padx=4, pady=4)

        # Preview
        preview = ttk.LabelFrame(self, text="Preview (single frame)")
        preview.pack(side=tk.TOP, fill=tk.BOTH, padx=8, pady=8, expand=True)

        # Text preview using a Text widget with per-char tags
        self.preview_text = tk.Text(preview, height=3, wrap=tk.NONE)
        self.preview_text.pack(fill=tk.X, padx=8, pady=4)
        self.preview_text.configure(state=tk.DISABLED)

        # Frame slider
        slider_row = ttk.Frame(preview)
        slider_row.pack(fill=tk.X, padx=8, pady=4)
        ttk.Label(slider_row, text="Frame:").pack(side=tk.LEFT)
        self.frame_slider = ttk.Scale(slider_row, from_=0, to=1, orient=tk.HORIZONTAL, command=self._on_slider)
        self.frame_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        self.frame_label = ttk.Label(slider_row, text="0/0")
        self.frame_label.pack(side=tk.LEFT)

        # YAML output box
        yaml_box = ttk.LabelFrame(self, text="YAML output")
        yaml_box.pack(side=tk.TOP, fill=tk.BOTH, padx=8, pady=8, expand=True)
        self.yaml_text = tk.Text(yaml_box, height=10, wrap=tk.NONE)
        self.yaml_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        out_btns = ttk.Frame(self)
        out_btns.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
        ttk.Button(out_btns, text="Generate YAML", command=self._on_generate_yaml).pack(side=tk.LEFT, padx=4)
        ttk.Button(out_btns, text="Copy YAML", command=self._on_copy_yaml).pack(side=tk.LEFT, padx=4)
        ttk.Button(out_btns, text="Save YAML...", command=self._on_save_yaml).pack(side=tk.LEFT, padx=4)

        # Bind changes to update preview
        for var in [self.text_var, self.shift_mode_var, self.shift_per_frame_var, self.root_key_var, self.list_key_var]:
            var.trace_add("write", self._trace_update_preview)
        for var in [self.frames_var, self.interval_var]:
            var.trace_add("write", self._trace_update_frame_slider)
        self._update_frame_slider()

        # Update preview when tab changes
        self.notebook.bind("<<NotebookTabChanged>>", lambda _e: self._update_preview())

    def _trace_update_preview(self, *_args):
        self._update_preview()
        return ""

    def _trace_update_frame_slider(self, *_args):
        self._update_frame_slider()
        return ""

    def _add_default_tabs(self):
        # Create one default gradient tab
        self._create_gradient_tab(name="Gradient 1")
        # Add a pleasing default stops set
        defaults = [
            (0.00, "#3B28CC"),
            (0.33, "#3E7FF5"),
            (0.66, "#63A2F8"),
            (1.00, "#71AAF6"),
        ]
        tree = self.gradients_trees[0]
        for pos, hexc in defaults:
            self._tree_insert_stop(tree, pos, hexc)

    # Gradient tab management
    def _create_gradient_tab(self, name: str):
        if len(self.gradients_trees) >= self.MAX_GRADIENTS:
            messagebox.showwarning("Limit", f"Maximum {self.MAX_GRADIENTS} gradients allowed.")
            return
        frame = ttk.Frame(self.notebook)
        # Tree
        tree = ttk.Treeview(frame, columns=("position", "color"), show="headings", height=6)
        tree.heading("position", text="Position (0..1)")
        tree.heading("color", text="Hex Color (#RRGGBB)")
        tree.column("position", width=120, anchor="center")
        tree.column("color", width=150, anchor="center")
        tree.grid(row=0, column=0, columnspan=6, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        # Buttons
        btns = ttk.Frame(frame)
        btns.grid(row=1, column=0, sticky="w")
        ttk.Button(btns, text="Add Stop", command=lambda tr=tree: self._on_add_stop(tr)).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(btns, text="Edit Stop", command=lambda tr=tree: self._on_edit_stop(tr)).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(btns, text="Remove Stop", command=lambda tr=tree: self._on_remove_stop(tr)).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(btns, text="Move Up", command=lambda tr=tree: self._move_selected(tr, -1)).grid(row=0, column=3, padx=4, pady=4)
        ttk.Button(btns, text="Move Down", command=lambda tr=tree: self._move_selected(tr, 1)).grid(row=0, column=4, padx=4, pady=4)
        ttk.Button(btns, text="Distribute positions", command=lambda tr=tree: self._distribute_positions(tr)).grid(row=0, column=5, padx=4, pady=4)

        self.notebook.add(frame, text=name)
        self.gradients_trees.append(tree)
        self.notebook.select(frame)

    def _on_add_gradient_tab(self):
        idx = len(self.gradients_trees) + 1
        self._create_gradient_tab(name=f"Gradient {idx}")
        self._update_preview()

    def _on_remove_current_gradient_tab(self):
        if len(self.gradients_trees) <= 1:
            messagebox.showinfo("Gradients", "At least one gradient is required.")
            return
        current = self.notebook.index(self.notebook.select())
        self.notebook.forget(current)
        del self.gradients_trees[current]
        self._update_preview()

    # Stop manipulation helpers for a given tree
    def _tree_insert_stop(self, tree: ttk.Treeview, position: float, hex_color: str, index: Optional[int] = None):
        tree.insert("", index if index is not None else tk.END, values=(f"{position:.4f}", hex_color.upper()))

    def _selected_item(self, tree: ttk.Treeview) -> Optional[str]:
        sel = tree.selection()
        return sel[0] if sel else None

    def _on_add_stop(self, tree: ttk.Treeview):
        pos = self._ask_position(0.5)
        if pos is None:
            return
        color = colorchooser.askcolor(title="Choose color")[1]
        if not color:
            return
        assert isinstance(color, str)
        self._tree_insert_stop(tree, float(pos), color)
        self._update_preview()

    def _on_edit_stop(self, tree: ttk.Treeview):
        item = self._selected_item(tree)
        if not item:
            messagebox.showinfo("Edit stop", "Select a stop to edit.")
            return
        pos_str, color_hex = tree.item(item, "values")
        pos = self._ask_position(float(pos_str))
        if pos is None:
            return
        color = colorchooser.askcolor(color=color_hex, title="Choose color")[1]
        if not color:
            return
        assert isinstance(color, str)
        tree.item(item, values=(f"{float(pos):.4f}", color.upper()))
        self._update_preview()

    def _on_remove_stop(self, tree: ttk.Treeview):
        item = self._selected_item(tree)
        if not item:
            return
        tree.delete(item)
        self._update_preview()

    def _move_selected(self, tree: ttk.Treeview, delta: int):
        item = self._selected_item(tree)
        if not item:
            return
        parent = tree.parent(item)
        index = tree.index(item)
        new_index = max(0, index + delta)
        tree.move(item, parent, new_index)
        self._update_preview()

    def _distribute_positions(self, tree: ttk.Treeview):
        items = tree.get_children()
        n = len(items)
        if n == 0:
            return
        for i, item in enumerate(items):
            pos = 0.0 if n == 1 else i / (n - 1)
            vals = list(tree.item(item, "values"))
            vals[0] = f"{pos:.4f}"
            tree.item(item, values=tuple(vals))
        self._update_preview()

    def _ask_position(self, default: float) -> Optional[float]:
        dlg = tk.Toplevel(self)
        dlg.title("Set position (0..1)")
        dlg.grab_set()
        var = tk.StringVar(value=f"{default:.4f}")
        ttk.Label(dlg, text="Position (0..1):").pack(padx=8, pady=8)
        e = ttk.Entry(dlg, textvariable=var)
        e.pack(padx=8, pady=4)
        e.focus_set()

        result: List[Optional[float]] = [None]

        def ok():
            try:
                v = float(var.get())
                if not (0.0 <= v <= 1.0):
                    raise ValueError
            except Exception:
                messagebox.showerror("Invalid", "Enter a number between 0 and 1.")
                return
            result[0] = v
            dlg.destroy()

        def cancel():
            dlg.destroy()

        btns = ttk.Frame(dlg)
        btns.pack(padx=8, pady=8)
        ttk.Button(btns, text="OK", command=ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=4)
        dlg.wait_window()
        return result[0]

    # Building gradient model
    def _collect_stops_from_tree(self, tree: ttk.Treeview) -> List[ColorStop]:
        items = tree.get_children()
        pairs = []
        for item in items:
            pos_str, color_hex = tree.item(item, "values")
            try:
                pos = float(pos_str)
            except Exception:
                pos = 0.0
            pairs.append((max(0.0, min(1.0, pos)), color_hex))
        pairs.sort(key=lambda p: p[0])
        return [ColorStop.from_hex(p, c) for p, c in pairs]

    def _collect_all_gradients(self) -> List[List[ColorStop]]:
        gradients: List[List[ColorStop]] = []
        for tree in self.gradients_trees:
            gradients.append(self._collect_stops_from_tree(tree))
        return gradients

    def _get_shift_per_frame(self) -> Optional[float]:
        s = self.shift_per_frame_var.get().strip()
        if not s:
            return None
        try:
            v = float(s)
        except Exception:
            return None
        return v

    # Presets
    def _refresh_preset_list(self):
        names = presets_mgr.list_preset_names()
        self.preset_combo.configure(values=names)

    def _on_save_preset(self):
        # Ask name
        name = self._ask_text("Save preset", "Preset name:")
        if not name:
            return
        preset = self._build_preset_dict()
        try:
            presets_mgr.put_preset(name, preset)
            self._refresh_preset_list()
            self.preset_combo_var.set(name)
            messagebox.showinfo("Preset", f"Saved preset '{name}'.")
        except Exception as e:
            messagebox.showerror("Preset", f"Failed to save preset: {e}")

    def _on_load_preset(self):
        name = self.preset_combo_var.get().strip()
        if not name:
            messagebox.showinfo("Preset", "Select a preset to load.")
            return
        data = presets_mgr.get_preset(name)
        if not data:
            messagebox.showerror("Preset", f"Preset '{name}' not found.")
            return
        try:
            self._apply_preset_dict(data)
            messagebox.showinfo("Preset", f"Loaded preset '{name}'.")
        except Exception as e:
            messagebox.showerror("Preset", f"Failed to load preset: {e}")

    def _on_delete_preset(self):
        name = self.preset_combo_var.get().strip()
        if not name:
            return
        if not messagebox.askyesno("Delete preset", f"Delete preset '{name}'?"):
            return
        try:
            presets_mgr.delete_preset(name)
            self._refresh_preset_list()
            self.preset_combo_var.set("")
        except Exception as e:
            messagebox.showerror("Preset", f"Failed to delete: {e}")

    def _ask_text(self, title: str, prompt: str) -> Optional[str]:
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.grab_set()
        var = tk.StringVar()
        ttk.Label(dlg, text=prompt).pack(padx=8, pady=8)
        e = ttk.Entry(dlg, textvariable=var, width=40)
        e.pack(padx=8, pady=4)
        e.focus_set()
        result: List[Optional[str]] = [None]

        def ok():
            v = var.get().strip()
            if not v:
                messagebox.showerror("Invalid", "Name cannot be empty.")
                return
            result[0] = v
            dlg.destroy()

        def cancel():
            dlg.destroy()

        btns = ttk.Frame(dlg)
        btns.pack(padx=8, pady=8)
        ttk.Button(btns, text="OK", command=ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=4)
        dlg.wait_window()
        return result[0]

    def _build_preset_dict(self) -> Dict[str, Any]:
        gradients = []
        for stops in self._collect_all_gradients():
            gradients.append([
                {"position": s.position, "color": f"#{gradient_core.rgb_to_hex(s.color)}"}
                for s in gradient_core.normalize_stops(stops)
            ])
        return {
            "text": self.text_var.get(),
            "frames": int(self.frames_var.get()),
            "interval": int(self.interval_var.get()),
            "shift_mode": self.shift_mode_var.get(),
            "shift_per_frame": float(self.shift_per_frame_var.get()) if self.shift_per_frame_var.get().strip() else None,
            "root_key": self.root_key_var.get(),
            "list_key": self.list_key_var.get(),
            "gradients": gradients,
        }

    def _apply_preset_dict(self, data: Dict[str, Any]) -> None:
        # Scalars
        self.text_var.set(data.get("text", self.text_var.get()))
        self.frames_var.set(int(data.get("frames", self.frames_var.get())))
        self.interval_var.set(int(data.get("interval", self.interval_var.get())))
        self.shift_mode_var.set(data.get("shift_mode", self.shift_mode_var.get()))
        spf = data.get("shift_per_frame", None)
        self.shift_per_frame_var.set("" if spf is None else str(spf))
        self.root_key_var.set(data.get("root_key", self.root_key_var.get()))
        self.list_key_var.set(data.get("list_key", self.list_key_var.get()))
        # Gradients
        grads = data.get("gradients", [])[: self.MAX_GRADIENTS]
        # Clear notebook
        for i in reversed(range(len(self.gradients_trees))):
            self.notebook.forget(i)
        self.gradients_trees.clear()
        if not grads:
            self._add_default_tabs()
        else:
            for idx, g in enumerate(grads):
                self._create_gradient_tab(name=f"Gradient {idx+1}")
                tree = self.gradients_trees[-1]
                # Clear existing rows just in case
                for item in tree.get_children():
                    tree.delete(item)
                # Add rows
                for stop in g:
                    pos = float(stop.get("position", 0.0))
                    color = str(stop.get("color", "#FFFFFF"))
                    self._tree_insert_stop(tree, pos, color)
        self._update_frame_slider()
        self._update_preview()

    # Preview
    def _on_slider(self, _evt=None):
        self.preview_frame_index.set(int(round(self.frame_slider.get())))
        self._update_preview()

    def _update_frame_slider(self):
        total = max(1, self.frames_var.get())
        self.frame_slider.configure(from_=0, to=total - 1)
        cur = min(self.preview_frame_index.get(), total - 1)
        self.preview_frame_index.set(cur)
        self.frame_slider.set(cur)
        self.frame_label.configure(text=f"{cur+1}/{total}")
        self._update_preview()

    def _update_preview(self):
        try:
            text = self.text_var.get()
            gradients = self._collect_all_gradients()
            if not gradients:
                gradients = [[]]
            frames = per_letter_gradient_frames_multi(
                text=text,
                stops_list=gradients,
                num_frames=max(1, self.frames_var.get()),
                shift_mode=self.shift_mode_var.get(),
                shift_per_frame=self._get_shift_per_frame(),
            )
            idx = min(self.preview_frame_index.get(), len(frames) - 1)
            frame = frames[idx]
            # Render colored text
            self.preview_text.configure(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            # Parse '&#RRGGBB<char>' segments and create tags
            i = 0
            out_chars = []
            colors = []
            while i < len(frame):
                if frame[i:i+2] == "&#":
                    hexcode = frame[i+2:i+8]
                    ch = frame[i+8:i+9]
                    if len(hexcode) == 6 and len(ch) == 1:
                        out_chars.append(ch)
                        colors.append(f"#{hexcode}")
                        i += 9
                        continue
                # Fallback, shouldn't happen
                out_chars.append(frame[i])
                colors.append("#FFFFFF")
                i += 1
            self.preview_text.insert("1.0", "".join(out_chars))
            # Apply tags
            for idx2, color in enumerate(colors):
                tag = f"c{idx2}"
                self.preview_text.tag_add(tag, f"1.{idx2}", f"1.{idx2+1}")
                self.preview_text.tag_config(tag, foreground=color)
            self.preview_text.configure(state=tk.DISABLED)
        except Exception as e:
            # Non-fatal
            self.preview_text.configure(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", f"Preview error: {e}")
            self.preview_text.configure(state=tk.DISABLED)

    # YAML generation handlers
    def _on_generate_yaml(self):
        text = self.text_var.get()
        if not text:
            messagebox.showerror("Error", "Text cannot be empty")
            return
        try:
            gradients = self._collect_all_gradients()
            frames = per_letter_gradient_frames_multi(
                text=text,
                stops_list=gradients,
                num_frames=max(1, self.frames_var.get()),
                shift_mode=self.shift_mode_var.get(),
                shift_per_frame=self._get_shift_per_frame(),
            )
            y = frames_to_yaml(
                frames,
                change_interval_ms=max(1, self.interval_var.get()),
                root_key=self.root_key_var.get() or "web",
                list_key=self.list_key_var.get() or "texts",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate: {e}")
            return
        self.yaml_text.delete("1.0", tk.END)
        self.yaml_text.insert("1.0", y)

    def _on_copy_yaml(self):
        data = self.yaml_text.get("1.0", tk.END)
        if not data.strip():
            self._on_generate_yaml()
            data = self.yaml_text.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(data)
        self.update()
        messagebox.showinfo("Copied", "YAML copied to clipboard.")

    def _on_save_yaml(self):
        data = self.yaml_text.get("1.0", tk.END)
        if not data.strip():
            self._on_generate_yaml()
            data = self.yaml_text.get("1.0", tk.END)
        path = filedialog.asksaveasfilename(defaultextension=".yml", filetypes=[("YAML", "*.yml;*.yaml"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
            messagebox.showinfo("Saved", f"Saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")


def main():
    root = tk.Tk()
    # Use ttk theme
    try:
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    app = GradientTextApp(root)
    app.mainloop()


if __name__ == "__main__":
    main()
