import mido
import logging

class MidiClient:
    def __init__(self, device_name_hint="NUX MG-400"):
        self.device_name_hint = device_name_hint
        self.port_name = None
        self.outport = None

    def find_device(self):
        """Scans available MIDI output ports and attempts to connect to the MG-400."""
        available_ports = mido.get_output_names()
        
        for port in available_ports:
            # We look for a keyword like 'NUX' or 'MG-400'
            if "NUX" in port or "MG400" in port or "MG-400" in port:
                self.port_name = port
                break
                
        if not self.port_name:
            # Just fallback to the first port if testing, or raise an error ideally
            if available_ports:
                logging.warning(f"Could not find exact MG-400 device. Available outputs: {available_ports}")
                # We won't connect strictly unless sure, or we could raise an error:
                raise ConnectionError(f"NUX MG-400 not found. Available MIDI ports out: {available_ports}")
            else:
                raise ConnectionError("No MIDI output ports found on system.")
                
        return self.port_name

    def connect(self):
        """Opens a MIDI out connection."""
        if not self.port_name:
            self.find_device()
            
        try:
            self.outport = mido.open_output(self.port_name)
            logging.info(f"Successfully connected to MIDI port: {self.port_name}")
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to open MIDI port {self.port_name}: {e}")

    def send_cc_parameters(self, params: dict, mapping: dict):
        """
        Transmits Control Change (CC) messages for a dictionary of parameters
        using the provided mapping from string names to exact MIDI CC numbers.
        Ranges are bounded 0-100 logically, but CC accepts 0-127 natively.
        We pass the 0-100 exact parameter scale from AI into the CC value directly.
        """
        if not self.outport:
            self.connect()

        try:
            for key, value in params.items():
                key_lower = key.lower()
                if key_lower in mapping:
                    cc_num = mapping[key_lower]
                    try:
                        # Convert float logic to rigid int scale limit for the protocol
                        int_val = int(round(float(value))) 
                        clamped_val = max(0, min(127, int_val))
                        
                        # Generate CC packet for this specific effect knob
                        msg = mido.Message('control_change', control=cc_num, value=clamped_val)
                        self.outport.send(msg)
                    except (ValueError, TypeError):
                        logging.warning(f"Invalid CC value '{value}' skipped for {key}")
                else:
                    logging.info(f"Skipping CC send: '{key}' mapping not supported for realtime sync.")
                    
            logging.info(f"Successfully swept CC messages to realtime active hardware memory.")
            return True
        except Exception as e:
            raise RuntimeError(f"Error transmitting parameters over MIDI to MG-400: {e}")

    def send_patch_name(self, name: str):
        """
        Transmits the patch identity to the physical MG-400 display 
        via proprietary SysEx command.
        Format: F0 00 20 72 01 07 (Header) 00 00 00 10 (Len) <chars> F7
        """
        if not self.outport:
            try:
                self.connect()
            except:
                return False # Silent fail if not connected

        try:
            # NUX/Cherub SysEx Header (without F0/F7 for mido data)
            # 00 20 72 (Mfr) 01 (Model) 07 (CMD) 00 00 00 10 (ADDR/LEN)
            header = [0x00, 0x20, 0x72, 0x01, 0x07, 0x00, 0x00, 0x00, 0x10]
            
            # ASCII Name Payload (16 byte safe buffer)
            safe_name = name.upper()[:16].ljust(16)
            name_bytes = [ord(c) for c in safe_name]
            
            # Construct and fire
            full_data = header + name_bytes
            msg = mido.Message('sysex', data=full_data)
            self.outport.send(msg)
            logging.info(f"Identity Propagation Successful: Transmitted '{name}' to Hardware.")
            return True
        except Exception as e:
            logging.error(f"Identity Propagation Failed: {e}")
            return False

    def close(self):
        """Closes the MIDI port safely."""
        self.stop_listening()
        if self.outport:
            self.outport.close()
            self.outport = None

    def start_listening(self, callback):
        """Starts a background listener for MIDI input matching the device, executing callback on CC updates."""
        self._listening = True
        self.inport = None
        
        # Try to find an input port with the same name hint
        available_inputs = mido.get_input_names()
        in_port_name = None
        for port in available_inputs:
            if "NUX" in port or "MG400" in port or "MG-400" in port:
                in_port_name = port
                break
                
        if not in_port_name:
            logging.warning("No MIDI input port found for MG-400 sync.")
            return

        def listen_loop():
            try:
                self.inport = mido.open_input(in_port_name)
                logging.info(f"Listening on MIDI input: {in_port_name}")
                for msg in self.inport:
                    if not self._listening:
                        break
                    if msg.type == 'control_change':
                        callback(msg.control, msg.value)
            except Exception as e:
                logging.error(f"MIDI input listener error: {e}")
            finally:
                if self.inport:
                    self.inport.close()

        import threading
        self.listener_thread = threading.Thread(target=listen_loop, daemon=True)
        self.listener_thread.start()

    def stop_listening(self):
        self._listening = False
        if hasattr(self, 'inport') and self.inport:
            self.inport.close()
