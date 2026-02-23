import sys
import os
import json
import logging
import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox,
    QFrame, QSplitter, QLineEdit, QTabWidget, QScrollArea, QSlider, QGridLayout, QGroupBox, QListWidget, QInputDialog
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtGui import QFont, QColor

from ai.gemini_client import GeminiClient
from core.binary_encoder import BinaryEncoder
from core.midi_client import MidiClient
from core.database import ToneLibrary
from core.param_mapping import MIDI_CC_MAP

DARK_THEME = """
QMainWindow { background-color: #05050a; }
QWidget { font-family: 'Outfit', 'Inter', 'Segoe UI', sans-serif; font-size: 13px; color: #e2e8f0; }

/* Premium Glass Cards */
QFrame#Divider { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #05050a, stop:0.5 #00f7ff, stop:1 #05050a); border-radius: 1px; }

/* Duct Tape Headings */
QLabel#SectionLabel {
    background-color: rgba(30, 41, 59, 0.4);
    color: #00f7ff;
    font-weight: 900;
    padding: 6px 12px;
    border: 1px solid rgba(0, 247, 255, 0.2);
    border-radius: 4px;
}

QPushButton {
    background-color: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px; padding: 12px 20px; color: #ffffff;
    font-weight: 800; text-transform: uppercase; letter-spacing: 1.5px;
}
QPushButton:hover { 
    background-color: rgba(51, 65, 85, 0.6);
    border: 1px solid #00f7ff; 
    color: #00f7ff;
}
QPushButton:pressed { background-color: #0c0c1a; transform: translateY(1px); }

QPushButton#btnSend { 
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f7ff, stop:1 #7000ff); 
    color: #000;
    border: none; 
}
QPushButton#btnSend:hover { 
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #80fbff, stop:1 #a066ff); 
}

QPushButton#btnAnalyze { 
    background-color: transparent; border: 1px solid #2dd4bf; color: #2dd4bf;
}
QPushButton#btnAnalyze:hover { background-color: rgba(45, 212, 191, 0.1); }

QTextEdit, QLineEdit, QListWidget {
    background-color: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 12px; color: #f1f5f9;
}
QTextEdit:focus, QLineEdit:focus, QListWidget:focus { border: 1px solid #38bdf8; background-color: #0f172a; }

QLabel { color: #94a3b8; }
QLabel#TitleText { 
    color: #ffffff; font-weight: 900; letter-spacing: -1px; font-size: 34px; 
    background: transparent;
}
QLabel#SubtitleText { color: #38bdf8; font-weight: 700; font-size: 13px; letter-spacing: 2px; text-transform: uppercase; }

QTabWidget::pane { border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; background: rgba(15, 23, 42, 0.4); top: -1px; }
QTabBar::tab {
    background: #0f172a; border: 1px solid rgba(255, 255, 255, 0.05); border-bottom: none;
    padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; color: #94a3b8;
    margin-right: 4px;
}
QTabBar::tab:selected { background: #1e293b; color: #38bdf8; font-weight: bold; border-color: rgba(255, 255, 255, 0.1); }

QSlider::groove:horizontal { height: 6px; background: rgba(0, 0, 0, 0.6); border-radius: 3px; }
QSlider::sub-page:horizontal { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f7ff, stop:1 #7000ff); border-radius: 3px; }
QSlider::handle:horizontal { 
    background: #ffffff; width: 22px; height: 22px; margin-top: -8px; margin-bottom: -8px; border-radius: 11px; border: 2px solid #00f7ff;
}

QGroupBox { border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; margin-top: 20px; padding: 20px; background: rgba(255, 255, 255, 0.02); }
QGroupBox::title { subcontrol-origin: margin; left: 15px; padding: 0 10px; color: #f8fafc; font-weight: 900; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }

QScrollBar:vertical { border: none; background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: rgba(255, 255, 255, 0.1); border-radius: 4px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background: rgba(255, 255, 255, 0.2); }
QScrollBar::add-line, QScrollBar::sub-line { border: none; background: none; }
"""

class AIThread(QThread):
    finished = Signal(object)
    error = Signal(str)
    def __init__(self, mode, api_key, data, model="gemini-2.5-flash"):
        super().__init__()
        self.mode = mode
        self.data = data
        self.gemini = GeminiClient(api_key=api_key, model=model)
    def run(self):
        try:
            if self.mode == 'generate':
                res = self.gemini.parse_prompt(self.data)
                self.finished.emit(res)
            elif self.mode == 'analyze':
                res = self.gemini.analyze_tone(self.data)
                self.finished.emit(res)
        except Exception as e:
            self.error.emit(str(e))

class MidiSignals(QObject):
    cc_received = Signal(int, int)
    global_update = Signal(dict)

class MainWindow(QMainWindow):
    def __init__(self, config_mgr=None, logger=None):
        super().__init__()
        self.config_mgr = config_mgr
        self.logger = logger or logging.getLogger(__name__)
        self.setWindowTitle("MG400 AI DSP Routing Suite Pro")
        self.resize(1200, 800)
        self.setStyleSheet(DARK_THEME)
        
        self.template_path = None
        self.generated_params = {}
        self.db = ToneLibrary()
        self.midi = MidiClient()
        self.current_patch_name = "NEURAL-01"
        self.midi_signals = MidiSignals()
        self.reverse_cc_map = {v: k for k, v in MIDI_CC_MAP.items()}
        self.sliders = {} # Connect CC names to QSlider instances
        
        self.init_ui()
        self._load_library()
        
        # Start persistent MIDI listening
        try:
            self.midi.start_listening(self._on_midi_rx)
            self.log_message("Bidirectional MIDI listener bound to background thread.")
        except Exception as e:
            self.log_message(f"MIDI Input binding failed: {e}")

        # Start Global Multi-Device Sync Stream
        import threading
        self.sse_thread = threading.Thread(target=self._sse_listen_loop, daemon=True)
        self.sse_thread.start()

        if self.config_mgr:
            last_tpl = self.config_mgr.get("last_template_path", "")
            if last_tpl and os.path.exists(last_tpl):
                self.template_path = last_tpl
                self.lbl_template.setText(f"Loaded from config: {last_tpl}")
                self._display_loaded_params()
                
        self.log_message("System initialized successfully.")

    def _on_midi_rx(self, control, value):
        self.midi_signals.cc_received.emit(control, value)

    def _handle_cc(self, control, value):
        if control in self.reverse_cc_map:
            param_key = self.reverse_cc_map[control]
            self.generated_params[param_key] = float(value)
            self._fire_global_sync({param_key: int(value)})
            if param_key in self.sliders:
                # Block signals so we don't circularly fire back out to MIDI
                slider, val_lbl = self.sliders[param_key]
                slider.blockSignals(True)
                slider.setValue(int(value))
                val_lbl.setText(str(int(value)))
                slider.blockSignals(False)

    def _sse_listen_loop(self):
        import pysher
        import json
        import time

        def callback(data):
            try:
                data_dict = json.loads(data)
                if data_dict.get('source') != 'macHost':
                    params = data_dict.get('params', {})
                    self.midi_signals.global_update.emit(params)
            except Exception as e:
                self.logger.error(f"Pusher event decode failed: {e}")

        def connect_handler(data):
            # Subscribe to the worldwide sync channel
            channel = pusher_client.subscribe('mg400-updates')
            channel.bind('patch-update', callback)
            self.log_message("✓ Neural Cloud Mesh bound via Pusher.")

        try:
            cluster = self.config_mgr.get("pusher_cluster", "ap2")
            # Use provided public key
            pusher_client = pysher.Pusher('854cb7b69b1f213de54a', cluster=cluster)
            pusher_client.connection.bind('pusher:connection_established', connect_handler)
            pusher_client.connect()

            while True:
                # Keep thread alive
                time.sleep(10)
        except Exception as e:
            self.logger.error(f"Pusher Initialization Fail: {e}")
            time.sleep(5)

    def _fire_global_sync(self, params_dict):
        import pusher
        import threading
        
        # Load from config or env
        app_id = self.config_mgr.get("pusher_app_id") or os.getenv('PUSHER_APP_ID')
        key = '854cb7b69b1f213de54a'
        secret = self.config_mgr.get("pusher_secret") or os.getenv('PUSHER_SECRET')
        cluster = self.config_mgr.get("pusher_cluster", "ap2")

        def worker():
            try:
                if not secret:
                    self.logger.warning("Pusher Secret missing - bypassing global broadcast.")
                    return

                p_client = pusher.Pusher(app_id=app_id, key=key, secret=secret, cluster=cluster, ssl=True)
                p_client.trigger('mg400-updates', 'patch-update', {
                    'source': 'macHost',
                    'params': params_dict
                })
            except Exception as e:
                self.logger.error(f"Global sync broadcast failed: {e}")
        
        threading.Thread(target=worker, daemon=True).start()

    def _handle_global_update(self, partial_params):
        for k, v in partial_params.items():
            self.generated_params[k] = float(v)
            if k in self.sliders:
                slider, val_lbl = self.sliders[k]
                slider.blockSignals(True)
                slider.setValue(int(v))
                val_lbl.setText(str(int(v)))
                slider.blockSignals(False)
            
            # Autopush to physical MG-400
            if k in MIDI_CC_MAP and hasattr(self, 'midi'):
                try:
                    self.midi.outport = mido.open_output(self.midi.port_name) if getattr(self.midi, 'port_name', None) else None
                    if self.midi.outport:
                        msg = mido.Message('control_change', channel=0, control=MIDI_CC_MAP[k], value=int(v))
                        self.midi.outport.send(msg)
                except: pass

    def init_ui(self):
        self.midi_signals.cc_received.connect(self._handle_cc)
        self.midi_signals.global_update.connect(self._handle_global_update)

        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        central_widget.setStyleSheet("#CentralWidget { background: qradialgradient(cx:0.5, cy:0, radius:1.2, fx:0.5, fy:0, stop:0 #1a1635, stop:1 #05050a); }")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header_layout = QVBoxLayout()
        title_lbl = QLabel("MG400 DSP Signal Modeler")
        title_lbl.setObjectName("TitleText")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_lbl = QLabel("Professional Bi-Directional Algorithmic Signal Chain Generation")
        subtitle_lbl.setObjectName("SubtitleText")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_lbl)
        header_layout.addWidget(subtitle_lbl)
        main_layout.addLayout(header_layout)

        line = QFrame()
        line.setObjectName("Divider")
        line.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(line)

        # Connect Top Tools (API Key, Load File)
        top_layout = QHBoxLayout()
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_api_key.setPlaceholderText("Enter Google Gemini API Key")
        if self.config_mgr:
            self.txt_api_key.setText(self.config_mgr.get("gemini_api_key", ""))
        self.txt_api_key.textChanged.connect(lambda t: self.config_mgr.set("gemini_api_key", t) if self.config_mgr else None)
        
        self.btn_load_template = QPushButton("1. Load Base Patch (.mg400patch)")
        self.btn_load_template.clicked.connect(self.load_template)
        self.lbl_template = QLabel("No template loaded.")
        
        top_layout.addWidget(self.btn_load_template)
        top_layout.addWidget(self.lbl_template, stretch=1)
        
        self.txt_patch_name = QLineEdit(self.current_patch_name)
        self.txt_patch_name.setFixedWidth(120)
        self.txt_patch_name.setPlaceholderText("PATCH NAME")
        self.txt_patch_name.textChanged.connect(lambda t: setattr(self, 'current_patch_name', t.upper()))
        top_layout.addWidget(QLabel("Name:"))
        top_layout.addWidget(self.txt_patch_name)

        top_layout.addWidget(QLabel("API Key:"))
        top_layout.addWidget(self.txt_api_key)
        main_layout.addLayout(top_layout)

        # Splitting logic into 3 chunks: Library, Prompts, Parameters
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # == PANEL 1: Library & Analyics ==
        lib_panel = QWidget()
        lib_layout = QVBoxLayout(lib_panel)
        lib_layout.setContentsMargins(0,0,0,0)
        lib_layout.addWidget(QLabel("Saved DSP Configurations:"))
        
        self.list_lib = QListWidget()
        self.list_lib.itemDoubleClicked.connect(self.load_from_db)
        lib_layout.addWidget(self.list_lib)
        
        btn_save_db = QPushButton("Save Current to Library")
        btn_save_db.clicked.connect(self.save_to_db)
        lib_layout.addWidget(btn_save_db)

        self.btn_analyze = QPushButton("Execute Spectrum Analysis (AI)")
        self.btn_analyze.setObjectName("btnAnalyze")
        self.btn_analyze.clicked.connect(self.analyze_tone)
        lib_layout.addWidget(self.btn_analyze)

        # Support Section
        support_frame = QFrame()
        support_frame.setStyleSheet("background: rgba(255, 255, 255, 0.05); border-radius: 12px; margin-top: 10px;")
        support_layout = QVBoxLayout(support_frame)
        
        support_label = QLabel("SUPPORT THE DEVELOPER")
        support_label.setStyleSheet("font-size: 10px; font-weight: 900; color: #38bdf8; letter-spacing: 1px;")
        support_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        support_layout.addWidget(support_label)
        
        support_btns = QHBoxLayout()
        btn_coffee = QPushButton("Coffee")
        btn_coffee.setStyleSheet("background-color: #FFDD00; color: #000; font-size: 10px; padding: 6px;")
        btn_coffee.clicked.connect(lambda: os.system("open https://buymeacoffee.com/mahas"))
        
        btn_github = QPushButton("Sponsor")
        btn_github.setStyleSheet("background-color: #fff; color: #000; font-size: 10px; padding: 6px;")
        btn_github.clicked.connect(lambda: os.system("open https://github.com/sponsors/Mahas1234"))
        
        support_btns.addWidget(btn_coffee)
        support_btns.addWidget(btn_github)
        support_layout.addLayout(support_btns)
        
        lib_layout.addWidget(support_frame)

        splitter.addWidget(lib_panel)

        # == PANEL 2: Prompting ==
        prompt_panel = QWidget()
        prompt_layout = QVBoxLayout(prompt_panel)
        prompt_layout.setContentsMargins(0,0,0,0)
        
        prompt_layout.addWidget(QLabel("2. Target Soundstage Profile (Prompt):"))
        self.txt_prompt = QTextEdit()
        self.txt_prompt.setPlaceholderText("e.g. 'Generate a modern high-gain routing with parametric mid-scoops, sharp noise reduction thresholds, and an expansive delay tail via the effects loop...'")
        prompt_layout.addWidget(self.txt_prompt)
        
        btn_gen = QPushButton("3. Compute DSP Topology")
        btn_gen.clicked.connect(lambda: self.trigger_generation(False))
        prompt_layout.addWidget(btn_gen)
        
        self.btn_remix = QPushButton("A/B Algorithm Re-Routing (Variation)")
        self.btn_remix.setStyleSheet("background-color: transparent; border: 1px solid #38bdf8; color: #38bdf8;")
        self.btn_remix.clicked.connect(lambda: self.trigger_generation(True))
        prompt_layout.addWidget(self.btn_remix)
        self.btn_gen = btn_gen

        splitter.addWidget(prompt_panel)

        # == PANEL 3: Realtime Dash ==
        params_panel = QWidget()
        params_layout = QVBoxLayout(params_panel)
        params_layout.setContentsMargins(0,0,0,0)
        params_layout.addWidget(QLabel("Active Hardware Signal Chain (Live CC):"))
        
        self.param_tabs = QTabWidget()
        # Dashboard
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        self.preview_scroll.setWidget(self.preview_widget)
        self.param_tabs.addTab(self.preview_scroll, "Dashboard")
        
        # JSON
        self.txt_params = QTextEdit()
        self.txt_params.setReadOnly(True)
        self.param_tabs.addTab(self.txt_params, "Raw Code")
        
        params_layout.addWidget(self.param_tabs)
        
        horiz_btns = QHBoxLayout()
        self.btn_export = QPushButton("Export Binary (.mg400patch)")
        self.btn_export.setObjectName("btnExport")
        self.btn_export.clicked.connect(self.export_patch)
        self.btn_send = QPushButton("Push To Processor Output")
        self.btn_send.setObjectName("btnSend")
        self.btn_send.clicked.connect(self.send_to_device)
        horiz_btns.addWidget(self.btn_export)
        horiz_btns.addWidget(self.btn_send)
        params_layout.addLayout(horiz_btns)

        splitter.addWidget(params_panel)
        splitter.setSizes([250, 350, 450])
        main_layout.addWidget(splitter, stretch=2)

        # Logger
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFixedHeight(100)
        main_layout.addWidget(self.txt_log)

    def log_message(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.append(f"[{ts}] {msg}")
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())
        self.logger.info(msg)

    def load_template(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Open UI Template", "", "MG400 Patch (*.mg400patch);;All Files (*)")
        if fn:
            self.template_path = fn
            if self.config_mgr: self.config_mgr.set("last_template_path", fn)
            self.lbl_template.setText(os.path.basename(fn))
            self.log_message(f"Loaded template: {fn}")
            self._display_loaded_params()

    def _display_loaded_params(self):
        if not self.template_path: return
        try:
            enc = BinaryEncoder(self.template_path)
            enc.load_template()
            self.generated_params = enc.get_parameters()
            self._build_dashboard(self.generated_params)
            self.txt_params.setText(json.dumps(self.generated_params, indent=4))
        except Exception as e:
            self.log_message(f"Format decode error: {e}")

    def trigger_generation(self, is_remix=False):
        prompt = self.txt_prompt.toPlainText().strip()
        api_key = self.txt_api_key.text().strip()
        if not api_key or not prompt:
            QMessageBox.critical(self, "Error", "API Key and Prompt required.")
            return
        
        if is_remix:
            prompt += " Apply micro-adjustments to parametric EQ bounds and modulation decay factors to derive a parallel variation."
            
        self.btn_gen.setEnabled(False)
        self.btn_remix.setEnabled(False)
        self.log_message("Compiling AI DSP Chain...")
        self.thread = AIThread('generate', api_key, prompt)
        self.thread.finished.connect(self._on_gen_fin)
        self.thread.error.connect(self._on_err)
        self.thread.start()

    def _on_gen_fin(self, params):
        if "patchName" in params:
            self.current_patch_name = params["patchName"].upper()
            self.txt_patch_name.setText(self.current_patch_name)
            
        self.generated_params = params
        self.txt_params.setText(json.dumps(params, indent=4))
        self._build_dashboard(params)
        self.btn_gen.setEnabled(True)
        self.btn_remix.setEnabled(True)
        self.log_message(f"Successfully compiled AI mapping: {self.current_patch_name}")

    def _build_dashboard(self, params):
        while self.preview_layout.count():
            w = self.preview_layout.takeAt(0).widget()
            if w: w.deleteLater()
        
        self.sliders.clear()
        groups = {}
        for k, v in params.items():
            cat = k.split("_")[0].upper()
            if cat not in groups: groups[cat] = []
            groups[cat].append((k, v))
            
        for cat, items in groups.items():
            gb = QGroupBox(f"{cat} Routing Block")
            grid = QGridLayout(gb)
            for row, (k, v) in enumerate(items):
                lbl = QLabel(k)
                lbl.setStyleSheet("font-size: 11px;")
                slider = QSlider(Qt.Orientation.Horizontal)
                slider.setMaximum(127) # Midi max
                
                num_val = int(v) if isinstance(v, (int, float)) else 0
                num_val = max(0, min(127, num_val))
                slider.setValue(num_val)
                
                val_lbl = QLabel(str(num_val))
                val_lbl.setStyleSheet("font-size: 11px; color: #38bdf8;")
                
                # Bind lambda capturing key
                slider.valueChanged.connect(lambda val, key=k, vl=val_lbl: self._on_ui_slider_moved(key, val, vl))
                
                grid.addWidget(lbl, row, 0)
                grid.addWidget(slider, row, 1)
                grid.addWidget(val_lbl, row, 2)
                self.sliders[k] = (slider, val_lbl)
                
            self.preview_layout.addWidget(gb)
        self.preview_layout.addStretch()
        self.param_tabs.setCurrentIndex(0)

    def _on_ui_slider_moved(self, key, val, label):
        label.setText(str(val))
        self.generated_params[key] = float(val)
        self._fire_global_sync({key: int(val)})
        # Actively push to MG-400 physical unit if connected
        if key in MIDI_CC_MAP:
            try:
                # Fire silent CC background sync
                self.midi.outport = mido.open_output(self.midi.port_name) if getattr(self.midi, 'port_name', None) else None
                if self.midi.outport:
                     msg = mido.Message('control_change', control=MIDI_CC_MAP[key], value=int(val))
                     self.midi.outport.send(msg)
            except: pass

    def analyze_tone(self):
        if not self.generated_params: return
        api_key = self.txt_api_key.text().strip()
        if not api_key: return QMessageBox.critical(self, "Error", "API Key required for Analytics.")
        
        self.btn_analyze.setText("Reading DSP Memory...")
        self.thread = AIThread('analyze', api_key, self.generated_params)
        self.thread.finished.connect(self._on_analyze_fin)
        self.thread.error.connect(self._on_err)
        self.thread.start()

    def _on_analyze_fin(self, desc):
        self.btn_analyze.setText("Execute Spectrum Analysis (AI)")
        QMessageBox.information(self, "AI Signal Trace Analysis", desc)
        self.log_message("Reverse Tone Analytics complete.")

    def _on_err(self, err):
        self.log_message(f"Compute thread execution failed: {err}")
        self.btn_gen.setEnabled(True)
        self.btn_remix.setEnabled(True)
        self.btn_analyze.setText("Execute Spectrum Analysis (AI)")

    def _load_library(self):
        self.list_lib.clear()
        for t in self.db.load_all_tones():
            self.list_lib.addItem(f"{t['id']} | {t['name']} [{t.get('tags','')}]")

    def save_to_db(self):
        if not self.generated_params: return
        name, ok = QInputDialog.getText(self, "Save Tone", "Enter Patch Name:")
        if ok and name:
            tags, _ = QInputDialog.getText(self, "Save Tone", "Tags (comma separated):", text="user")
            self.db.save_tone(name, tags, "", self.generated_params)
            self._load_library()
            self.log_message("Tone saved to internal SQLite vault.")

    def load_from_db(self, item):
        tone_id = int(item.text().split(" |")[0])
        tones = self.db.load_all_tones()
        tone = next((t for t in tones if t['id'] == tone_id), None)
        if tone:
            try:
                self.generated_params = json.loads(tone['parameters'])
                self._build_dashboard(self.generated_params)
                self.txt_params.setText(json.dumps(self.generated_params, indent=4))
                self.log_message(f"Restored tone: {tone['name']}")
                self.send_to_device() # Auto push
            except Exception as e:
                self.log_message(f"Corrupt DB dict: {e}")

    def export_patch(self):
        if not self.template_path or not self.generated_params: return
        sn, _ = QFileDialog.getSaveFileName(self, "Export Patch", "Tone.mg400patch")
        if sn:
            enc = BinaryEncoder(self.template_path)
            enc.load_template()
            full_params = self.generated_params.copy()
            full_params["name"] = self.current_patch_name
            enc.apply_parameters(full_params)
            enc.export_patch(sn)
            self.log_message(f"Exported physically: {sn}")

    def send_to_device(self):
        if not self.generated_params: return
        try:
            self.midi.send_patch_name(self.current_patch_name)
            self.midi.send_cc_parameters(self.generated_params, MIDI_CC_MAP)
            self._fire_global_sync(self.generated_params)
            self.log_message(f"Synced '{self.current_patch_name}' to hardware & neural cloud.")
        except Exception as e:
            self.log_message(f"Hardware push fail: {e}")

    def closeEvent(self, event):
        self.midi.close()
        super().closeEvent(event)

