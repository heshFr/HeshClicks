# ============================================================
# 🦋 HeshClicks v1.0
#
# 👦 Kid-Friendly Guide (so easy even a 5-year-old can follow!)
#
# Step 1: Get the project
#   👉 Download the ZIP from GitHub and open it.
#
# Step 2: Install Python
#   👉 Go to python.org OR microsoft store, download Python, install it.
#   👉 Tick "Add Python to PATH" when installing.
#
# Step 3: Install helpers
#   👉 Open Command Prompt and type:
#       pip install -r requirements.txt
#
# Step 4: Run the app
#   👉 In Command Prompt, go to the folder and type:
#       python main.py
#
# Step 5: Play with it!
#   👉 Clickers tab: start left/right auto-clickers.
#   👉 Keyboard tab: type any text instantly.
#   👉 Macros tab: record and play back actions.
#   👉 About tab: see your logo and credits.
#   👉 Compact+ mode: shrink the app to quick actions.
#   👉 Themes: Coffee, Mint, Soda, Azure.
#   👉 Hotkeys: change them with a popup, see them at the bottom.
#
# 💡 Tips:
#   👉 If stuck, press "Stop All" or panic hotkey (Ctrl+Esc).
#   👉 Hotkeys save automatically.
#   👉 Add your logo in the assets/ folder to brand it.
#
# 👏 Credits:
#   Built with ❤️ by Hetesh.
# ============================================================
import tkinter as tk
from tkinter import ttk
import threading, time, json, os, webbrowser
import keyboard
import win32api, win32con

# Global state
running_left = False
running_right = False
cps_left, cps_right = 10, 10
text_to_type = "Namaste from HeshClicks!"
click_count = 0
key_count = 0

# Macro state
recording = False
macro_events = []
_last_event_time = None
playback_speed = 1.0

# Hotkeys + persistence
HOTKEY_FILE = "hotkeys.json"
hotkeys = {
    "left": "f6",
    "right": "f7",
    "type": "f8",
    "compact_mode": "ctrl+shift+c",
    "stop_all": "ctrl+esc",
    "record_macro": "ctrl+shift+m",
    "stop_macro": "ctrl+shift+s",
    "play_macro": "f9",
}
hotkey_handlers = {}

def load_hotkeys():
    global hotkeys
    if os.path.exists(HOTKEY_FILE):
        try:
            with open(HOTKEY_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for k, v in data.items():
                        if k in hotkeys and isinstance(v, str) and v.strip():
                            hotkeys[k] = v.strip().lower()
        except Exception:
            pass

def save_hotkeys():
    try:
        with open(HOTKEY_FILE, "w") as f:
            json.dump(hotkeys, f, indent=2)
    except Exception:
        pass

def do_left_click(stats_label=None):
    global click_count
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    click_count += 1
    if stats_label:
        stats_label.configure(text=f"Clicks: {click_count} | Keys: {key_count}")

def do_right_click(stats_label=None):
    global click_count
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
    click_count += 1
    if stats_label:
        stats_label.configure(text=f"Clicks: {click_count} | Keys: {key_count}")

def flash_label(lbl, on=True):
    target = "#1a8e2a" if on else "#b00020"
    original = lbl.cget("foreground")
    lbl.configure(foreground=target)
    lbl.after(220, lambda: lbl.configure(foreground=original))

# Workers and toggles
def worker_left(status, btn, stats_label):
    global running_left, cps_left
    while True:
        if running_left:
            do_left_click(stats_label)
            time.sleep(1 / max(1, cps_left))
        else:
            time.sleep(0.05)

def worker_right(status, btn, stats_label):
    global running_right, cps_right
    while True:
        if running_right:
            do_right_click(stats_label)
            time.sleep(1 / max(1, cps_right))
        else:
            time.sleep(0.05)

def toggle_left(status, btn):
    global running_left
    running_left = not running_left
    btn.configure(text="Stop Left" if running_left else "Start Left")
    status.configure(text=f"Left: {'ON' if running_left else 'OFF'} | CPS={cps_left}")
    flash_label(status, on=running_left)

def toggle_right(status, btn):
    global running_right
    running_right = not running_right
    btn.configure(text="Stop Right" if running_right else "Start Right")
    status.configure(text=f"Right: {'ON' if running_right else 'OFF'} | CPS={cps_right}")
    flash_label(status, on=running_right)

def set_cps_left(val, status):
    global cps_left
    try:
        cps_left = int(float(val))
    except Exception:
        cps_left = 10
    status.configure(text=f"Left: {'ON' if running_left else 'OFF'} | CPS={cps_left}")

def set_cps_right(val, status):
    global cps_right
    try:
        cps_right = int(float(val))
    except Exception:
        cps_right = 10
    status.configure(text=f"Right: {'ON' if running_right else 'OFF'} | CPS={cps_right}")

def type_text(kb_status, kb_entry, stats_label):
    global text_to_type, key_count
    text_to_type = kb_entry.get()
    if text_to_type.strip():
        keyboard.write(text_to_type)
        key_count += len(text_to_type)
        kb_status.configure(text=f"Typed: {text_to_type}")
        stats_label.configure(text=f"Clicks: {click_count} | Keys: {key_count}")
    else:
        kb_status.configure(text="Nothing to type")

def stop_all(left_status, left_btn, right_status, right_btn, macro_status=None):
    global running_left, running_right, recording
    running_left = False
    running_right = False
    recording = False
    left_btn.configure(text="Start Left")
    right_btn.configure(text="Start Right")
    left_status.configure(text=f"Left: OFF | CPS={cps_left}")
    right_status.configure(text=f"Right: OFF | CPS={cps_right}")
    if macro_status:
        macro_status.configure(text="Stopped all actions")

# Macro recorder
def start_recording(macro_status):
    global recording, macro_events, _last_event_time
    macro_events = []
    recording = True
    _last_event_time = time.time()
    macro_status.configure(text="Recording... Press Stop to end.")

def stop_recording(macro_status):
    global recording
    recording = False
    macro_status.configure(text=f"Stopped. {len(macro_events)} events captured.")

def record_key_event(event):
    global recording, _last_event_time
    if not recording:
        return
    now = time.time()
    delay = now - _last_event_time if _last_event_time else 0
    _last_event_time = now
    name = event.name
    macro_events.append(("key", name, None, delay))

keyboard.on_press(record_key_event)

def add_click_event(button_name):
    global recording, _last_event_time
    if not recording:
        return
    pos = win32api.GetCursorPos()
    now = time.time()
    delay = now - _last_event_time if _last_event_time else 0
    _last_event_time = now
    macro_events.append(("click", button_name, pos, delay))

def play_macro(macro_status):
    global playback_speed
    if not macro_events:
        macro_status.configure(text="No macro to play.")
        return
    macro_status.configure(text="Playing macro...")
    for etype, value, pos, delay in macro_events:
        time.sleep(max(0.0, delay) / max(0.1, playback_speed))
        if etype == "key":
            keyboard.write(value)
        elif etype == "click":
            if pos:
                win32api.SetCursorPos(pos)
            if value == "left":
                do_left_click()
            else:
                do_right_click()
    macro_status.configure(text="Macro playback finished.")
# --- Part 2: Hotkeys (professional capture), themes (presets + packs), compact mode ---

# Modal hotkey capture (professional UX)
def start_hotkey_capture(entry, action_key, rebind_cb, preview_cb, parent):
    # Disable entry while capturing
    entry.configure(state="disabled")

    # Modal popup
    modal = tk.Toplevel(parent)
    modal.title("Set hotkey")
    modal.geometry("360x140")
    modal.resizable(False, False)
    modal.transient(parent)
    modal.grab_set()

    msg = ttk.Label(modal, text=f"Listening for hotkey for: {action_key}\nPress any combination now...")
    msg.pack(pady=(12, 8))

    status = ttk.Label(modal, text="Waiting...", foreground="#cad2d7")
    status.pack()

    btns = ttk.Frame(modal); btns.pack(pady=10)
    def cancel():
        modal.destroy()
        entry.configure(state="normal")
    ttk.Button(btns, text="Cancel", command=cancel).pack()

    # Capture in background to keep UI alive
    def capture():
        try:
            combo = keyboard.read_hotkey(suppress=True)
        except Exception:
            combo = None
        if combo:
            hotkeys[action_key] = combo.lower()
            save_hotkeys()
            status.configure(text=f"Set to: {hotkeys[action_key]}")
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.insert(0, hotkeys[action_key])
            rebind_cb()
            preview_cb()
            modal.after(500, modal.destroy)
        else:
            status.configure(text="No hotkey captured")
            entry.configure(state="normal")
    threading.Thread(target=capture, daemon=True).start()

# Binding and preview
def bind_all_hotkeys(hk_preview_label,
                     left_status, left_btn, right_status, right_btn,
                     kb_status, kb_entry, stats_label,
                     toggle_compact_cb, stop_all_cb,
                     start_rec_cb, stop_rec_cb, play_cb):
    # Clean previous
    for k, h in list(hotkey_handlers.items()):
        try:
            keyboard.remove_hotkey(h)
        except Exception:
            pass
        hotkey_handlers.pop(k, None)

    # Bind fresh
    hotkey_handlers["left"] = keyboard.add_hotkey(hotkeys["left"], lambda: toggle_left(left_status, left_btn))
    hotkey_handlers["right"] = keyboard.add_hotkey(hotkeys["right"], lambda: toggle_right(right_status, right_btn))
    hotkey_handlers["type"] = keyboard.add_hotkey(hotkeys["type"], lambda: type_text(kb_status, kb_entry, stats_label))
    hotkey_handlers["compact_mode"] = keyboard.add_hotkey(hotkeys["compact_mode"], toggle_compact_cb)
    hotkey_handlers["stop_all"] = keyboard.add_hotkey(hotkeys["stop_all"], stop_all_cb)
    hotkey_handlers["record_macro"] = keyboard.add_hotkey(hotkeys["record_macro"], start_rec_cb)
    hotkey_handlers["stop_macro"] = keyboard.add_hotkey(hotkeys["stop_macro"], stop_rec_cb)
    hotkey_handlers["play_macro"] = keyboard.add_hotkey(hotkeys["play_macro"], play_cb)

    hk_preview_label.configure(
        text="Hotkeys — "
             f"Left: {hotkeys['left']} | Right: {hotkeys['right']} | Type: {hotkeys['type']} | "
             f"Record: {hotkeys['record_macro']} | Stop Rec: {hotkeys['stop_macro']} | Play: {hotkeys['play_macro']} | "
             f"Compact: {hotkeys['compact_mode']} | Stop: {hotkeys['stop_all']}"
    )

# Presets: only switch ttk base theme to avoid clashes
def apply_light_preset(style):
    try:
        style.theme_use("vista")
    except Exception:
        style.theme_use("default")

def apply_dark_preset(style):
    try:
        style.theme_use("alt")
    except Exception:
        style.theme_use("default")

# Theme packs: full color control
def style_all(style, bg, fg, accent=None):
    style.configure(".", background=bg, foreground=fg)
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TLabelframe", background=bg, foreground=fg)
    style.configure("TLabelframe.Label", background=bg, foreground=fg)
    style.configure("TNotebook", background=bg)
    style.configure("TNotebook.Tab", background=(accent or bg), foreground=fg)
    style.configure("TEntry", fieldbackground=bg, foreground=fg)
    style.configure("TCombobox", fieldbackground=bg, foreground=fg)
    style.configure("TSpinbox", fieldbackground=bg, foreground=fg)
    style.configure("TButton", background=(accent or bg), foreground=fg)
    style.configure("TScale", background=bg)
    style.configure("Horizontal.TScale", background=bg)

def apply_theme_pack(style, pack="Soda"):
    if pack == "Soda":      # refined slate
        style_all(style, bg="#5980bf", fg="#000000", accent="#FFFFFF")
    elif pack == "Azure":
        style_all(style, bg="#eef6ff", fg="#0b3b7e", accent="#cfe2ff")
    elif pack == "Carbon":  # now Coffee
        style_all(style, bg="#3b2f2f", fg="#FF9D00", accent="#000000")
    elif pack == "Mint":
        style_all(style, bg="#eafff5", fg="#115e59", accent="#c7f9e8")
    else:
        apply_light_preset(style)

compact_mode = False

def build_quick_actions(parent, kb_status, kb_entry, macro_status):
    row = ttk.Frame(parent)
    row.pack(fill="x", padx=12, pady=(6, 10))
    ttk.Label(row, text="Quick actions:").pack(side="left")
    ttk.Button(row, text="Type", command=lambda: type_text(kb_status, kb_entry, kb_status)).pack(side="left", padx=6)
    ttk.Button(row, text="Record", command=lambda: start_recording(macro_status)).pack(side="left", padx=6)
    ttk.Button(row, text="Stop Rec", command=lambda: stop_recording(macro_status)).pack(side="left", padx=6)
    ttk.Button(row, text="Play", command=lambda: threading.Thread(target=play_macro, args=(macro_status,), daemon=True).start()).pack(side="left", padx=6)
    return row

def set_compact_mode(root, notebook, tabs, footer, enable=True):
    global compact_mode
    compact_mode = enable
    clicker_tab, keyboard_tab, macro_tab, about_tab = tabs
    if enable:
        notebook.select(clicker_tab)
        notebook.hide(keyboard_tab); notebook.hide(macro_tab); notebook.hide(about_tab)
        root.geometry("720x520")
    else:
        notebook.add(keyboard_tab); notebook.add(macro_tab); notebook.add(about_tab)
        root.geometry("980x780")
    footer.pack_forget(); footer.pack(fill="x", padx=10, pady=(0, 8))

def build_gui():
    load_hotkeys()

    root = tk.Tk()
    root.title("HeshClicks ❤️ v1.0")
    root.geometry("840x640")
    root.resizable(False, False)
    style = ttk.Style()

    # Top bar: Presets + Theme packs + Stats
    topbar = ttk.Frame(root)
    topbar.pack(fill="x", padx=10, pady=(10, 0))
    butterfly_label = ttk.Label(topbar, text="🦋", font=("Segoe UI", 20))
    butterfly_label.pack(side="left", padx=(0, 6))


    ttk.Label(topbar, text="Preset:").pack(side="left", padx=(0, 6))
    preset_sel = ttk.Combobox(topbar, values=["Light", "Dark"], width=10, state="readonly")
    preset_sel.set("Light")
    def on_preset_change(event=None):
        if preset_sel.get() == "Light":
            apply_light_preset(style)
        else:
            apply_dark_preset(style)
        # After preset changes, reapply theme pack to keep colors consistent
        apply_theme_pack(style, theme_sel.get())
    preset_sel.bind("<<ComboboxSelected>>", on_preset_change)
    preset_sel.pack(side="left")

    ttk.Label(topbar, text="Theme:").pack(side="left", padx=(12, 6))
    theme_sel = ttk.Combobox(topbar, values=["Soda", "Azure", "tutu", "Mint"], width=10, state="readonly")
    theme_sel.set("tutu")
    def on_theme_pack(event=None):
        apply_theme_pack(style, theme_sel.get())
    theme_sel.bind("<<ComboboxSelected>>", on_theme_pack)
    theme_sel.pack(side="left")

    stats_label_top = ttk.Label(topbar, text=f"Clicks: {click_count} | Keys: {key_count}", foreground="#007acc")
    stats_label_top.pack(side="right")

    # Apply defaults at startup
    apply_light_preset(style)
    apply_theme_pack(style, theme_sel.get())

    # Notebook
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # Clickers tab
    clicker_tab = ttk.Frame(notebook)
    notebook.add(clicker_tab, text="Clickers")

    left_frame = ttk.LabelFrame(clicker_tab, text="Left Clicker")
    left_frame.pack(fill="x", padx=12, pady=(12, 6))
    left_status = ttk.Label(left_frame, text=f"Left: OFF | CPS={cps_left}")
    left_status.pack(anchor="w", padx=10, pady=(8, 4))
    left_slider = ttk.Scale(left_frame, from_=1, to=30, orient="horizontal",
                            command=lambda v: set_cps_left(v, left_status))
    left_slider.set(cps_left)
    left_slider.pack(fill="x", padx=10, pady=4)
    left_btn = ttk.Button(left_frame, text="Start Left",
                          command=lambda: toggle_left(left_status, left_btn))
    left_btn.pack(padx=10, pady=(6, 10))

    right_frame = ttk.LabelFrame(clicker_tab, text="Right Clicker")
    right_frame.pack(fill="x", padx=12, pady=(6, 12))
    right_status = ttk.Label(right_frame, text=f"Right: OFF | CPS={cps_right}")
    right_status.pack(anchor="w", padx=10, pady=(8, 4))
    right_slider = ttk.Scale(right_frame, from_=1, to=30, orient="horizontal",
                             command=lambda v: set_cps_right(v, right_status))
    right_slider.set(cps_right)
    right_slider.pack(fill="x", padx=10, pady=4)
    right_btn = ttk.Button(right_frame, text="Start Right",
                           command=lambda: toggle_right(right_status, right_btn))
    right_btn.pack(padx=10, pady=(6, 10))

    stats_label = ttk.Label(clicker_tab, text=f"Clicks: {click_count} | Keys: {key_count}", foreground="#007acc")
    stats_label.pack(pady=(0, 8))

    threading.Thread(target=worker_left, args=(left_status, left_btn, stats_label), daemon=True).start()
    threading.Thread(target=worker_right, args=(right_status, right_btn, stats_label), daemon=True).start()

    # Keyboard tab
    keyboard_tab = ttk.Frame(notebook)
    notebook.add(keyboard_tab, text="Keyboard")

    kb_frame = ttk.LabelFrame(keyboard_tab, text="Keyboard automation")
    kb_frame.pack(fill="x", padx=12, pady=12)
    kb_entry = ttk.Entry(kb_frame, width=56)
    kb_entry.insert(0, text_to_type)
    kb_entry.pack(padx=10, pady=(8, 4))
    kb_status = ttk.Label(kb_frame, text="Ready to type text")
    kb_status.pack(anchor="w", padx=10, pady=(4, 4))
    ttk.Button(kb_frame, text="Type Now",
               command=lambda: type_text(kb_status, kb_entry, stats_label)).pack(padx=10, pady=(6, 10))

    # Macros tab
    macro_tab = ttk.Frame(notebook)
    notebook.add(macro_tab, text="Macros")

    macro_frame = ttk.LabelFrame(macro_tab, text="Macro recorder")
    macro_frame.pack(fill="x", padx=12, pady=12)
    macro_status = ttk.Label(macro_frame, text="No macro recorded yet")
    macro_status.pack(anchor="w", padx=10, pady=(8, 4))

    btn_row = ttk.Frame(macro_frame)
    btn_row.pack(padx=10, pady=6)
    ttk.Button(btn_row, text="⏺ Record", command=lambda: start_recording(macro_status)).pack(side="left", padx=5)
    ttk.Button(btn_row, text="⏹ Stop", command=lambda: stop_recording(macro_status)).pack(side="left", padx=5)
    ttk.Button(btn_row, text="▶ Play", command=lambda: threading.Thread(target=play_macro, args=(macro_status,), daemon=True).start()).pack(side="left", padx=5)

    add_row = ttk.Frame(macro_frame)
    add_row.pack(padx=10, pady=6)
    ttk.Label(add_row, text="Add click:").pack(side="left")
    ttk.Button(add_row, text="Left", command=lambda: add_click_event("left")).pack(side="left", padx=5)
    ttk.Button(add_row, text="Right", command=lambda: add_click_event("right")).pack(side="left", padx=5)

    speed_row = ttk.Frame(macro_frame)
    speed_row.pack(fill="x", padx=10, pady=6)
    ttk.Label(speed_row, text="Playback speed:").pack(side="left")
    def set_playback_speed(v):
        global playback_speed
        try:
            playback_speed = float(v)
        except Exception:
            playback_speed = 1.0
    speed_scale = ttk.Scale(speed_row, from_=0.25, to=3.0, orient="horizontal", command=set_playback_speed)
    speed_scale.set(playback_speed)
    speed_scale.pack(side="left", padx=8)

    # About tab (centered and enlarged)
    about_tab = ttk.Frame(notebook)
    notebook.add(about_tab, text="About")

    about_container = ttk.Frame(about_tab)
    about_container.pack(expand=True, fill="both")
    about_panel = ttk.Frame(about_container)
    about_panel.place(relx=0.5, rely=0.5, anchor="center")

    ttk.Label(about_panel, text="HeshClicks", font=("Chiller", 50, "bold")).pack(pady=(10, 10))
    ttk.Label(about_panel, text="Version history:\n- v1.0: Clickers, typing, macros, hotkeys, Compact+, presets & theme packs\n- v2.0 (coming soon): full mouse recording, persistence expansions, logging",
              justify="left", font=("Microsoft Himalayan", 13)).pack(pady=6)
    ttk.Label(about_panel, text="Developed by Hetesh with ❤️", font=("Segoe UI", 10)).pack(pady=4)
    ttk.Label(about_panel, text="Acknowledgements: Microsoft Copilot, tkinter, keyboard, pywin32 (win32api/win32con)\n- Special thanks to my mentors, friends, and classmates who encouraged me to refine this project and make it public.”",
              justify="left", font=("Segoe UI", 10)).pack(pady=4)

    link_row = ttk.Frame(about_panel); link_row.pack(pady=10)
    def open_github(): webbrowser.open("https://github.com/yourusername/HeshClicks")  
    def open_linkedin(): webbrowser.open("https://www.linkedin.com/in/hetesh-vichare-5895a4219/")   
    ttk.Button(link_row, text="View on GitHub", command=open_github).pack(side="left", padx=6)
    ttk.Button(link_row, text="Connect on LinkedIn", command=open_linkedin).pack(side="left", padx=6)



    # Footer
    footer = ttk.Frame(root)
    footer.pack(fill="x", padx=10, pady=(0, 8))
    hk_preview = ttk.Label(footer, text="", foreground="#555"); hk_preview.pack(side="left")
    ttk.Button(footer, text="⏹ Stop All",
               command=lambda: stop_all(left_status, left_btn, right_status, right_btn, macro_status)).pack(side="right")
    ttk.Button(footer, text="Compact+",
               command=lambda: set_compact_mode(root, notebook,
                                               (clicker_tab, keyboard_tab, macro_tab, about_tab),
                                               footer, enable=not compact_mode)).pack(side="right", padx=6)
# --- Part 4: Hotkey editors, rebind/preview closures, logo hook, and entry ---

    # Hotkey editors
    # Left/Right in Clickers
    left_hk_row = ttk.Frame(left_frame); left_hk_row.pack(fill="x", padx=10, pady=(0, 6))
    ttk.Label(left_hk_row, text="Left hotkey:").pack(side="left")
    left_entry = ttk.Entry(left_hk_row, width=20); left_entry.insert(0, hotkeys["left"]); left_entry.pack(side="left", padx=6)

    right_hk_row = ttk.Frame(right_frame); right_hk_row.pack(fill="x", padx=10, pady=(0, 6))
    ttk.Label(right_hk_row, text="Right hotkey:").pack(side="left")
    right_entry = ttk.Entry(right_hk_row, width=20); right_entry.insert(0, hotkeys["right"]); right_entry.pack(side="left", padx=6)

    # Type in Keyboard
    type_row = ttk.Frame(kb_frame); type_row.pack(fill="x", padx=10, pady=4)
    ttk.Label(type_row, text="Type hotkey:").pack(side="left")
    type_entry = ttk.Entry(type_row, width=20); type_entry.insert(0, hotkeys["type"]); type_entry.pack(side="left", padx=6)

    # Macro hotkeys in Macros
    macro_rows = []
    for key, label in [("record_macro", "Record hotkey:"), ("stop_macro", "Stop hotkey:"), ("play_macro", "Play hotkey:")]:
        row = ttk.Frame(macro_frame)
        row.pack(fill="x", padx=10, pady=4)
        ttk.Label(row, text=label).pack(side="left")
        entry = ttk.Entry(row, width=22)
        entry.insert(0, hotkeys[key])
        entry.pack(side="left", padx=6)
        macro_rows.append((key, entry))

    # Rebind + preview closures
    def preview_cb():
        hk_preview.configure(
            text="Hotkeys — "
                 f"Compact: {hotkeys['compact_mode']} | Force Stop: {hotkeys['stop_all']}"
        )

    def rebind_cb():
        bind_all_hotkeys(
            hk_preview_label=hk_preview,
            left_status=left_status, left_btn=left_btn,
            right_status=right_status, right_btn=right_btn,
            kb_status=kb_status, kb_entry=kb_entry, stats_label=stats_label,
            toggle_compact_cb=lambda: set_compact_mode(root, notebook,
                                                       (clicker_tab, keyboard_tab, macro_tab, about_tab),
                                                       footer, enable=not compact_mode),
            stop_all_cb=lambda: stop_all(left_status, left_btn, right_status, right_btn, macro_status),
            start_rec_cb=lambda: start_recording(macro_status),
            stop_rec_cb=lambda: stop_recording(macro_status),
            play_cb=lambda: threading.Thread(target=play_macro, args=(macro_status,), daemon=True).start()
        )

    # Wire Change buttons with modal capture
    ttk.Button(left_hk_row, text="Change",
               command=lambda: start_hotkey_capture(left_entry, "left", rebind_cb, preview_cb, root)).pack(side="left", padx=4)
    ttk.Button(right_hk_row, text="Change",
               command=lambda: start_hotkey_capture(right_entry, "right", rebind_cb, preview_cb, root)).pack(side="left", padx=4)
    ttk.Button(type_row, text="Change",
               command=lambda: start_hotkey_capture(type_entry, "type", rebind_cb, preview_cb, root)).pack(side="left", padx=4)
    for key, entry in macro_rows:
        ttk.Button(entry.master, text="Change",
                   command=lambda k=key, e=entry: start_hotkey_capture(e, k, rebind_cb, preview_cb, root)).pack(side="left", padx=4)

    # Initial bind/preview + mirror panic hotkey
    rebind_cb(); preview_cb()
    keyboard.add_hotkey(hotkeys["stop_all"], lambda: stop_all(left_status, left_btn, right_status, right_btn, macro_status))

    root.mainloop()

# Entry
if __name__ == "__main__":
    build_gui()
