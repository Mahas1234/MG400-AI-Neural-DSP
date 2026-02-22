import sys
from PySide6.QtWidgets import QApplication, QMessageBox
import logging

from core.config import ConfigManager
from core.logger import setup_logger
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    
    # Init Production Data Persistence Managers
    config_mgr = ConfigManager()
    
    # Init Local Log Stream Outputting mechanism
    logger = setup_logger(config_mgr.get("log_level", "INFO"))
    
    logger.info("Initializing MG400 AI Patch Generator boot sequence...")
    
    # Create the window structure with bound hooks
    window = MainWindow(config_mgr=config_mgr, logger=logger)
    window.show()

    logger.info("System fully initialized. Everything is ready.")

    # 2. Main PySide6 execution loop running logic cleanly
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
