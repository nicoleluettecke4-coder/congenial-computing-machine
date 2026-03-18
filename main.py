import os
import sys
import threading
import time
import math
import random
import io
import wave

# --- AUTO-INSTALLER FOR PYDROID 3 ---
# Versucht fehlende Bibliotheken automatisch zu installieren
def install_dependencies():
    import subprocess
    libs = ["requests", "kivy", "sounddevice"]
    print("Prüfe Bibliotheken...")
    for lib in libs:
        try:
            __import__(lib)
        except ImportError:
            print(f"Installiere {lib}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            print(f"{lib} installiert.")

try:
    import requests
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.relativelayout import RelativeLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.textinput import TextInput
    from kivy.uix.scrollview import ScrollView
    from kivy.clock import Clock
    from kivy.graphics import Color, Line, Ellipse, Rectangle
    from kivy.core.window import Window
    from kivy.utils import get_color_from_hex
except ImportError:
    print("\n[!] FEHLENDE BIBLIOTHEKEN ENTDECKT.")
    install_dependencies()
    print("\n[!] BITTE PROGRAMM JETZT NEU STARTEN!")
    sys.exit()

# --- AUDIO ATTEMPT (Pydroid troubleshooting) ---
sd = None
sd_error = "Fehlt"
try:
    import sounddevice as sd
    sd_error = None
except ImportError:
    sd = None
    sd_error = "NotInstalled"
except OSError:
    sd = None
    sd_error = "PortAudioMissing"

# --- CONFIGURATION ---
PC_IP = "192.168.178.85"
PORT = 5001
BASE_URL = f"https://{PC_IP}:{PORT}"

# --- COLORS (1:1 with ui.py) ---
C_BG    = get_color_from_hex("#000000")
C_PRI   = get_color_from_hex("#00d4ff")
C_MID   = get_color_from_hex("#007a99")
C_DIM   = get_color_from_hex("#003344")
C_TEXT  = get_color_from_hex("#8ffcff")
C_ACC   = get_color_from_hex("#ff6600")
C_ACC2  = get_color_from_hex("#ffcc00")
C_PANEL = get_color_from_hex("#010c10")
C_GREEN = get_color_from_hex("#00ff88")
C_RED   = get_color_from_hex("#ff3333")

class JarvisHUD(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tick = 0
        self.speaking = False
        self.rings_spin = [0.0, 120.0, 240.0]
        self.scan_angle = 0.0
        self.scan2_angle = 180.0
        self.pulse_r = []
        self.core_scale = 1.0
        self.target_scale = 1.0
        self.last_t = time.time()
        Clock.schedule_interval(self.update_logic, 1/60)

    def update_logic(self, dt):
        self.tick += 1
        now = time.time()
        if now - self.last_t > (0.14 if self.speaking else 0.55):
            self.target_scale = random.uniform(1.05, 1.11) if self.speaking else random.uniform(1.001, 1.007)
            self.last_t = now
        sp = 0.35 if self.speaking else 0.16
        self.core_scale += (self.target_scale - self.core_scale) * sp
        for i, spd in enumerate([1.2, -0.8, 1.9] if self.speaking else [0.5, -0.3, 0.82]):
            self.rings_spin[i] = (self.rings_spin[i] + spd) % 360
        self.scan_angle = (self.scan_angle + (2.8 if self.speaking else 1.2)) % 360
        self.scan2_angle = (self.scan2_angle + (-1.7 if self.speaking else -0.68)) % 360
        pspd = 3.8 if self.speaking else 1.8
        limit = 200
        self.pulse_r = [r + pspd for r in self.pulse_r if r + pspd < limit]
        if len(self.pulse_r) < 3 and random.random() < (0.06 if self.speaking else 0.022):
            self.pulse_r.append(0.0)
        self.draw_hud()

    def draw_hud(self):
        cx, cy = self.center
        self.canvas.clear()
        with self.canvas:
            Color(*C_DIM[:3], 0.2)
            Ellipse(pos=(cx-180, cy-180), size=(360, 360))
            for r in self.pulse_r:
                alpha = max(0, 1.0 - r / 200)
                Color(*C_PRI[:3], alpha * 0.5)
                Line(circle=(cx, cy, r), width=1)
            ring_configs = [(170, C_PRI, self.rings_spin[0], 110, 75), (140, C_MID, self.rings_spin[1], 75, 55), (110, C_DIM, self.rings_spin[2], 55, 38)]
            for r, col, spin, arch_l, gap in ring_configs:
                Color(*col[:3], 0.6)
                for s in range(0, 360, arch_l + gap):
                    start = (spin + s) % 360
                    Line(circle=(cx, cy, r, start, start + arch_l), width=2)
            Color(*C_PRI[:3], 0.8)
            Line(circle=(cx, cy, 180, self.scan_angle, self.scan_angle + 42), width=3)
            Color(*C_ACC[:3], 0.4)
            Line(circle=(cx, cy, 180, self.scan2_angle, self.scan2_angle + 42), width=2)
            core_r = 60 * self.core_scale
            Color(*C_PRI[:3], 0.1)
            Ellipse(pos=(cx-core_r-20, cy-core_r-20), size=((core_r+20)*2, (core_r+20)*2))
            Color(*C_PRI[:3], 0.8)
            Line(circle=(cx, cy, core_r), width=2)
            Color(*C_PRI[:3], 0.3)
            Ellipse(pos=(cx-core_r+10, cy-core_r+10), size=((core_r-10)*2, (core_r-10)*2))
            blen = 30
            Color(*C_PRI)
            bracket_r = 200
            for dx, dy in [(-1,1), (1,1), (-1,-1), (1,-1)]:
                bx, by = cx + dx * bracket_r, cy + dy * bracket_r
                Line(points=[bx, by - dy*blen, bx, by, bx - dx*blen, by], width=2)

class JarvisMobileApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        self.title = "J.A.R.V.I.S — MARK XXX"
        self.is_muted = False
        self.is_recording = False
        
        root = RelativeLayout()
        
        # --- HEADER ---
        header = BoxLayout(orientation='vertical', size_hint=(1, None), height=140, pos_hint={'top': 1}, padding=[20, 10])
        with header.canvas.before:
            Color(0, 0.03, 0.05, 1)
            Rectangle(pos=(0, Window.height - 140), size=(Window.width, 140))
            Color(*C_MID[:3], 1)
            Line(points=[0, Window.height - 140, Window.width, Window.height - 140], width=1)

        title_lbl = Label(text="J.A.R.V.I.S", font_size='26sp', color=C_PRI, bold=True, size_hint_y=None, height=40)
        motto_lbl = Label(text="Just A Rather Very Intelligent System", font_size='11sp', color=C_MID, size_hint_y=None, height=20)
        badge_lbl = Label(text="MARK XXX", font_size='11sp', color=C_DIM, size_hint_y=None, height=20)
        
        header.add_widget(title_lbl)
        header.add_widget(motto_lbl)
        header.add_widget(badge_lbl)
        root.add_widget(header)

        # --- OVERLAY ---
        self.clock_lbl = Label(text="00:00:00", font_size='18sp', color=C_PRI, bold=True, pos_hint={'right': 0.98, 'top': 0.98}, size_hint=(None, None), size=(150, 40))
        Clock.schedule_interval(self.update_clock, 1)
        root.add_widget(self.clock_lbl)

        self.mute_btn = Button(text="UNMUTED", font_size='12sp', color=C_GREEN, background_color=(0, 0.05, 0.08, 1),
                               size_hint=(None, None), size=(110, 40), pos_hint={'x': 0.02, 'top': 0.98})
        self.mute_btn.bind(on_release=self.toggle_mute)
        root.add_widget(self.mute_btn)

        self.fps_lbl = Label(text="FPS: 60", font_size='10sp', color=C_DIM, pos_hint={'x': 0.02, 'top': 0.93}, size_hint=(None, None), size=(110, 30))
        Clock.schedule_interval(self.update_fps, 1)
        root.add_widget(self.fps_lbl)

        # --- HUD ---
        self.hud = JarvisHUD(size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.55})
        root.add_widget(self.hud)

        # --- MIC BUTTON ---
        self.mic_btn = Button(text="REC", font_size='14sp', color=C_PRI, background_color=(0, 0.05, 0.1, 1),
                              size_hint=(None, None), size=(70, 70), pos_hint={'right': 0.95, 'center_y': 0.55})
        self.mic_btn.bind(on_release=self.toggle_record)
        root.add_widget(self.mic_btn)

        # --- BOTTOM ---
        bottom_area = BoxLayout(orientation='vertical', padding=20, spacing=10, size_hint=(1, None), height=300, pos_hint={'y': 0.05})
        self.log_scroll = ScrollView(size_hint=(1, 1))
        self.log_label = Label(text="[color=ffcc00]SYS: Systems initialised. JARVIS online.[/color]", 
                               markup=True, size_hint_y=None, halign='left', valign='top',
                               color=C_TEXT, font_size='14sp', text_size=(Window.width - 40, None))
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        self.log_scroll.add_widget(self.log_label)
        
        input_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        self.cmd_input = TextInput(multiline=False, background_color=(0, 0.05, 0.08, 1), 
                                  foreground_color=(1, 1, 1, 1), cursor_color=C_PRI)
        self.cmd_input.bind(on_text_validate=self.send_command)
        send_btn = Button(text="▸", size_hint_x=None, width=80, background_color=(0, 0.03, 0.05, 1), color=C_PRI, font_size='24sp', bold=True)
        send_btn.bind(on_release=self.send_command)
        input_box.add_widget(self.cmd_input)
        input_box.add_widget(send_btn)
        bottom_area.add_widget(self.log_scroll)
        bottom_area.add_widget(input_box)
        root.add_widget(bottom_area)

        footer = Label(text="FatihMakes Industries  ·  CLASSIFIED  ·  MARK XXX", font_size='10sp', color=C_DIM, size_hint=(1, None), height=30, pos_hint={'y': 0})
        root.add_widget(footer)
        return root

    def update_clock(self, dt): self.clock_lbl.text = time.strftime("%H:%M:%S")
    def update_fps(self, dt): self.fps_lbl.text = f"FPS: {int(Clock.get_rfps())}"
    def toggle_mute(self, instance):
        self.is_muted = not self.is_muted
        self.mute_btn.text = "MUTED" if self.is_muted else "UNMUTED"
        self.mute_btn.color = C_RED if self.is_muted else C_GREEN
        self.add_log(f"SYS: Microphone {'MUTED' if self.is_muted else 'UNMUTED'}.", 'sys')
    def add_log(self, text, type='sys'):
        color = "ffcc00" if type == 'sys' else "00d4ff" if type == 'ai' else "e8e8e8"
        self.log_label.text += f"\n[color={color}]{text}[/color]"
        Clock.schedule_once(lambda dt: setattr(self.log_scroll, 'scroll_y', 0), 0.1)
    def send_command(self, instance):
        text = self.cmd_input.text.strip()
        if not text: return
        self.cmd_input.text = ""
        self.add_log(f"YOU: {text}", 'you')
        threading.Thread(target=lambda: requests.post(f"{BASE_URL}/command", json={"text": text}, verify=False)).start()
    def toggle_record(self, instance):
        if not sd:
            if sd_error == "PortAudioMissing":
                self.add_log("SYS: sounddevice ist zwar installiert, aber die PortAudio System-Bibliothek fehlt auf Android. Mikrofon über die App leider nicht möglich.", 'ai')
            else:
                self.add_log("SYS: sounddevice fehlt! Bitte 'pip install sounddevice' im Pydroid Pip Menü.", 'ai')
            return
        # Record logic (simplified for parity)
        self.add_log("SYS: Aufnahme wird gestartet...", 'sys')

if __name__ == "__main__":
    JarvisMobileApp().run()
