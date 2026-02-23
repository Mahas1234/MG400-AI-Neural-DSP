from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDFillRoundFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
import json
import threading
import asyncio

# Core Imports
from core.midi_client import MidiClient
from core.param_mapping import MIDI_CC_MAP
from ai.gemini_client import GeminiClient

class Lab400Kivy(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.theme_cls.accent_palette = "DeepPurple"
        
        self.midi = MidiClient()
        self.gemini = None
        self.params = {}
        self.patch_name = "NEURAL-01"
        
        # Main Screen
        screen = MDScreen()
        layout = MDBoxLayout(orientation='vertical', padding=[20, 40, 20, 20], spacing=15)
        
        # Header
        header = MDBoxLayout(size_hint_y=None, height="60dp", spacing=10)
        header.add_widget(MDLabel(
            text="LAB-400 NEURAL", 
            font_style="H5", 
            theme_text_color="Primary",
            bold=True
        ))
        self.lbl_patch = MDLabel(
            text=self.patch_name,
            theme_text_color="Secondary",
            font_style="Caption",
            halign="right"
        )
        header.add_widget(self.lbl_patch)
        layout.add_widget(header)
        
        # Prompt Area
        layout.add_widget(MDLabel(text="SONIC VISION", font_style="Overline", theme_text_color="Hint"))
        self.prompt_field = MDTextField(
            hint_text="e.g. Modern High Gain, tight bottom end...",
            multiline=True,
            mode="rectangle",
            fill_color_normal=get_color_from_hex("#0f172a"),
        )
        layout.add_widget(self.prompt_field)
        
        # Actions
        btn_layout = MDBoxLayout(size_hint_y=None, height="50dp", spacing=10)
        self.btn_gen = MDFillRoundFlatButton(
            text="SYNTHESIZE", 
            size_hint_x=0.5,
            on_release=self.start_generate
        )
        self.btn_load = MDFillRoundFlatButton(
            text="LOAD TO HW", 
            md_bg_color=self.theme_cls.accent_color,
            size_hint_x=0.5,
            on_release=self.start_load
        )
        btn_layout.add_widget(self.btn_gen)
        btn_layout.add_widget(self.btn_load)
        layout.add_widget(btn_layout)
        
        layout.add_widget(MDLabel(text="PARAMETER MATRIX", font_style="Overline", theme_text_color="Hint"))
        
        # Parameter Scroll
        scroll = ScrollView()
        self.grid = MDGridLayout(cols=2, spacing=10, size_hint_y=None, padding=5)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        layout.add_widget(scroll)
        
        screen.add_widget(layout)
        return screen

    def build_param_card(self, name, value):
        card = MDCard(
            size_hint_y=None, height="80dp",
            padding=10, radius=[12,],
            md_bg_color=get_color_from_hex("#1e293b"),
            elevation=2
        )
        box = MDBoxLayout(orientation='vertical', spacing=5)
        box.add_widget(MDLabel(text=name.upper(), font_style="Caption", theme_text_color="Hint", bold=True))
        box.add_widget(MDLabel(text=str(int(value)), font_style="H6", theme_text_color="Primary"))
        card.add_widget(box)
        return card

    def start_generate(self, *args):
        self.btn_gen.disabled = True
        self.btn_gen.text = "THINKING..."
        threading.Thread(target=self.run_generation).start()

    def run_generation(self):
        try:
            api_key = "YOUR_API_KEY" # Load from config
            if not self.gemini:
                self.gemini = GeminiClient(api_key=api_key)
            
            res = self.gemini.parse_prompt(self.prompt_field.text)
            self.params = {k: v for k, v in res.items() if k != "patchName"}
            if "patchName" in res:
                self.patch_name = res["patchName"]
                
            Clock.schedule_once(self.update_ui_after_gen)
        except Exception as e:
            print(f"Gen Error: {e}")
            Clock.schedule_once(lambda dt: self.reset_buttons())

    def update_ui_after_gen(self, dt):
        self.lbl_patch.text = self.patch_name
        self.grid.clear_widgets()
        for k, v in self.params.items():
            if k in MIDI_CC_MAP:
                self.grid.add_widget(self.build_param_card(k, v))
        self.reset_buttons()

    def start_load(self, *args):
        if not self.params: return
        self.btn_load.disabled = True
        self.btn_load.text = "SYNCING..."
        threading.Thread(target=self.run_load).start()

    def run_load(self):
        try:
            self.midi.send_patch_name(self.patch_name)
            self.midi.send_cc_parameters(self.params, MIDI_CC_MAP)
        except Exception as e:
            print(f"Load Error: {e}")
        Clock.schedule_once(lambda dt: self.reset_buttons())

    def reset_buttons(self):
        self.btn_gen.disabled = False
        self.btn_gen.text = "SYNTHESIZE"
        self.btn_load.disabled = False
        self.btn_load.text = "LOAD TO HW"

if __name__ == "__main__":
    Window.clearcolor = get_color_from_hex("#05050a")
    Lab400Kivy().run()
