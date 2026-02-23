import flet as ft
import json
import asyncio
from core.midi_client import MidiClient
from core.param_mapping import MIDI_CC_MAP
from ai.gemini_client import GeminiClient

class Lab400Mobile:
    def __init__(self, page: ft.Page):
        self.page = page
        self.midi = MidiClient()
        self.gemini = None
        self.params = {}
        self.patch_name = "NEURAL-01"
        self.loading = False
        
        # UI State
        self.page.title = "Lab-400 Mobile"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#05050a"
        self.page.padding = 0
        self.page.window_width = 400
        self.page.window_height = 800
        
        self.init_ui()

    def init_ui(self):
        # Header
        self.patch_title = ft.Text(self.patch_name, size=10, color="#38bdf8", weight="bold")
        self.sync_dot = ft.Container(width=10, height=10, border_radius=5, bgcolor="red")
        
        self.header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.MEMORY, color="#00f7ff", size=24),
                ft.Column([
                    ft.Text("LAB-400", size=18, weight="black", color="white", letter_spacing=1),
                    self.patch_title,
                ], spacing=0),
                ft.Spacer(),
                self.sync_dot,
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.only(left=24, right=24, top=40, bottom=20),
            bgcolor="#0a0a14",
        )

        # Prompt Input Area
        self.prompt_box = ft.TextField(
            label="Sonic Vision",
            hint_text="e.g. Aggressive modern metal with scooped mids...",
            multiline=True,
            min_lines=3,
            max_lines=3,
            bgcolor="#0f172a",
            border_color="#1e293b",
            focused_border_color="#00f7ff",
            border_radius=16,
            label_style=ft.TextStyle(color="#94a3b8"),
        )

        # Action Buttons
        self.btn_gen = ft.ElevatedButton(
            content=ft.Row([ft.Icon(ft.icons.ZAP, size=16), ft.Text("SYNTHESIZE")], alignment="center"),
            bgcolor="#00f7ff",
            color="black",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            height=50,
            on_click=self.handle_generate
        )

        self.btn_load = ft.OutlinedButton(
            content=ft.Row([ft.Icon(ft.icons.CPU, size=16), ft.Text("LOAD TO HW")], alignment="center"),
            style=ft.ButtonStyle(
                side={"": ft.BorderSide(2, "#00f7ff")},
                shape=ft.RoundedRectangleBorder(radius=12),
                color="#00f7ff",
            ),
            height=50,
            on_click=self.handle_load
        )

        # Topology Board
        self.topology = ft.Row(
            controls=[
                self.build_block(label) for label in ["CMP", "EFX", "AMP", "EQ", "NR", "MOD", "DLY", "RVB"]
            ],
            scroll=ft.ScrollMode.ALWAYS,
            spacing=10
        )

        # Main Layout
        self.knob_grid = ft.GridView(
            expand=1,
            runs_count=3,
            max_extent=120,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        self.page.add(
            self.header,
            ft.Container(
                content=ft.Column([
                    ft.Text("NEURAL DECK", size=10, weight="bold", color="#94a3b8", letter_spacing=2),
                    self.prompt_box,
                    ft.Row([self.btn_gen, self.btn_load], spacing=10),
                    ft.Divider(color="#1e293b", height=40),
                    ft.Text("SIGNAL TOPOLOGY", size=10, weight="bold", color="#94a3b8", letter_spacing=2),
                    self.topology,
                    ft.Container(height=20),
                    ft.Text("PARAMETER MATRIX", size=10, weight="bold", color="#94a3b8", letter_spacing=2),
                    self.knob_grid,
                ], scroll=ft.ScrollMode.HIDDEN, spacing=15),
                padding=24,
                expand=True
            )
        )
        
        self.check_midi()

    def build_block(self, label):
        return ft.Container(
            content=ft.Text(label, size=9, weight="bold", color="white"),
            bgcolor="#1e293b",
            width=50,
            height=50,
            border_radius=8,
            alignment=ft.alignment.center,
            border=ft.border.all(1, "rgba(255,255,255,0.05)")
        )

    def build_knob(self, label, value):
        return ft.Container(
            content=ft.Column([
                ft.Text(label.upper(), size=8, color="#94a3b8", weight="bold"),
                ft.Stack([
                    ft.PieChart(
                        sections=[
                            ft.PieChartSection(value, color="#00f7ff", radius=5),
                            ft.PieChartSection(100 - value, color="#1e293b", radius=5),
                        ],
                        sections_space=0,
                        center_space_radius=15,
                        width=40,
                        height=40,
                    ),
                    ft.Container(
                        content=ft.Text(str(int(value)), size=8, weight="bold"),
                        alignment=ft.alignment.center
                    )
                ], alignment=ft.alignment.center)
            ], alignment="center", spacing=5),
            bgcolor="rgba(255,255,255,0.02)",
            border_radius=12,
            padding=10,
            border=ft.border.all(1, "rgba(255,255,255,0.05)")
        )

    def check_midi(self):
        try:
            self.midi.find_device()
            self.sync_dot.bgcolor = "green"
            self.page.update()
        except:
            self.sync_dot.bgcolor = "red"
            self.page.update()

    async def handle_generate(self, e):
        api_key = self.page.session.get("api_key") or "YOUR_API_KEY" # In real app, load from secure storage
        if not self.gemini:
            self.gemini = GeminiClient(api_key=api_key)
            
        self.btn_gen.disabled = True
        self.btn_gen.content.controls[0].name = ft.icons.REFRESH
        self.page.update()
        
        try:
            res = await asyncio.to_thread(self.gemini.parse_prompt, self.prompt_box.value)
            self.params = {k: v for k, v in res.items() if k != "patchName"}
            if "patchName" in res:
                self.patch_name = res["patchName"]
                self.patch_title.value = self.patch_name
            
            # Update Knobs
            self.knob_grid.controls.clear()
            for k, v in self.params.items():
                if k in MIDI_CC_MAP:
                    self.knob_grid.controls.append(self.build_knob(k, v))
            
            self.page.snack_bar = ft.SnackBar(ft.Text(f"✓ {self.patch_name} Calculated"))
            self.page.snack_bar.open = True
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"✕ Fault: {str(ex)}"))
            self.page.snack_bar.open = True
            
        self.btn_gen.disabled = False
        self.btn_gen.content.controls[0].name = ft.icons.ZAP
        self.page.update()

    async def handle_load(self, e):
        if not self.params:
            self.page.snack_bar = ft.SnackBar(ft.Text("✕ Matrix Empty - Synth First"))
            self.page.snack_bar.open = True
            self.page.update()
            return
            
        self.btn_load.disabled = True
        old_name = self.patch_title.value
        self.patch_title.value = "SYNCING..."
        self.page.update()
        
        try:
            await asyncio.to_thread(self.midi.send_patch_name, old_name)
            await asyncio.to_thread(self.midi.send_cc_parameters, self.params, MIDI_CC_MAP)
            self.page.snack_bar = ft.SnackBar(ft.Text("✓ Hardware Synchronized"))
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"✕ Load Fail: {str(ex)}"))
            
        self.patch_title.value = old_name
        self.btn_load.disabled = False
        self.page.snack_bar.open = True
        self.page.update()

def main(page: ft.Page):
    Lab400Mobile(page)

if __name__ == "__main__":
    ft.app(target=main)
