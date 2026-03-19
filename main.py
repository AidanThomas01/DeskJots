"""
main.py - DeskJots main window
Tile-based note list with per-tile delete button.
"""

import tkinter as tk
from tkinter import messagebox
import deskjots_db as db
from note_window import NoteWindow

APP_NAME = "DeskJots"

# ── Palette ────────────────────────────────────────────────────────────────
BG         = "#1a1a1a"
BG_PANEL   = "#111111"
BG_TILE    = "#222222"
BG_TILE_HO = "#292929"
FG         = "#d0d0d0"
FG_DIM     = "#9e9e9e"
FG_MUTED   = "#888888"
ACCENT     = "#f5c842"
BORDER     = "#2e2e2e"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        db.init_db()

        self.title(APP_NAME)
        self.geometry("400x540")
        self.minsize(320, 360)
        self.configure(bg=BG)

        self._open_notes: dict[int, NoteWindow] = {}
        self._tiles: list[tk.Frame] = []

        self._build_ui()
        self._refresh_list()

    # ------------------------------------------------------------------- UI

    def _build_ui(self):
        # ── Top bar ────────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=BG_PANEL, height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(
            topbar, text="DeskJots",
            bg=BG_PANEL, fg=ACCENT,
            font=("Sans", 14, "bold"),
        ).pack(side="left", padx=16)

        tk.Button(
            topbar, text="+",
            bg=BG_PANEL, fg=ACCENT,
            activebackground=BG_PANEL, activeforeground="#fff",
            relief="flat", bd=0,
            highlightthickness=0,
            font=("Sans", 22, "bold"),
            cursor="hand2",
            command=self._new_note,
        ).pack(side="right", padx=16)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Scrollable tile area ────────────────────────────────────────
        wrapper = tk.Frame(self, bg=BG)
        wrapper.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            wrapper, bg=BG,
            highlightthickness=0, bd=0,
        )
        sb = tk.Scrollbar(
            wrapper, orient="vertical",
            command=self.canvas.yview,
            bg=BG, troughcolor=BG,
            activebackground=BORDER,
            width=6, relief="flat", bd=0,
        )
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tile_frame = tk.Frame(self.canvas, bg=BG)
        self._canvas_window = self.canvas.create_window(
            (0, 0), window=self.tile_frame, anchor="nw"
        )

        self.tile_frame.bind("<Configure>", self._on_tile_frame_resize)
        self.canvas.bind("<Configure>",     self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>",    self._on_mousewheel)
        self.canvas.bind("<Button-4>",      self._on_mousewheel)
        self.canvas.bind("<Button-5>",      self._on_mousewheel)

        # ── Status bar ─────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        statusbar = tk.Frame(self, bg=BG_PANEL, height=30)
        statusbar.pack(fill="x", side="bottom")
        statusbar.pack_propagate(False)

        self.status_var = tk.StringVar()
        tk.Label(
            statusbar, textvariable=self.status_var,
            bg=BG_PANEL, fg=FG_DIM,
            font=("Sans", 8),
        ).pack(side="left", padx=12)

    # --------------------------------------------------------- tile builder

    def _refresh_list(self):
        for tile in self._tiles:
            tile.destroy()
        self._tiles.clear()

        notes = db.get_all_notes()
        for note in notes:
            self._build_tile(note)

        n = len(notes)
        self.status_var.set(f"{n} note{'s' if n != 1 else ''}")

    def _build_tile(self, note):
        note_id = note["id"]
        colour  = note["colour"]
        title   = note["title"] or "Untitled"
        preview = note["content"].replace("\n", " ").strip()
        preview = preview[:60] + "…" if len(preview) > 60 else preview
        updated = note["updated_at"][:16].replace("T", "  ")

        # ── Tile frame ─────────────────────────────────────────────────
        tile = tk.Frame(self.tile_frame, bg=BG_TILE, cursor="hand2")
        tile.pack(fill="x", padx=10, pady=(6, 0))
        self._tiles.append(tile)

        # Coloured left stripe
        stripe = tk.Frame(tile, width=4, bg=colour)
        stripe.pack(side="left", fill="y")

        # Main tile body
        body = tk.Frame(tile, bg=BG_TILE, padx=10, pady=8)
        body.pack(side="left", fill="both", expand=True)

        # Top row: title + ✕ button
        top_row = tk.Frame(body, bg=BG_TILE)
        top_row.pack(fill="x")

        tk.Label(
            top_row, text=title,
            bg=BG_TILE, fg=FG,
            font=("Sans", 10, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # ✕ delete button — command handles delete, binding stops propagation
        delete_btn = tk.Button(
            top_row, text="✕",
            bg=BG_TILE, fg=FG_DIM,
            activebackground=BG_TILE, activeforeground="#ff6b6b",
            relief="flat", bd=0,
            highlightthickness=0,
            font=("Sans", 9),
            cursor="hand2",
            command=lambda nid=note_id, t=title: self._delete_note(nid, t),
        )
        delete_btn.pack(side="right")

        # Preview text
        if preview:
            tk.Label(
                body, text=preview,
                bg=BG_TILE, fg=FG_MUTED,
                font=("Sans", 8),
                anchor="w", justify="left",
            ).pack(fill="x", pady=(2, 0))

        # Timestamp
        tk.Label(
            body, text=updated,
            bg=BG_TILE, fg=FG_DIM,
            font=("Sans", 7),
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        # ── Bind open + hover to everything except the delete button ───
        def _bind_tile(widget):
            if widget is delete_btn:
                return
            widget.bind("<Button-1>",
                        lambda e, nid=note_id: self._open_note_window(nid))
            widget.bind("<Enter>",
                        lambda e, t=tile: t.configure(bg=BG_TILE_HO))
            widget.bind("<Leave>",
                        lambda e, t=tile: t.configure(bg=BG_TILE))
            widget.bind("<MouseWheel>", self._on_mousewheel)
            widget.bind("<Button-4>",   self._on_mousewheel)
            widget.bind("<Button-5>",   self._on_mousewheel)
            for child in widget.winfo_children():
                _bind_tile(child)

        _bind_tile(tile)

    # -------------------------------------------------------- scroll helpers

    def _on_tile_frame_resize(self, _event):
        self.canvas.update_idletasks()
        content_height = self.tile_frame.winfo_reqheight()
        canvas_height  = self.canvas.winfo_height()
        if content_height > canvas_height:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        else:
            self.canvas.configure(scrollregion=(0, 0, 0, 0))

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ---------------------------------------------------------- note actions

    def _new_note(self):
        note_id = db.create_note()
        self._open_note_window(note_id)
        self._refresh_list()

    def _open_note_window(self, note_id):
        if note_id in self._open_notes:
            win = self._open_notes[note_id]
            win.lift()
            win.focus_force()
            return
        win = NoteWindow(self, note_id, on_close_callback=self._on_note_closed)
        self._open_notes[note_id] = win

    def _on_note_closed(self, note_id):
        self._open_notes.pop(note_id, None)
        self._refresh_list()

    def _delete_note(self, note_id, title):
        if not messagebox.askyesno(
            APP_NAME,
            f'Delete "{title}"?\nThis cannot be undone.',
            icon="warning",
        ):
            return
        if note_id in self._open_notes:
            self._open_notes[note_id].destroy()
            self._open_notes.pop(note_id)
        db.delete_note(note_id)
        self._refresh_list()


if __name__ == "__main__":
    app = App()
    app.mainloop()
