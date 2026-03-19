# DeskJots

> Minimal dark-themed sticky notes for KDE Linux desktops.

![Status](https://img.shields.io/badge/status-alpha-orange) ![Platform](https://img.shields.io/badge/platform-Fedora%20%2F%20KDE-blue) ![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

DeskJots lives in the corner of your workflow — a lightweight note manager that keeps your thoughts visible without getting in the way. Notes float above your other windows, remember where you left them, and stay out of your way until you need them.

Built with Python and Tkinter. No Electron. No cloud. Just notes.

---

## Features

- Dark UI that fits naturally into a KDE desktop
- Floating, always-on-top sticky note windows
- Tile-based note list with title, preview and timestamp
- 7 accent colours per note shown as a left border stripe
- Per-note font size control
- Notes persist between sessions via a local SQLite database
- Window position and size saved per note

---

## Installation

Download the latest binary from the [Releases](../../releases) page and run it:

```bash
./deskjots
```

No Python required.

---

## Running from Source

Requires Python 3.8+ with Tkinter. On Fedora:

```bash
sudo dnf install python3-tkinter
git clone https://github.com/AidanThomas01/Deskjots.git
cd Deskjots
python main.py
```

---

## Usage

| Action | How |
|---|---|
| New note | Click **+** in the main window |
| Open note | Click anywhere on a tile |
| Edit title | Click the bold title on the note |
| Move to body | Press **Enter** in the title field |
| Change colour | Click **◈** in the note's bottom bar |
| Resize font | Click **A−** / **A+** in the note's bottom bar |
| Close note | KDE title bar close button |
| Delete note | Click **✕** on the tile |

---

## Add to KDE Launcher

Create `~/.local/share/applications/deskjots.desktop`:

```ini
[Desktop Entry]
Name=DeskJots
Comment=Minimal sticky notes
Exec=/path/to/deskjots
Icon=accessories-text-editor
Terminal=false
Type=Application
Categories=Utility;
```

To launch on login, copy the same file to `~/.config/autostart/`.

---

## Building

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name deskjots main.py
# Output: dist/deskjots
```

---

## Notes

- Tested on Fedora with KDE Plasma on X11
- Wayland is untested
- Alpha software — bugs are expected. Please open an [issue](../../issues) if you find one.

---

## License

MIT
