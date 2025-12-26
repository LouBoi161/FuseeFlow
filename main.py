import sys
import os
import shutil
import subprocess
import usb.core
import random
import json
import urllib.request
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QMessageBox, QComboBox, QProgressBar, QAbstractItemView,
    QCheckBox, QTextEdit, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QByteArray, QTimer, QRectF
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QPainter, QColor

# ----------------- Constants -----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RCM_VENDOR_ID = 0x0955
RCM_PRODUCT_ID = 0x7321
FUSEE_NANO_PATH = shutil.which("fusee-nano") or os.path.join(BASE_DIR, "fusee-nano") or os.path.expanduser("~/bin/fusee-nano")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
PAYLOADS_DIR = os.path.join(BASE_DIR, "payloads")
HEKATE_API_URL = "https://api.github.com/repos/CTCaer/hekate/releases/latest"

# ----------------- Stylesheet (QSS) -----------------
DARK_THEME = """
QWidget#MainWindow, QWidget#LogContainer { background-color: #2E3440; }
QLabel { color: #ECEFF4; font-size: 14px; }
QLabel#StatusLabel { font-size: 18px; font-weight: bold; }
QLabel#ActivePayloadLabel { color: #88C0D0; font-style: italic; }
QComboBox { background-color: #4C566A; color: #ECEFF4; border: 1px solid #3B4252; padding: 5px 10px; border-radius: 5px; }
QComboBox:hover { background-color: #5E81AC; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 25px; border-left-width: 1px; border-left-color: #3B4252; border-left-style: solid; border-top-right-radius: 5px; border-bottom-right-radius: 5px; }
QComboBox::down-arrow { image: url(arrow_down.svg); width: 14px; height: 14px; }
QComboBox::down-arrow:on { image: url(arrow_right.svg); }
QComboBox QAbstractItemView { background-color: #4C566A; color: #ECEFF4; selection-background-color: #5E81AC; border: 1px solid #3B4252; }
QPushButton { background-color: #4C566A; color: #ECEFF4; border: none; padding: 10px 20px; font-size: 14px; border-radius: 15px; }
QPushButton#LoadFileButton, QPushButton#DownloadButton, QPushButton#AddPayloadButton, QPushButton#ThemeButton, QPushButton#OpenFolderButton, QPushButton#InfoButton { padding: 5px 10px; }
QPushButton:hover { background-color: #5E81AC; }
QPushButton:pressed { background-color: #81A1C1; }
QPushButton:disabled { background-color: #3B4252; color: #4C566A; }
QPushButton#BigInjectButton { font-size: 24px; font-weight: bold; border-radius: 40px; }
QProgressBar { border: 1px solid #4C566A; border-radius: 5px; text-align: center; color: #ECEFF4; }
QProgressBar::chunk { background-color: #A3BE8C; border-radius: 5px; }
QCheckBox { color: #ECEFF4; spacing: 5px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 3px; border: 1px solid #4C566A; background-color: #3B4252; }
QCheckBox::indicator:checked { background-color: #A3BE8C; }
QTextEdit { background-color: #3B4252; color: #ECEFF4; border: 1px solid #4C566A; border-radius: 5px; font-family: monospace; }
QTabWidget::pane { border: 1px solid #4C566A; border-radius: 5px; }
QTabBar::tab { background: #3B4252; color: #ECEFF4; padding: 10px 20px; border-top-left-radius: 5px; border-top-right-radius: 5px; margin-right: 2px; }
QTabBar::tab:selected { background: #4C566A; font-weight: bold; border-bottom: 2px solid #88C0D0; }
"""

LIGHT_THEME = """
QWidget#MainWindow, QWidget#LogContainer { background-color: #ECEFF4; }
QLabel { color: #2E3440; font-size: 14px; }
QLabel#StatusLabel { font-size: 18px; font-weight: bold; }
QLabel#ActivePayloadLabel { color: #5E81AC; font-style: italic; }
QComboBox { background-color: #D8DEE9; color: #2E3440; border: 1px solid #BCC6D9; padding: 5px 10px; border-radius: 5px; }
QComboBox:hover { background-color: #E5E9F0; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right; width: 25px; border-left-width: 1px; border-left-color: #BCC6D9; border-left-style: solid; border-top-right-radius: 5px; border-bottom-right-radius: 5px; }
QComboBox::down-arrow { image: url(arrow_down_dark.svg); width: 14px; height: 14px; }
QComboBox::down-arrow:on { image: url(arrow_right_dark.svg); }
QComboBox QAbstractItemView { background-color: #D8DEE9; color: #2E3440; selection-background-color: #88C0D0; border: 1px solid #BCC6D9; }
QPushButton { background-color: #D8DEE9; color: #2E3440; border: 1px solid #BCC6D9; padding: 10px 20px; font-size: 14px; border-radius: 15px; }
QPushButton#LoadFileButton, QPushButton#DownloadButton, QPushButton#AddPayloadButton, QPushButton#ThemeButton, QPushButton#OpenFolderButton, QPushButton#InfoButton { padding: 5px 10px; }
QPushButton:hover { background-color: #E5E9F0; }
QPushButton:pressed { background-color: #ECEFF4; }
QPushButton:disabled { background-color: #E5E9F0; color: #9CA6B9; border: 1px solid #D8DEE9; }
QPushButton#BigInjectButton { font-size: 24px; font-weight: bold; border-radius: 40px; }
QProgressBar { border: 1px solid #BCC6D9; border-radius: 5px; text-align: center; color: #2E3440; }
QProgressBar::chunk { background-color: #A3BE8C; border-radius: 5px; }
QCheckBox { color: #2E3440; spacing: 5px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 3px; border: 1px solid #BCC6D9; background-color: #ECEFF4; }
QCheckBox::indicator:checked { background-color: #A3BE8C; }
QTextEdit { background-color: #E5E9F0; color: #2E3440; border: 1px solid #BCC6D9; border-radius: 5px; font-family: monospace; }
QTabWidget::pane { border: 1px solid #BCC6D9; border-radius: 5px; }
QTabBar::tab { background: #E5E9F0; color: #2E3440; padding: 10px 20px; border-top-left-radius: 5px; border-top-right-radius: 5px; margin-right: 2px; }
QTabBar::tab:selected { background: #D8DEE9; font-weight: bold; border-bottom: 2px solid #5E81AC; }
"""

# ----------------- Custom Widgets -----------------
class CustomComboBox(QComboBox):
    def showPopup(self):
        super().showPopup()
        popup = self.view()
        
        # Force the popup to appear below the combobox
        if popup and popup.parentWidget():
            global_pos = self.mapToGlobal(self.rect().bottomLeft())
            popup.parentWidget().move(global_pos)

        # Scroll so the current item is at the top
        index = self.model().index(self.currentIndex(), 0)
        if index.isValid():
            popup.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtTop)

class DropOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label = QLabel("DROP PAYLOAD HERE")
        self.label.setStyleSheet("""
            QLabel {
                color: #ECEFF4;
                font-size: 24px;
                font-weight: bold;
                background-color: rgba(46, 52, 64, 200);
                border: 3px dashed #A3BE8C;
                border-radius: 20px;
                padding: 40px;
            }
        """)
        layout.addWidget(self.label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150)) # Semi-transparent dark background

class ConfettiOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.pieces = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_positions)
        self.colors = [QColor(c) for c in ["#88C0D0", "#81A1C1", "#5E81AC", "#BF616A", "#D08770", "#EBCB8B", "#A3BE8C", "#B48EAD"]]

    def start(self, duration=3000):
        self.pieces = []
        parent_rect = self.parent().rect()
        for _ in range(150):
            self.pieces.append({
                'rect': QRectF(random.uniform(0, parent_rect.width()), random.uniform(-parent_rect.height(), 0), random.uniform(8, 12), random.uniform(10, 15)),
                'vx': random.uniform(-2, 2), 'vy': random.uniform(3, 6), 'color': random.choice(self.colors)
            })
        if not self.timer.isActive(): self.timer.start(16)
        self.show(); self.raise_(); QTimer.singleShot(duration, self.stop)

    def stop(self):
        self.timer.stop(); self.pieces = []; self.hide()

    def _update_positions(self):
        parent_height = self.parent().rect().height()
        for piece in self.pieces:
            piece['rect'].translate(piece['vx'], piece['vy'])
            if piece['rect'].top() > parent_height: piece['rect'].moveBottom(0)
        self.update()

    def paintEvent(self, event):
        if not self.pieces: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for piece in self.pieces:
            painter.setBrush(piece['color']); painter.setPen(Qt.PenStyle.NoPen); painter.drawRect(piece['rect'])

# ----------------- Worker Threads -----------------
class UsbWorker(QThread):
    device_status = pyqtSignal(bool)
    def run(self):
        while not self.isInterruptionRequested():
            try:
                device = usb.core.find(idVendor=RCM_VENDOR_ID, idProduct=RCM_PRODUCT_ID)
                self.device_status.emit(device is not None)
            except usb.core.NoBackendError:
                print("Warning: No libusb backend found. USB detection disabled.")
                self.device_status.emit(False)
                break
            self.msleep(1000)

class HekateDownloader(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def run(self):
        try:
            with urllib.request.urlopen(HEKATE_API_URL) as response:
                if response.status != 200: self.error.emit(f"API Error: Status {response.status}"); return
                data = json.load(response)
            
            asset_url, asset_name = None, None
            for asset in data.get('assets', []):
                if asset['name'].startswith('hekate_ctcaer_') and asset['name'].endswith('.bin'):
                    asset_url, asset_name = asset['browser_download_url'], asset['name']
                    break
            
            if not asset_url: self.error.emit("Could not find Hekate .bin file in the latest release."); return
            
            if not os.path.exists(PAYLOADS_DIR): os.makedirs(PAYLOADS_DIR)
            for item in os.listdir(PAYLOADS_DIR):
                if item.startswith('hekate_ctcaer_'): os.remove(os.path.join(PAYLOADS_DIR, item))
            
            save_path = os.path.join(PAYLOADS_DIR, asset_name)
            
            def report_hook(count, block_size, total_size): self.progress.emit(int(count * block_size * 100 / total_size))
            urllib.request.urlretrieve(asset_url, save_path, reporthook=report_hook)
            self.finished.emit(asset_name)

        except Exception as e: self.error.emit(f"An unexpected error occurred: {e}")


# ----------------- Main Application Window -----------------
class SwitchInjectorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_ready = False
        self.payload_path = None
        self.config = {"last_payload": "", "dark_mode": True, "auto_inject": False, "favorites": [], "simple_mode": False}
        self.is_dark_mode = True
        self.is_simple_mode = False
        self.last_usb_status = False
        
        self.setWindowTitle("FuseeFlow")
        self.resize(900, 600)
        self.setAcceptDrops(True)
        
        self.central_widget = QWidget(self); self.central_widget.setObjectName("MainWindow")
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # --- Top Bar (Status + Theme) ---
        top_bar = QHBoxLayout()
        self.status_icon_widget = QSvgWidget(); self.status_icon_widget.setFixedSize(48, 48)
        self.status_label = QLabel("Status: Checking..."); self.status_label.setObjectName("StatusLabel")
        
        self.open_folder_btn = QPushButton("📂"); self.open_folder_btn.setObjectName("OpenFolderButton"); self.open_folder_btn.setFixedSize(30, 30); self.open_folder_btn.clicked.connect(self.open_payload_folder)
        self.open_folder_btn.setToolTip("Open Payloads Folder")

        self.info_button = QPushButton("i"); self.info_button.setObjectName("InfoButton"); self.info_button.setFixedSize(30, 30); self.info_button.clicked.connect(self.show_info)
        self.info_button.setToolTip("Show Information")

        self.theme_button = QPushButton("☀"); self.theme_button.setObjectName("ThemeButton"); self.theme_button.setFixedSize(30, 30); self.theme_button.clicked.connect(self.toggle_theme)
        
        top_bar.addWidget(self.status_icon_widget); top_bar.addWidget(self.status_label); top_bar.addStretch(); top_bar.addWidget(self.open_folder_btn); top_bar.addWidget(self.info_button); top_bar.addWidget(self.theme_button)
        
        # --- Tabs ---
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # === Advanced Tab ===
        self.tab_advanced = QWidget()
        adv_layout = QVBoxLayout(self.tab_advanced)
        
        # Payload Selection
        self.payload_combobox = CustomComboBox()
        self.payload_combobox.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.payload_combobox.customContextMenuRequested.connect(self.show_context_menu)
        self.payload_combobox.currentTextChanged.connect(self.on_payload_selected_from_dropdown)
        
        # Actions Row
        adv_actions = QHBoxLayout()
        self.add_payload_btn = QPushButton("Add Payload"); self.add_payload_btn.clicked.connect(self.add_payload_to_library)
        self.load_file_btn = QPushButton("Load File..."); self.load_file_btn.clicked.connect(self.select_payload_from_file)
        self.get_hekate_btn_adv = QPushButton("Get Hekate"); self.get_hekate_btn_adv.clicked.connect(self.start_hekate_download)
        adv_actions.addWidget(self.add_payload_btn); adv_actions.addWidget(self.load_file_btn); adv_actions.addWidget(self.get_hekate_btn_adv)
        
        # Options Row
        adv_options = QHBoxLayout()
        self.auto_inject_checkbox = QCheckBox("Auto-Inject when RCM detected")
        self.auto_inject_checkbox.stateChanged.connect(self.on_auto_inject_toggled)
        self.check_udev_btn_adv = QPushButton("Check Permissions"); self.check_udev_btn_adv.clicked.connect(self.check_udev_rules)
        adv_options.addWidget(self.auto_inject_checkbox); adv_options.addStretch(); adv_options.addWidget(self.check_udev_btn_adv)
        
        # Inject Button & Label
        self.active_payload_label = QLabel("No payload selected."); self.active_payload_label.setObjectName("ActivePayloadLabel"); self.active_payload_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inject_btn_adv = QPushButton("INJECT PAYLOAD"); self.inject_btn_adv.setMinimumHeight(50); self.inject_btn_adv.clicked.connect(self.inject_payload)
        
        adv_layout.addWidget(QLabel("Select Payload:"))
        adv_layout.addWidget(self.payload_combobox)
        adv_layout.addLayout(adv_actions)
        adv_layout.addSpacing(10)
        adv_layout.addLayout(adv_options)
        adv_layout.addSpacing(10)
        adv_layout.addWidget(self.active_payload_label)
        adv_layout.addWidget(self.inject_btn_adv)
        adv_layout.addStretch()
        
        # === Simple Tab ===
        self.tab_simple = QWidget()
        simple_layout = QVBoxLayout(self.tab_simple)
        simple_layout.setSpacing(20)
        simple_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.inject_btn_simple = QPushButton("INJECT HEKATE"); self.inject_btn_simple.setMinimumHeight(80); self.inject_btn_simple.setMinimumWidth(250)
        self.inject_btn_simple.setObjectName("BigInjectButton")
        self.inject_btn_simple.clicked.connect(self.inject_payload)
        
        self.get_hekate_btn_simple = QPushButton("Get Latest Hekate"); self.get_hekate_btn_simple.setMinimumWidth(200); self.get_hekate_btn_simple.clicked.connect(self.start_hekate_download)
        self.check_udev_btn_simple = QPushButton("Check USB Permissions"); self.check_udev_btn_simple.setMinimumWidth(200); self.check_udev_btn_simple.clicked.connect(self.check_udev_rules)
        
        self.auto_inject_checkbox_simple = QCheckBox("Auto-Inject")
        self.auto_inject_checkbox_simple.stateChanged.connect(self.on_auto_inject_toggled)

        simple_layout.addStretch()
        simple_layout.addWidget(self.inject_btn_simple, 0, Qt.AlignmentFlag.AlignCenter)
        simple_layout.addSpacing(20)
        simple_layout.addWidget(self.get_hekate_btn_simple, 0, Qt.AlignmentFlag.AlignCenter)
        simple_layout.addWidget(self.check_udev_btn_simple, 0, Qt.AlignmentFlag.AlignCenter)
        simple_layout.addSpacing(10)
        simple_layout.addWidget(self.auto_inject_checkbox_simple, 0, Qt.AlignmentFlag.AlignCenter)
        simple_layout.addStretch()

        # Add tabs
        self.tabs.addTab(self.tab_advanced, "Advanced")
        self.tabs.addTab(self.tab_simple, "Simple")

        # --- Shared Bottom ---
        self.progress_bar = QProgressBar(); self.progress_bar.hide()

        # --- Assemble Main Layout ---
        self.main_layout.addLayout(top_bar)
        self.main_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.progress_bar)
        
        # --- Initial State ---
        self.load_config()
        self.scan_and_populate_payloads()
        self.apply_config_state()
        self.render_joycon_svg("#D08770")
        self.start_usb_worker()
        self.update_status(False)
        
        self.confetti_overlay = ConfettiOverlay(self.central_widget); self.confetti_overlay.hide()
        self.drop_overlay = DropOverlay(self.central_widget)
        self.config_ready = True
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.drop_overlay.show()
            self.drop_overlay.raise_()
            event.accept()
        else: event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_overlay.hide()

    def dropEvent(self, event):
        self.drop_overlay.hide()
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.endswith('.bin'):
                self.add_payload_to_library(f)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.confetti_overlay.setGeometry(self.central_widget.rect())
        self.drop_overlay.setGeometry(self.central_widget.rect())

    def log(self, message, type="info"):
        print(f"[{type.upper()}] {message}")

    def on_tab_changed(self, index):
        # Index 0 is Advanced, Index 1 is Simple
        self.is_simple_mode = (index == 1)
        self.save_config()
    
    def on_auto_inject_toggled(self, state):
        # Sync both checkboxes
        is_checked = (state == 2) # Qt.CheckState.Checked
        self.auto_inject_checkbox.setChecked(is_checked)
        self.auto_inject_checkbox_simple.setChecked(is_checked)
        self.save_config()

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        self.save_config()

    def apply_theme(self):
        app = QApplication.instance()
        app.setStyleSheet(DARK_THEME if self.is_dark_mode else LIGHT_THEME)
        self.theme_button.setText("☀" if self.is_dark_mode else "☾")
        self.render_joycon_svg("#A3BE8C" if "DETECTED" in self.status_label.text() else "#BF616A") # Refresh Icon color

    def show_context_menu(self, pos):
        # Implementation for context menu later
        pass

    def check_udev_rules(self):
        # Check specific rule existence or simple read access
        try:
            # Simple check: can we open a device? 
            # Or check file existence
            if os.path.exists("/etc/udev/rules.d/50-switch.rules") or os.path.exists("/lib/udev/rules.d/50-switch.rules"):
                 self.log("Udev rules seem to be present.", "success")
            else:
                 self.log("Udev rules not found! You might need them for USB access without sudo.", "error")
                 cmd = 'echo \'SUBSYSTEM=="usb", ATTRS{idVendor}=="0955", ATTRS{idProduct}=="7321", MODE="0666"\' | sudo tee /etc/udev/rules.d/50-switch.rules && sudo udevadm control --reload-rules && sudo udevadm trigger'
                 self.log(f"Run this in terminal:\n{cmd}", "info")
                 QMessageBox.information(self, "Udev Rules Missing", f"To fix USB permissions, run this in your terminal:\n\n{cmd}")
        except Exception as e:
            self.log(f"Error checking rules: {e}", "error")

    def add_payload_to_library(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select payload", os.path.expanduser("~"), "Binary files (*.bin);;All files (*.*)")
        
        if file_path and os.path.exists(file_path):
            try:
                if not os.path.exists(PAYLOADS_DIR): os.makedirs(PAYLOADS_DIR)
                target_path = os.path.join(PAYLOADS_DIR, os.path.basename(file_path))
                if os.path.abspath(file_path) != os.path.abspath(target_path):
                    shutil.copy2(file_path, target_path)
                self.scan_and_populate_payloads()
                self.payload_combobox.setCurrentText(os.path.basename(file_path))
                self.log(f"Added '{os.path.basename(file_path)}' to library.", "success")
            except Exception as e:
                self.log(f"Could not copy file: {e}", "error")

    def open_payload_folder(self):
        if not os.path.exists(PAYLOADS_DIR): os.makedirs(PAYLOADS_DIR)
        try:
            subprocess.Popen(['xdg-open', PAYLOADS_DIR])
        except Exception as e:
            self.log(f"Could not open folder: {e}", "error")

    def show_info(self):
        info_text = """
        <h3>Switch Payload Injector - Help</h3>
        <p><b>Modes:</b>
        <ul>
            <li><b>Simple:</b> One-click injection for Hekate. Ideal for most users.</li>
            <li><b>Advanced:</b> Manage multiple payloads and select custom files.</li>
        </ul></p>
        <p><b>Features:</b>
        <ul>
            <li><b>Auto-Inject:</b> Automatically injects the selected payload as soon as an RCM device is detected.</li>
            <li><b>Drag & Drop:</b> Drag any .bin file onto the window to add it to your library.</li>
            <li><b>Get Hekate:</b> Downloads the latest version of Hekate directly from GitHub.</li>
        </ul></p>
        <p><b>Permissions:</b> If the status stays on 'Waiting...' despite the Switch being connected in RCM, click 'Check Permissions' to fix Linux USB access rules.</p>
        """
        QMessageBox.information(self, "Information", info_text)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e: print(f"Config load error: {e}")
    
    def apply_config_state(self):
        self.is_dark_mode = self.config.get("dark_mode", True)
        self.apply_theme()
        
        self.is_simple_mode = self.config.get("simple_mode", False)
        self.tabs.setCurrentIndex(1 if self.is_simple_mode else 0)
        
        auto_inject = self.config.get("auto_inject", False)
        self.auto_inject_checkbox.setChecked(auto_inject)
        self.auto_inject_checkbox_simple.setChecked(auto_inject)
        
        last = self.config.get("last_payload", "")
        if last and self.payload_combobox.findText(last) != -1:
            self.payload_combobox.setCurrentText(last)

    def save_config(self):
        if not self.config_ready: return
        self.config["last_payload"] = self.payload_combobox.currentText()
        self.config["dark_mode"] = self.is_dark_mode
        self.config["simple_mode"] = self.is_simple_mode
        self.config["auto_inject"] = self.auto_inject_checkbox.isChecked()
        try:
            with open(CONFIG_FILE, "w") as f: json.dump(self.config, f)
        except Exception as e: print(f"Config save error: {e}")

    def start_hekate_download(self):
        self.get_hekate_btn_adv.setEnabled(False)
        self.get_hekate_btn_simple.setEnabled(False)
        self.progress_bar.setValue(0); self.progress_bar.show()
        self.downloader = HekateDownloader()
        self.downloader.finished.connect(self.on_download_finished); self.downloader.error.connect(self.on_download_error); self.downloader.progress.connect(self.on_download_progress)
        self.downloader.start()

    def on_download_progress(self, percent): self.progress_bar.setValue(percent)

    def on_download_finished(self, filename):
        self.get_hekate_btn_adv.setEnabled(True)
        self.get_hekate_btn_simple.setEnabled(True)
        self.progress_bar.hide()
        self.log(f"Successfully downloaded '{filename}'.", "success")
        self.show_temporary_status("DOWNLOAD COMPLETE!", "#A3BE8C")
        self.scan_and_populate_payloads(); self.payload_combobox.setCurrentText(filename)

    def on_download_error(self, message):
        self.get_hekate_btn_adv.setEnabled(True)
        self.get_hekate_btn_simple.setEnabled(True)
        self.progress_bar.hide()
        self.log(f"Download Failed: {message}", "error")
        self.show_temporary_status("DOWNLOAD FAILED!", "#BF616A")

    def scan_and_populate_payloads(self):
        self.payload_combobox.clear()
        if not os.path.exists(PAYLOADS_DIR): os.makedirs(PAYLOADS_DIR)
        payloads = sorted([f for f in os.listdir(PAYLOADS_DIR) if f.endswith('.bin')])
        if payloads:
            self.payload_combobox.setEnabled(True); self.payload_combobox.addItems(payloads)
        else:
            self.payload_combobox.addItem("No payloads in 'payloads' folder"); self.payload_combobox.setEnabled(False)

    def on_payload_selected_from_dropdown(self, payload_name):
        if "No payloads" in payload_name or not payload_name:
            self.payload_path = None; self.active_payload_label.setText("No payload selected.")
        else:
            self.payload_path = os.path.join(PAYLOADS_DIR, payload_name); self.active_payload_label.setText(f"Active: {payload_name}")
        self.save_config(); self.update_inject_button_state()



    def select_payload_from_file(self):
        initial_dir = os.path.dirname(self.payload_path) if self.payload_path and os.path.exists(os.path.dirname(self.payload_path)) else PAYLOADS_DIR
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a payload file", initial_dir, "Binary files (*.bin);;All files (*.*)")
        if file_path:
            self.payload_path = file_path; self.active_payload_label.setText(f"Active (external): {os.path.basename(file_path)}"); self.update_inject_button_state()

    def render_joycon_svg(self, color):
        try:
            with open('joycon.svg', 'r') as f: svg_data = f.read()
            modified_svg_data = svg_data.replace('#000000', color)
            self.status_icon_widget.load(QByteArray(modified_svg_data.encode('utf-8')))
        except Exception as e: print(f"Failed to render SVG: {e}")

    def start_usb_worker(self):
        self.usb_thread = UsbWorker(self); self.usb_thread.device_status.connect(self.update_status); self.usb_thread.start()

    def update_status(self, found):
        if hasattr(self, '_status_override') and self._status_override:
            return

        if found:
            self.status_label.setText("Status: Switch DETECTED!"); self.render_joycon_svg("#A3BE8C")
            if not self.last_usb_status and self.auto_inject_checkbox.isChecked():
                self.log("Auto-injecting payload...", "info")
                QTimer.singleShot(500, self.inject_payload) # Small delay to ensure connection stability
        else:
            self.status_label.setText("Status: Waiting for Switch..."); self.render_joycon_svg("#BF616A")
        
        self.last_usb_status = found
        self.status_label.setStyleSheet(f"color: {'#A3BE8C' if found else '#BF616A'}; font-size: 18px; font-weight: bold;")
        self.update_inject_button_state()

    def show_temporary_status(self, message, color, duration=3000):
        self._status_override = True
        old_text = self.status_label.text()
        old_style = self.status_label.styleSheet()
        
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        
        def reset_status():
            self._status_override = False
            self.update_status(self.last_usb_status)
            
        QTimer.singleShot(duration, reset_status)

    def update_inject_button_state(self):
        device_found = "DETECTED" in self.status_label.text()
        payload_selected = self.payload_path is not None and os.path.exists(self.payload_path)
        self.inject_btn_adv.setEnabled(device_found and payload_selected)
        # Simple mode button is always enabled (it will check for hekate on click)
        self.inject_btn_simple.setEnabled(device_found)
        
    def inject_payload(self):
        payload_to_inject = self.payload_path

        if self.is_simple_mode:
            # Find Hekate in payloads folder
            if os.path.exists(PAYLOADS_DIR):
                candidates = [f for f in os.listdir(PAYLOADS_DIR) if f.lower().startswith('hekate') and f.endswith('.bin')]
                if candidates:
                    # Sort to get latest (assuming version naming or date) - naive sort
                    candidates.sort(reverse=True)
                    payload_to_inject = os.path.join(PAYLOADS_DIR, candidates[0])
                else:
                    self.log("Hekate payload not found in library! Please click 'Get Hekate'.", "error")
                    QMessageBox.warning(self, "Hekate Not Found", "Could not find a Hekate payload in your library.\nPlease use the 'Get Hekate' button to download it.")
                    return
            else:
                 self.log("Payloads directory missing.", "error"); return

        if not payload_to_inject or not os.path.exists(payload_to_inject): self.log("Selected payload not found.", "error"); return
        if not os.path.exists(FUSEE_NANO_PATH): self.log(f"fusee-nano not found at: {FUSEE_NANO_PATH}", "error"); return
        
        self.log(f"Injecting {os.path.basename(payload_to_inject)}...", "info")
        try:
            process = subprocess.Popen([FUSEE_NANO_PATH, payload_to_inject], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            if process.returncode == 0: 
                self.confetti_overlay.start()
                self.log("Payload injected successfully!", "success")
                self.show_temporary_status("INJECTION SUCCESSFUL!", "#A3BE8C")
                if stdout.strip(): self.log(stdout, "info")
            else: 
                self.log("Injection Failed.", "error")
                self.show_temporary_status("INJECTION FAILED!", "#BF616A")
                self.log(stderr, "error")
        except Exception as e: 
            self.log(f"Execution Error: {e}", "error")

    def on_download_finished(self, filename):
        self.get_hekate_btn_adv.setEnabled(True)
        self.get_hekate_btn_simple.setEnabled(True)
        self.progress_bar.hide()
        self.log(f"Successfully downloaded '{filename}'.", "success")
        self.show_temporary_status("DOWNLOAD COMPLETE!", "#A3BE8C")
        self.scan_and_populate_payloads(); self.payload_combobox.setCurrentText(filename)

    def on_download_error(self, message):
        self.get_hekate_btn_adv.setEnabled(True)
        self.get_hekate_btn_simple.setEnabled(True)
        self.progress_bar.hide()
        self.log(f"Download Failed: {message}", "error")
        self.show_temporary_status("DOWNLOAD FAILED!", "#BF616A")

    def load_last_payload(self):
        # Deprecated by load_config, keeping empty for safety or removing calls
        pass

    def save_last_payload(self):
        self.save_config()

                
    def closeEvent(self, event):
        self.usb_thread.requestInterruption(); self.usb_thread.wait(); event.accept()

# ----------------- Run Application -----------------
def run_in_new_terminal():
    # Check if we have already relaunched in a new terminal to avoid loops
    if os.environ.get("SWITCH_INJECTOR_TERMINAL") == "1":
        return

    # List of terminal emulators to try [executable, flag_to_execute_command]
    terminals = [
        ["gnome-terminal", "--"],
        ["konsole", "-e"],
        ["xfce4-terminal", "-e"],
        ["x-terminal-emulator", "-e"],
        ["xterm", "-e"]
    ]

    script_path = os.path.abspath(__file__)
    env = os.environ.copy()
    env["SWITCH_INJECTOR_TERMINAL"] = "1"

    # Wrap execution in bash to keep window open after exit/crash
    inner_cmd = f"'{sys.executable}' '{script_path}'; echo; echo 'Press Enter to close terminal...'; read"

    for term_cmd in terminals:
        term_exe = term_cmd[0]
        term_flag = term_cmd[1]
        
        if shutil.which(term_exe):
            # Construct command: terminal -e bash -c "python ...; read"
            cmd = [term_exe, term_flag, "bash", "-c", inner_cmd]
            try:
                subprocess.Popen(cmd, env=env)
                sys.exit(0) # Exit this instance, the new terminal will take over
            except Exception as e:
                print(f"Failed to launch {term_exe}: {e}")
                continue

if __name__ == "__main__":
    # Attempt to open in a new terminal window for logs
    run_in_new_terminal()
    
    app = QApplication(sys.argv)
    window = SwitchInjectorApp()
    window.show()
    sys.exit(app.exec())
