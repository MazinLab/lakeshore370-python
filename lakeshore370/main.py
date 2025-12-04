#!/usr/bin/env python3
"""
Main interface for Lakeshore370 AC Resistance Bridge Driver 
"""

import argparse
import serial
from .temperature import TemperatureReader

def main():
    parser = argparse.ArgumentParser(description="Lakeshore 370 AC Resistance Bridge Controller")
    
    # Device information
    parser.add_argument("--info", action="store_true", help="Get device information")
    
    # Reading arguments
    parser.add_argument("--read-temp", type=int, metavar='INPUT', help="Read temperature from input: --read-temp <input_num>")
    parser.add_argument("--read-resistance", type=int, metavar='INPUT', help="Read resistance from input: --read-resistance <input_num>")
    parser.add_argument("--read-status", type=int, metavar='INPUT', help="Read status from input: --read-status <input_num>")
    parser.add_argument("--scan", nargs='*', metavar='INPUT', help="Scan multiple inputs: --scan [1 2 3 4 5] (default: 1-5)")
    parser.add_argument("--all", action="store_true", help="Read all inputs (1-16)")
    
    # Serial communication settings
    parser.add_argument("--port", default="/dev/ttyUSB4", help="Serial port (default: /dev/ttyUSB4)")
    parser.add_argument("--baudrate", type=int, default=9600, choices=[300, 1200, 9600], help="Baud rate (default: 9600)")
    parser.add_argument("--get-baud", action="store_true", help="Get current baud rate setting")
    parser.add_argument("--set-baud", type=int, choices=[0, 1, 2], help="Set baud rate: 0=300, 1=1200, 2=9600")
    
    args = parser.parse_args()

    try:
        temp_reader = TemperatureReader(port=args.port, baudrate=args.baudrate)

        # Device information
        if args.info:
            print("Device Information:")
            identification = temp_reader.get_identification()
            baud_rate = temp_reader.get_baud_rate()
            print(f"  ID: {identification}")
            print(f"  Baud Rate Code: {baud_rate} (0=300, 1=1200, 2=9600)")
            print()

        # Baud rate operations
        if args.get_baud:
            baud_code = temp_reader.get_baud_rate()
            baud_map = {"0": "300", "1": "1200", "2": "9600"}
            baud_str = baud_map.get(baud_code, f"Unknown ({baud_code})")
            print(f"Current baud rate: {baud_str} baud (code: {baud_code})")

        if args.set_baud is not None:
            print(f"Setting baud rate to code {args.set_baud}...")
            temp_reader.set_baud_rate(args.set_baud)
            print("Note: You may need to reconnect with the new baud rate")

        # Single input readings
        if args.read_temp is not None:
            temp = temp_reader.read_temperature(args.read_temp)
            if isinstance(temp, (int, float)):
                print(f"Input {args.read_temp} Temperature: {temp:.3f} K")
            else:
                print(f"Input {args.read_temp} Temperature: {temp}")

        if args.read_resistance is not None:
            resistance = temp_reader.read_resistance(args.read_resistance)
            if isinstance(resistance, (int, float)):
                print(f"Input {args.read_resistance} Resistance: {resistance:.4f} Ω")
            else:
                print(f"Input {args.read_resistance} Resistance: {resistance}")

        if args.read_status is not None:
            status = temp_reader.get_status(args.read_status)
            print(f"Input {args.read_status} Status: {status}")

        # Multiple input scanning
        if args.scan is not None:
            if len(args.scan) == 0:
                # Default scan inputs 1-5
                input_list = [1, 2, 3, 4, 5]
            else:
                # Use provided input numbers
                try:
                    input_list = [int(x) for x in args.scan]
                except ValueError:
                    print("Error: Invalid input numbers for --scan")
                    return

            print(f"Scanning inputs: {input_list}")
            results = temp_reader.scan_inputs(input_list)
            
            for input_ch, data in results.items():
                print(f"Input {input_ch}:")
                temp = data['temperature']
                resistance = data['resistance']
                
                if isinstance(temp, (int, float)):
                    print(f"  Temperature: {temp:.3f} K")
                else:
                    print(f"  Temperature: {temp}")
                    
                if isinstance(resistance, (int, float)):
                    print(f"  Resistance:  {resistance:.4f} Ω")
                else:
                    print(f"  Resistance:  {resistance}")
                print()

        # Read inputs (unsure of total number yet)
        if args.all:
            print("Reading all inputs (1-16):")
            all_inputs = list(range(1, 17))
            results = temp_reader.scan_inputs(all_inputs)
            
            for input_ch, data in results.items():
                temp = data['temperature']
                resistance = data['resistance']
                
                # Only print inputs that have valid data
                if temp != "NO_RESPONSE" and resistance != "NO_RESPONSE":
                    print(f"Input {input_ch:2d}:", end="")
                    
                    if isinstance(temp, (int, float)):
                        print(f" Temp: {temp:8.3f} K", end="")
                    else:
                        print(f" Temp: {temp:>8s}", end="")
                        
                    if isinstance(resistance, (int, float)):
                        print(f" | Resistance: {resistance:10.4f} Ω")
                    else:
                        print(f" | Resistance: {resistance:>10s}")

    # Handle serial connection issues
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")
        print(f"Make sure the Lakeshore 370 is connected to {args.port} and the port is correct.")
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            temp_reader.close()
        except:
            pass

if __name__ == "__main__":
    main()