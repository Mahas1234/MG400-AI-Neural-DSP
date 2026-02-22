import logging
import sys
from pathlib import Path
from .config import APP_DIR

def setup_logger(log_level_str="INFO"):
    """Configures persistent logging out to the ~/.mg400ai/app.log tracking file and stdout."""
    log_file = APP_DIR / "app.log"
    
    level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    logger = logging.getLogger("MG400AI")
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        # File handler to persist warnings and usage events
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(level)
        
        # Console output for dev and trailing output
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
    return logger
