"""
main.py - DeskJots main window
Minimal dark UI with muted amber accent.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import deskjots_db as db
from note_window import NoteWindow

APP_NAME = "DeskJots"

# ── Palette ────────────────────────────────────────────────────────────────
BG         = "#1a1a1a"
BG_PANEL   = "#111111"
FG         = "#d0d0d0"
FG_DIM     = "#555555"
ACCENT     = "#f5c842"
BTN_BG     = "#252525"
SEL_BG     = "#2a2a2a"
BORDER     = "#2e2e2e"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        db.init_db()

        self.title(APP_NAME)
        self.geometry("400x520")
        self.minsize(320, 360)
        self.configure(bg=BG)

        self._open_notes: dict[int, NoteWindow] = {}

        self._style()
        self._build_ui()
        self._refresh_list()

    # ---------------------------------------------------------------- style

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("Treeview",
                    background=BG,
                    fieldbackground=BG,
                    foreground=FG,
                    rowheight=42,
                    borderwidth=0,
                    font=("Sans", 10))
        s.configure("Treeview.Heading",
                    background=BG_PANEL,
                    foreground=FG_DIM,
                    font=("Sans", 8),
                    borderwidth=0,
                    relief="flat")
        s.map("Treeview",
              background=[("selected", SEL_BG)],
              foreground=[("selected", ACCENT)])
        s.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        s.configure("Vertical.TScrollbar",
                    background=BG,
                    troughcolor=BG,
                    borderwidth=0,
                    arrowsize=0)
        s.map("Vertical.TScrollbar",
              background=[("active", BORDER)])

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
        ).pack(side="left", padx=16, pady=0)

        tk.Button(
            topbar, text="+",
            bg=BG_PANEL, fg=ACCENT,
            activebackground=BG_PANEL, activeforeground="#fff",
            relief="flat", bd=0,
            font=("Sans", 22, "bold"),
            cursor="hand2",
            command=self._new_note,
        ).pack(side="right", padx=16)

        # thin separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Note list ──────────────────────────────────────────────────
        list_frame = tk.Frame(self, bg=BG)
        list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            list_frame,
            columns=("indicator", "title", "updated"),
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("indicator", text="")
        self.tree.heading("title",     text="TITLE")
        self.tree.heading("updated",   text="MODIFIED")
        self.tree.column("indicator", width=6,   stretch=False, anchor="center")
        self.tree.column("title",     width=240, stretch=True,  anchor="w")
        self.tree.column("updated",   width=120, stretch=False, anchor="e")

        sb = ttk.Scrollbar(list_frame, orient="vertical",
                           command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._open_selected)
        self.tree.bind("<Return>",   self._open_selected)
        self.tree.bind("<Delete>",   self._delete_selected)

        # ── Bottom bar ─────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        bottombar = tk.Frame(self, bg=BG_PANEL, height=34)
        bottombar.pack(fill="x", side="bottom")
        bottombar.pack_propagate(False)

        self.status_var = tk.StringVar()
        tk.Label(
            bottombar, textvariable=self.status_var,
            bg=BG_PANEL, fg=FG_DIM,
            font=("Sans", 8),
        ).pack(side="left", padx=12, pady=0)

        tk.Button(
            bottombar, text="delete",
            bg=BG_PANEL, fg=FG_DIM,
            activebackground=BG_PANEL, activeforeground="#c0392b",
            relief="flat", bd=0,
            font=("Sans", 8),
            cursor="hand2",
            command=self._delete_selected,
        ).pack(side="right", padx=12)

    # ----------------------------------------------------------- list logic

    def _refresh_list(self):
        notes = db.get_all_notes()
        self.tree.delete(*self.tree.get_children())
        self._row_ids = {}

        for note in notes:
            updated = note["updated_at"][:16].replace("T", "  ")
            title   = note["title"] or "Untitled"
            iid = self.tree.insert("", "end",
                                   values=("", title, updated))
            # colour the left indicator stripe via tag
            tag = f"dot_{note['id']}"
            self.tree.tag_configure(tag, foreground=note["colour"])
            self.tree.item(iid, tags=(tag,))
            self._row_ids[iid] = note["id"]

        n = len(notes)
        self.status_var.set(f"{n} note{'s' if n != 1 else ''}")

    def _selected_note_id(self):
        sel = self.tree.selection()
        return self._row_ids.get(sel[0]) if sel else None

    # ---------------------------------------------------------- note actions

    def _new_note(self):
        note_id = db.create_note()
        self._open_note_window(note_id)
        self._refresh_list()

    def _open_selected(self, _event=None):
        note_id = self._selected_note_id()
        if note_id is not None:
            self._open_note_window(note_id)

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

    def _delete_selected(self, _event=None):
        note_id = self._selected_note_id()
        if note_id is None:
            return
        note  = db.get_note(note_id)
        title = note["title"] if note else "this note"
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
