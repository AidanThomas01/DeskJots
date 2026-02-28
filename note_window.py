"""
note_window.py - DeskJots individual sticky note window

Uses a proper WM-managed window (no overrideredirect) so KWin/X11
correctly hands keyboard focus on click. The native title bar is hidden
via wm_attributes and we draw our own toolbar inside the window instead.
"""

import tkinter as tk
import deskjots_db as db

# ── Palette ────────────────────────────────────────────────────────────────
NOTE_BG       = "#1e1e1e"
NOTE_BG_BAR   = "#161616"
NOTE_FG       = "#d0d0d0"
NOTE_FG_DIM   = "#444444"
NOTE_TITLE_FG = "#eeeeee"
CURSOR_COL    = "#f5c842"
SEL_BG        = "#2e2e2e"
DIVIDER       = "#2c2c2c"

COLOURS = {
    "Amber":    "#f5c842",
    "Teal":     "#3dd6c8",
    "Blue":     "#4a9eff",
    "Rose":     "#ff6b8a",
    "Green":    "#5ecf6e",
    "Lavender": "#a78bfa",
    "Slate":    "#94a3b8",
}
DEFAULT_COLOUR = "#f5c842"

MIN_FONT = 8
MAX_FONT = 28
BORDER_W = 4


class NoteWindow(tk.Toplevel):
    def __init__(self, master, note_id, on_close_callback):
        super().__init__(master)
        self.note_id           = note_id
        self.on_close_callback = on_close_callback
        self._drag_x = self._drag_y = 0

        note = db.get_note(note_id)
        if not note:
            self.destroy()
            return

        self._colour    = note["colour"] if note["colour"] in COLOURS.values() \
                          else DEFAULT_COLOUR
        self._font_size = note["font_size"]

        # ── Use a real WM window so KWin gives us keyboard focus ───────
        self.wm_attributes("-type", "utility")
        self.attributes("-topmost", True)
        self.resizable(True, True)
        self.minsize(220, 200)

        # Clamp to a sensible size in case old DB values are too large
        w = min(note["width"],  600)
        h = min(note["height"], 400)
        self.geometry(f"{w}x{h}+{note['pos_x']}+{note['pos_y']}")
        self.configure(bg=NOTE_BG)

        # Remove the native title bar text — our toolbar replaces it
        self.wm_title("")
        # Tell KWin to strip decorations while staying a managed window
        try:
            self.wm_attributes("-toolwindow", True)  # no-op on Linux but harmless
        except tk.TclError:
            pass

        self._build_ui(note)
        self._apply_border_colour(self._colour)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Configure>", self._on_configure)

    # ------------------------------------------------------------------ UI

    def _build_ui(self, note):
        # ── Left colour stripe ─────────────────────────────────────────
        self.stripe = tk.Frame(self, width=BORDER_W, bg=self._colour)
        self.stripe.pack(side="left", fill="y")

        # ── Main content area ──────────────────────────────────────────
        content = tk.Frame(self, bg=NOTE_BG)
        content.pack(side="left", fill="both", expand=True)



        # ── Title inside the body ──────────────────────────────────────
        title_frame = tk.Frame(content, bg=NOTE_BG)
        title_frame.pack(fill="x", padx=10, pady=(10, 0))

        self.title_var = tk.StringVar(value=note["title"])
        self.title_entry = tk.Entry(
            title_frame,
            textvariable=self.title_var,
            bg=NOTE_BG, fg=NOTE_TITLE_FG,
            insertbackground=CURSOR_COL,
            relief="flat", bd=0,
            highlightthickness=0,
            font=("Sans", 11, "bold"),
        )
        self.title_entry.pack(fill="x")
        self.title_entry.bind("<FocusOut>",  self._save_title)
        self.title_entry.bind("<Return>",    self._title_confirm)
        self.title_entry.bind("<Control-a>", lambda e: (
            self.title_entry.select_range(0, "end"),
            self.title_entry.icursor("end"),
            "break"
        ))

        # Thin divider between title and body
        tk.Frame(content, bg=DIVIDER, height=1).pack(fill="x", padx=10, pady=(8, 0))

        # ── Bottom bar: colour, font size, resize grip ─────────────────
        # Must be packed BEFORE text_frame so expand=True doesn't swallow it
        bottom_bar = tk.Frame(content, bg=NOTE_BG_BAR, height=28)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        btn = dict(
            bg=NOTE_BG_BAR,
            activebackground=NOTE_BG_BAR,
            relief="flat", bd=0,
            highlightthickness=0,
            font=("Sans", 9),
            cursor="hand2",
            padx=5, pady=0,
        )

        grip = tk.Label(
            bottom_bar, text="⠿",
            bg=NOTE_BG_BAR, fg=NOTE_FG_DIM,
            font=("Sans", 7), cursor="sizing",
        )
        grip.pack(side="right", padx=4)
        grip.bind("<ButtonPress-1>", self._resize_start)
        grip.bind("<B1-Motion>",     self._resize_motion)

        tk.Button(bottom_bar, text="A+",
                  fg=NOTE_FG_DIM, activeforeground=NOTE_FG,
                  command=self._font_up, **btn).pack(side="right")

        tk.Button(bottom_bar, text="A-",
                  fg=NOTE_FG_DIM, activeforeground=NOTE_FG,
                  command=self._font_down, **btn).pack(side="right")

        self.colour_btn = tk.Menubutton(
            bottom_bar, text="◈",
            bg=NOTE_BG_BAR, fg=self._colour,
            activebackground=NOTE_BG_BAR,
            relief="flat", bd=0,
            highlightthickness=0,
            font=("Sans", 11), cursor="hand2", padx=5,
        )
        self.colour_btn.pack(side="left", padx=2)

        colour_menu = tk.Menu(
            self.colour_btn, tearoff=0,
            bg="#1a1a1a", fg=NOTE_FG,
            activebackground="#2a2a2a", activeforeground=NOTE_FG,
            bd=0, relief="flat",
        )
        self.colour_btn["menu"] = colour_menu
        for name, hex_val in COLOURS.items():
            colour_menu.add_command(
                label=f"  {name}",
                foreground=hex_val,
                activeforeground=hex_val,
                command=lambda h=hex_val: self._apply_border_colour(h),
            )

        # ── Note body ──────────────────────────────────────────────────
        text_frame = tk.Frame(content, bg=NOTE_BG)
        text_frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            text_frame,
            wrap="word",
            relief="flat", bd=0,
            highlightthickness=0,
            bg=NOTE_BG, fg=NOTE_FG,
            insertbackground=CURSOR_COL,
            selectbackground=SEL_BG,
            selectforeground=NOTE_FG,
            undo=True,
            font=("Sans", self._font_size),
            padx=10, pady=8,
            spacing1=2, spacing3=2,
        )
        self.text.insert("1.0", note["content"])
        self.text.pack(fill="both", expand=True, side="left")
        self.text.bind("<KeyRelease>", self._save_content)
        self.text.bind("<Control-a>", lambda e: (
            self.text.tag_add("sel", "1.0", "end"),
            self.text.mark_set("insert", "end"),
            "break"
        ))

        sb = tk.Scrollbar(
            text_frame, command=self.text.yview,
            bg=NOTE_BG, troughcolor=NOTE_BG,
            activebackground="#333", width=6,
            relief="flat", bd=0,
        )
        sb.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=sb.set)

        # Focus the text body when the note first opens
        self.after(50, self.text.focus_set)

    # ---------------------------------------------------------------- drag

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _drag_motion(self, event):
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    # -------------------------------------------------------------- resize

    def _resize_start(self, event):
        self._drag_x  = event.x_root
        self._drag_y  = event.y_root
        self._start_w = self.winfo_width()
        self._start_h = self.winfo_height()

    def _resize_motion(self, event):
        w = max(200, self._start_w + event.x_root - self._drag_x)
        h = max(150, self._start_h + event.y_root - self._drag_y)
        self.geometry(f"{w}x{h}")

    # ------------------------------------------------------------ colour

    def _apply_border_colour(self, hex_colour):
        self._colour = hex_colour
        self.stripe.configure(bg=hex_colour)
        self.colour_btn.configure(fg=hex_colour)
        db.update_note(self.note_id, colour=hex_colour)

    # --------------------------------------------------------- font size

    def _font_up(self):
        if self._font_size < MAX_FONT:
            self._font_size += 1
            self.text.configure(font=("Sans", self._font_size))
            db.update_note(self.note_id, font_size=self._font_size)

    def _font_down(self):
        if self._font_size > MIN_FONT:
            self._font_size -= 1
            self.text.configure(font=("Sans", self._font_size))
            db.update_note(self.note_id, font_size=self._font_size)

    # -------------------------------------------------------------- save

    def _save_content(self, _=None):
        db.update_note(self.note_id, content=self.text.get("1.0", "end-1c"))

    def _save_title(self, _=None):
        db.update_note(self.note_id, title=self.title_var.get() or "Untitled")

    def _title_confirm(self, _=None):
        self._save_title()
        self.text.focus_set()
        self.text.mark_set("insert", "1.0")

    def _on_configure(self, _=None):
        if hasattr(self, "_geo_after"):
            self.after_cancel(self._geo_after)
        self._geo_after = self.after(500, self._save_geometry)

    def _save_geometry(self):
        db.update_note(
            self.note_id,
            pos_x=self.winfo_x(),    pos_y=self.winfo_y(),
            width=self.winfo_width(), height=self.winfo_height(),
        )

    def _on_close(self):
        self._save_content()
        self._save_title()
        self._save_geometry()
        self.on_close_callback(self.note_id)
        self.destroy()
