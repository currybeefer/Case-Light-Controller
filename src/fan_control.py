import importlib
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request
import winreg
import zipfile
from tkinter import colorchooser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class App:
    BG = '#f5f5f7'
    CARD = '#ffffff'
    ACCENT = '#0071e3'
    GREEN = '#34c759'
    TEXT = '#1d1d1f'
    SUB = '#86868b'
    OFF_BG = '#e8e8ed'
    FONT = ('Helvetica Neue', 11)
    FONT_BOLD = ('Helvetica Neue', 11, 'bold')
    FONT_TITLE = ('Helvetica Neue', 16, 'bold')

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('CaseLight')
        self.root.geometry('340x440')
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)

        icon_path = os.path.join(BASE_DIR, 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self.client = None
        self.connected = False
        self.openrgb_path = r'D:\Program Files\OpenRGB\OpenRGB.exe'
        self.light_on = True
        self.config_file = os.path.join(BASE_DIR, 'config.json')
        self.current_color = self._load_color()

        self._build_ui()
        self._ensure_dependencies()

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)

        tk.Label(self.root, text='CaseLight', font=self.FONT_TITLE,
                 bg=self.BG, fg=self.TEXT).pack(pady=(30, 4))

        self.status = tk.Label(self.root, text='Connecting to OpenRGB...',
                               font=self.FONT, bg=self.BG, fg=self.SUB)
        self.status.pack(pady=(0, 10))

        card = tk.Frame(self.root, bg=self.CARD, highlightbackground='#e0e0e0',
                        highlightthickness=1, highlightcolor='#e0e0e0', padx=0, pady=0)
        card.pack(padx=30, pady=0, fill='x')

        self.indicator = tk.Canvas(card, width=120, height=120,
                                   highlightthickness=0, bg=self.CARD,
                                   cursor='hand2')
        self.indicator.pack(pady=(20, 2))
        self.indicator.bind('<Button-1>', lambda e: self._pick_color())

        self.label = tk.Label(card, text='', font=self.FONT_BOLD, bg=self.CARD)
        self.label.pack(pady=(0, 10))

        self.toggle_canvas = tk.Canvas(card, width=64, height=34,
                                       highlightthickness=0, bg=self.CARD, cursor='hand2')
        self.toggle_canvas.pack(pady=(0, 8))
        self._draw_toggle(False)
        self.toggle_canvas.bind('<Button-1>', lambda e: self._toggle())

        self.auto_start_var = tk.BooleanVar(value=self._is_auto_start_enabled())
        self.auto_start_cb = tk.Checkbutton(
            card, text='Auto start on boot', variable=self.auto_start_var,
            command=self._toggle_auto_start,
            font=('Helvetica Neue', 10), bg=self.CARD, fg=self.TEXT,
            selectcolor=self.CARD, activebackground=self.CARD,
            activeforeground=self.TEXT, cursor='hand2', relief=tk.FLAT)
        self.auto_start_cb.pack(pady=(0, 14))

        self.info = tk.Label(self.root, text='', font=('Helvetica Neue', 9),
                             fg=self.SUB, bg=self.BG)
        self.info.pack(pady=(6, 0))

        self._draw_bulb(False)

    def _update_status(self, text, fg=None):
        self.root.after(0, lambda: self.status.config(text=text, fg=fg or self.SUB))

    def _is_auto_start_enabled(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r'Software\Microsoft\Windows\CurrentVersion\Run',
                                0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, 'CaseLight')
                return True
        except OSError:
            return False

    def _toggle_auto_start(self):
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
        try:
            if self.auto_start_var.get():
                pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
                if not os.path.exists(pythonw):
                    pythonw = sys.executable
                script = os.path.abspath(__file__)
                value = f'"{pythonw}" "{script}"'
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path,
                                    0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, 'CaseLight', 0, winreg.REG_SZ, value)
            else:
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path,
                                        0, winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, 'CaseLight')
                except OSError:
                    pass
        except OSError:
            self.auto_start_var.set(not self.auto_start_var.get())

    def _ensure_dependencies(self):
        threading.Thread(target=self._check_dependencies, daemon=True).start()

    def _check_dependencies(self):
        if not self._ensure_openrgb_package():
            return
        if not self._ensure_openrgb_exe():
            return
        self._connect()

    def _ensure_openrgb_package(self):
        if importlib.util.find_spec('openrgb') is not None:
            return True
        self._update_status('Installing openrgb package...')
        for cmd in [
            [sys.executable, '-m', 'pip', 'install', 'openrgb', '--user'],
            [sys.executable, '-m', 'pip', 'install', 'openrgb'],
        ]:
            try:
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)
                importlib.invalidate_caches()
                return True
            except Exception:
                pass
        self._update_status('Failed to install openrgb, run: pip install openrgb', '#ff3b30')
        return False

    def _ensure_openrgb_exe(self):
        if os.path.exists(self.openrgb_path):
            return True
        local_dir = os.path.join(BASE_DIR, '_openrgb')
        local_exe = os.path.join(local_dir, 'OpenRGB.exe')
        if os.path.exists(local_exe):
            self.openrgb_path = local_exe
            return True
        self._update_status('Downloading OpenRGB...')
        try:
            req = urllib.request.Request(
                'https://api.github.com/repos/OpenRGB/OpenRGB/releases/latest',
                headers={'User-Agent': 'fan-control-app'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            url = next(
                (a['browser_download_url'] for a in data['assets']
                 if 'portable' in a['name'].lower() and a['name'].endswith('.zip')),
                None)
            if not url:
                self._update_status('No OpenRGB download link found', '#ff3b30')
                return False
            os.makedirs(local_dir, exist_ok=True)
            zip_path = os.path.join(local_dir, 'openrgb.zip')
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(local_dir)
            os.remove(zip_path)
            if os.path.exists(local_exe):
                self.openrgb_path = local_exe
                return True
        except Exception as e:
            self._update_status(f'Download OpenRGB failed: {e}', '#ff3b30')
        return False

    def _draw_toggle(self, on):
        self.toggle_canvas.delete('all')
        w, h, r = 64, 34, 17
        if on:
            bg = self.GREEN
            knob_x = w - r - 2
        else:
            bg = self.OFF_BG
            knob_x = r + 2
        self.toggle_canvas.create_arc(0, 0, h, h, start=90, extent=180,
                                      fill=bg, outline='', style='pieslice')
        self.toggle_canvas.create_arc(w - h, 0, w, h, start=-90, extent=180,
                                      fill=bg, outline='', style='pieslice')
        self.toggle_canvas.create_rectangle(r, 0, w - r, h, fill=bg, outline='')
        self.toggle_canvas.create_oval(knob_x - 12, h // 2 - 12,
                                       knob_x + 12, h // 2 + 12,
                                       fill='#ffffff', outline='#d0d0d5', width=1)

    def _draw_bulb(self, lit, color=None):
        self.indicator.delete('all')
        cx, cy, r = 60, 58, 34
        if lit:
            c = color or (255, 215, 0)
            fill = '#%02x%02x%02x' % c
            for i in range(5, 0, -1):
                glow = '#%02x%02x%02x' % tuple(
                    min(255, int(c[j] * (0.1 + 0.15 * (6 - i)))) for j in range(3))
                self.indicator.create_oval(cx - r - i * 4, cy - r - i * 4,
                    cx + r + i * 4, cy + r + i * 4,
                    fill=glow, outline='')
            self.indicator.create_oval(cx - r, cy - r, cx + r, cy + r,
                fill=fill, outline='')
            self.indicator.create_oval(cx - r + 10, cy - r + 6, cx + r - 10, cy + r - 6,
                fill='', outline='#ffffff', width=1)
        else:
            self.indicator.create_oval(cx - r, cy - r, cx + r, cy + r,
                fill='#e8e8ed', outline='#d2d2d7', width=1)

    def _update_ui(self, on):
        self.light_on = on
        self._draw_bulb(on, self.current_color)
        self._draw_toggle(on)
        hex_color = '#%02x%02x%02x' % self.current_color if on else self.SUB
        self.label.config(text='Light  ON' if on else 'Light  OFF',
                          fg=hex_color if on else self.SUB)

    def _connect(self):
        from openrgb import OpenRGBClient
        def run():
            launched = False
            for _ in range(30):
                try:
                    cli = OpenRGBClient()
                    names = [d.name for d in cli.devices]
                    self.client = cli
                    self.root.after(0, self._on_connect_result, True, names)
                    return
                except Exception:
                    if not launched:
                        self.root.after(0, self.status.config,
                            {'text': 'Starting OpenRGB...'})
                        try:
                            subprocess.Popen(
                                [self.openrgb_path, '--startminimized', '--server'],
                                shell=True)
                        except Exception:
                            pass
                        launched = True
                    time.sleep(1)
            self.root.after(0, self._on_connect_result, False, [])

        threading.Thread(target=run, daemon=True).start()

    def _on_connect_result(self, ok, device_names):
        if ok:
            self.connected = True
            self.light_on = True
            self.status.config(text='Connected', fg=self.GREEN)
            if device_names:
                self.info.config(text=' | '.join(device_names))
            self._update_ui(True)
        else:
            self.status.config(text='Connection failed, make sure OpenRGB is running', fg='#ff3b30')
            self.toggle_canvas.unbind('<Button-1>')

    def _toggle(self):
        from openrgb.utils import RGBColor
        if not self.connected or not self.client:
            return
        new_state = not self.light_on

        def run():
            try:
                if new_state:
                    self.client.set_color(RGBColor(*self.current_color))
                else:
                    self.client.set_color(RGBColor(0, 0, 0))
                self.root.after(0, self._on_toggle_result, True, new_state)
            except Exception as e:
                print(f"Toggle error: {e}")
                self.root.after(0, self._on_toggle_result, False, new_state)

        threading.Thread(target=run, daemon=True).start()

    def _on_toggle_result(self, ok, new_state):
        if ok:
            self._update_ui(new_state)
        else:
            self.label.config(text='Operation failed', fg='#ff3b30')

    def _pick_color(self):
        rgb, _ = colorchooser.askcolor(
            title='Select Color',
            color='#%02x%02x%02x' % self.current_color,
            parent=self.root)
        if rgb:
            self.current_color = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
            self._save_color(self.current_color)
            if self.light_on and self.connected:
                threading.Thread(target=self._apply_color, daemon=True).start()

    def _apply_color(self):
        from openrgb.utils import RGBColor
        try:
            self.client.set_color(RGBColor(*self.current_color))
            self.root.after(0, self._update_ui, True)
        except Exception as e:
            print(f"Apply color error: {e}")

    def _load_color(self):
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                return tuple(data['color'])
        except:
            return (255, 255, 255)

    def _save_color(self, color):
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'color': list(color)}, f)
        except:
            pass

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    App().run()
