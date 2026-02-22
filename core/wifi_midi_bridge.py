import sys
import json
import mido

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 wifi_midi_bridge.py <json_payload>")
        sys.exit(1)
        
    try:
        data = json.loads(sys.argv[1])
    except Exception as e:
        print(f"JSON Parsing Error: {e}")
        sys.exit(1)
        
    outport_name = None
    for port in mido.get_output_names():
        if "NUX" in port or "MG400" in port or "MG-400" in port:
            outport_name = port
            break
            
    if not outport_name:
        print("MG-400 is not plugged into the Mac via USB.")
        sys.exit(1)
        
    try:
        with mido.open_output(outport_name) as port:
            for cc_num, value in data.items():
                port.send(mido.Message('control_change', channel=0, control=int(cc_num), value=int(value)))
        print("Success")
    except Exception as e:
        print(f"MIDI Port Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
