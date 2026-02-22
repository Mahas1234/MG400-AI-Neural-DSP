import os
import logging
from typing import Dict, Any
from .param_mapping import OFFSET_MAP

class BinaryEncoder:
    """
    Binary encoder for MG400 patch files.
    Loads a base template patch, modifies bytes targeting specific offsets, 
    and handles byte generation within safe thresholds (0-127).
    """
    def __init__(self, template_path: str):
        self.template_path = template_path
        self.patch_data = bytearray()
        
    def load_template(self) -> None:
        """Loads binary data from the .mg400patch base template file."""
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template patch file not found: {self.template_path}")
            
        try:
            with open(self.template_path, "rb") as f:
                self.patch_data = bytearray(f.read())
        except IOError as e:
            raise RuntimeError(f"Error reading the template patch binary: {e}")
            
    def get_parameters(self) -> Dict[str, Any]:
        """Reads parameter values mapped directly from the current patch layout memory bytes."""
        if not self.patch_data:
            return {}
        
        parsed = {}
        for key, offset in OFFSET_MAP.items():
            if offset < len(self.patch_data):
                parsed[key] = self.patch_data[offset]
        return parsed
            
    def apply_parameters(self, params: Dict[str, Any]) -> None:
        """
        Modifies the binary bytearray based on the given parameter dict mapped to OFFSET_MAP.
        Ensures all byte values are securely clamped between 0 and 127.
        """
        if not self.patch_data:
            raise ValueError("Template logic error: Base patch not loaded yet. Call load_template() first.")
            
        data_len = len(self.patch_data)
        
        for key, value in params.items():
            key_lower = key.lower()
            
            # Map keyword into OFFSET list. e.g. delay_time -> 0x30
            if key_lower in OFFSET_MAP:
                offset_idx = OFFSET_MAP[key_lower]
                
                try:
                    # Sanitize parameter data type parsing (e.g. string numbers to floats and cast to nearest int)
                    int_val = int(round(float(value))) 
                    
                    # Ensure strict byte-safety constraint limits: min 0, max 127
                    clamped_byte_val = max(0, min(127, int_val))
                    
                    if offset_idx < data_len:
                        self.patch_data[offset_idx] = clamped_byte_val
                    else:
                        logging.warning(f"Offset index {offset_idx} is out of bounds for patched parameter '{key}'. Ignored.")
                except (ValueError, TypeError):
                    logging.error(f"Invalid integer formatting '{value}' passed for parameter '{key}'. Ignored.")
            else:
                logging.info(f"Parameter semantic '{key}' not found in OFFSET_MAP mappings. Excluded from patch encoding.")
                
    def export_patch(self, output_path: str) -> None:
        """Exports the modified binary bytearray safely to an external valid .mg400patch file."""
        if not self.patch_data:
            raise ValueError("Export execution error: Patch memory is empty.")
            
        out_dir = os.path.dirname(output_path)
        if out_dir and not os.path.exists(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
            except OSError as e:
                raise RuntimeError(f"Failed to initialize export patch directory {out_dir}: {e}")
                
        try:
            with open(output_path, "wb") as f:
                f.write(self.patch_data)
        except IOError as e:
            raise RuntimeError(f"Unknown logic error occured while generating exported custom patch file: {e}")
