#!/usr/bin/env python3
"""
Main interface for Lakeshore370 AC Resistance Bridge Driver 

Original serial commands located in temperature.py and outputs.py
"""

import argparse
import serial
from .temperature import TemperatureReader
from .outputs import OutputController

def main():
    parser = argparse.ArgumentParser(
        description="Lakeshore 370 AC Resistance Bridge CLI"
    )
    
    # Device information
    parser.add_argument("--info", action="store_true", help="Get device information (*IDN?, BAUD?)")
    
    # Reading arguments
    parser.add_argument("--read-temp", type=int, metavar='INPUT', help="Read temperature from input (RDGK? <input>)")
    parser.add_argument("--read-resistance", type=int, metavar='INPUT', help="Read resistance from input (RDGR? <input>)")
    parser.add_argument("--read-sensor", type=int, metavar='INPUT', help="Read raw sensor value from input (RDGS? <input>)")
    parser.add_argument("--read-power", type=int, metavar='INPUT', help="Read excitation power from input (RDGPWR? <input>)")
    parser.add_argument("--read-status", type=int, metavar='INPUT', help="Read status from input (RDGST? <input>)")
    
    # Range operations
    parser.add_argument("--get-range", type=int, metavar='INPUT', help="Get resistance range configuration (RDGRNG? <input>)")
    parser.add_argument("--set-range", nargs=2, metavar=('INPUT', 'CONFIG'), help="Set resistance range (RDGRNG <input>,<config>)")
    
    # Heater control arguments
    parser.add_argument("--heater-output", type=float, metavar='PERCENT', help="Set heater output percentage (MOUT <percent>)")
    parser.add_argument("--get-heater-output", action="store_true", help="Get current heater output percentage (HTR?)")
    parser.add_argument("--heater-range", type=int, metavar='RANGE', help="Set heater range (HTRRNG <range>)")
    parser.add_argument("--get-heater-range", action="store_true", help="Get current heater range (HTRRNG?)")
    parser.add_argument("--get-heater-status", action="store_true", help="Get heater status (HTRST?)")
    
    # Analog output arguments
    parser.add_argument("--analog-config", nargs='+', metavar=('CHANNEL', 'ARGS'), help="Set analog output config (ANALOG <channel>,<polarity>,<mode>,[other args])")
    parser.add_argument("--get-analog-config", type=int, metavar='CHANNEL', help="Get analog output configuration (ANALOG? <channel>)")
    parser.add_argument("--get-analog-output", type=int, metavar='CHANNEL', help="Get analog output value (AOUT? <channel>)")
    
    # Scanning arguments
    parser.add_argument("--scan", nargs='*', metavar='INPUT', help="Scan multiple inputs (RDGK?, RDGR?, RDGS?, RDGPWR?, RDGST?)")
    parser.add_argument("--scan-range", nargs=2, type=int, metavar=('START', 'STOP'), help="Scan input range (multiple commands)")
    parser.add_argument("--all", action="store_true", help="Read all inputs 1-16 (RDGK?, RDGR?, RDGPWR?)")
    
    # Serial communication settings
    parser.add_argument("--port", default="/dev/ttyUSB1", help="Serial port (default: /dev/ttyUSB1)")
    parser.add_argument("--baudrate", type=int, default=9600, choices=[300, 1200, 9600], help="Baud rate (default: 9600)")
    parser.add_argument("--get-baud", action="store_true", help="Get current baud rate setting (BAUD?)")
    parser.add_argument("--set-baud", type=int, choices=[0, 1, 2], help="Set baud rate (BAUD <code>)")
    
    # Raw command
    parser.add_argument("--raw-command", type=str, help="Send raw command to device")
    
    args = parser.parse_args()

    try:
        temp_reader = TemperatureReader(port=args.port, baudrate=args.baudrate)

        if args.raw_command:
            print(f"Command: {args.raw_command}")
            response = temp_reader.send_command(args.raw_command)
            print(f"Response: {response}")
            return

        # Device information
        if args.info:
            print("Device Information:")
            print("Command: *IDN?")
            identification = temp_reader.get_identification()
            print("Command: BAUD?")
            baud_rate = temp_reader.get_baud_rate()
            print(f"  ID: {identification}")
            print(f"  Baud Rate Code: {baud_rate} (0=300, 1=1200, 2=9600)")
            print()

        # Baud rate operations
        if args.get_baud:
            print("Command: BAUD?")
            baud_code = temp_reader.get_baud_rate()
            baud_map = {"0": "300", "1": "1200", "2": "9600"}
            baud_str = baud_map.get(baud_code, f"Unknown ({baud_code})")
            print(f"Current baud rate: {baud_str} baud (code: {baud_code})")

        if args.set_baud is not None:
            print(f"Command: BAUD {args.set_baud}")
            print(f"Setting baud rate to code {args.set_baud}...")
            temp_reader.set_baud_rate(args.set_baud)
            print("Note: You may need to reconnect with the new baud rate")

        # Single input readings
        if args.read_temp is not None:
            print(f"Command: RDGK? {args.read_temp}")
            temp = temp_reader.read_kelvin_temperature(args.read_temp)
            if isinstance(temp, (int, float)):
                print(f"Input {args.read_temp} Temperature: {temp:.3f} K")
            else:
                print(f"Input {args.read_temp} Temperature: {temp}")

        if args.read_resistance is not None:
            print(f"Command: RDGR? {args.read_resistance}")
            resistance = temp_reader.read_resistance(args.read_resistance)
            if isinstance(resistance, (int, float)):
                print(f"Input {args.read_resistance} Resistance: {resistance:.4f} Ω")
            else:
                print(f"Input {args.read_resistance} Resistance: {resistance}")

        if args.read_sensor is not None:
            print(f"Command: RDGS? {args.read_sensor}")
            sensor = temp_reader.read_sensor(args.read_sensor)
            if isinstance(sensor, (int, float)):
                print(f"Input {args.read_sensor} Sensor: {sensor:.6f}")
            else:
                print(f"Input {args.read_sensor} Sensor: {sensor}")

        if args.read_power is not None:
            print(f"Command: RDGPWR? {args.read_power}")
            power = temp_reader.read_excitation_power(args.read_power)
            if isinstance(power, (int, float)):
                if power < 1e-12:  # Less than 1 pW
                    print(f"Input {args.read_power} Power: {power*1e15:.3f} fW")
                elif power < 1e-9:  # Less than 1 nW
                    print(f"Input {args.read_power} Power: {power*1e12:.3f} pW")
                elif power < 1e-6:  # Less than 1 µW
                    print(f"Input {args.read_power} Power: {power*1e9:.3f} nW")
                elif power < 1e-3:  # Less than 1 mW
                    print(f"Input {args.read_power} Power: {power*1e6:.3f} µW")
                else:
                    print(f"Input {args.read_power} Power: {power*1e3:.3f} mW")
            else:
                print(f"Input {args.read_power} Power: {power}")

        if args.read_status is not None:
            print(f"Command: RDGST? {args.read_status}")
            status = temp_reader.read_status(args.read_status)
            if isinstance(status, int):
                print(f"Input {args.read_status} Status: {status} (0x{status:02X})")
            else:
                print(f"Input {args.read_status} Status: {status}")

        # Range operations
        if args.get_range is not None:
            print(f"Command: RDGRNG? {args.get_range}")
            range_config = temp_reader.get_resistance_range(args.get_range)
            print(f"Input {args.get_range} Resistance Range Configuration:")
            if isinstance(range_config, dict):
                print(f"  Format: <mode>,<excitation>,<range>,<autorange>,<cs_off>")
                print(f"  Response: {range_config['mode']},{range_config['excitation']},{range_config['range']},{range_config['autorange']},{range_config['cs_off']}")
                print(f"  Parsed:")
                print(f"    Mode: {range_config['mode']} (0=manual, 1=current, 2=voltage)")
                print(f"    Excitation: {range_config['excitation']} (level 1-22)")
                print(f"    Range: {range_config['range']} (range 1-22)")
                print(f"    Autorange: {range_config['autorange']} (0=off, 1=on)")
                print(f"    Current Source: {range_config['cs_off']} (0=on, 1=off)")
            else:
                print(f"  Format: <mode>,<excitation>,<range>,<autorange>,<cs_off>")
                print(f"  Response: {range_config}")

        if args.set_range is not None:
            input_num, config_str = args.set_range
            try:
                input_num = int(input_num)
                # Parse the comma-separated configuration string
                config_parts = config_str.split(',')
                if len(config_parts) != 5:
                    print("Error: Configuration must have exactly 5 comma-separated values: <mode>,<excitation>,<range>,<autorange>,<cs_off>")
                    return
                
                mode, excitation, range_code, autorange, cs_off = map(int, config_parts)
                print(f"Command: RDGRNG {input_num},{mode},{excitation},{range_code},{autorange},{cs_off}")
                
                success = temp_reader.set_resistance_range(input_num, mode, excitation, range_code, autorange, cs_off)
                if success:
                    print(f"Command sent successfully for input {input_num}")
                    print(f"  Mode: {mode} (0=manual, 1=current, 2=voltage)")
                    print(f"  Excitation: {excitation} (level 1-22)")
                    print(f"  Range: {range_code} (range 1-22)")
                    print(f"  Autorange: {autorange} (0=off, 1=on)")
                    print(f"  Current Source: {cs_off} (0=on, 1=off)")
                    print()
                    print(f"Verify the setting with: lakeshore370 --get-range {input_num}")
                else:
                    print(f"Failed to send command for input {input_num}")
            except ValueError as e:
                print(f"Error parsing configuration: {e}")
                print("Configuration format: <mode>,<excitation>,<range>,<autorange>,<cs_off>")
                print("Example: --set-range 1 1,10,22,1,0")

        # Analog output and heater control
        if (
            args.heater_output is not None or args.get_heater_output or
            args.heater_range is not None or args.get_heater_range or
            args.get_heater_status or args.analog_config is not None or
            args.get_analog_config is not None or args.get_analog_output is not None
        ):
            output_ctrl = OutputController(port=args.port, baudrate=args.baudrate)
            
            if args.heater_output is not None:
                print(f"Command: MOUT {args.heater_output:.3f}")
                success = output_ctrl.set_heater_output(args.heater_output)
                if success:
                    print(f"Heater output set to {args.heater_output:.3f}%")
                else:
                    print("Failed to set heater output")

            if args.get_heater_output:
                print("Command: HTR?")
                output = output_ctrl.get_heater_output()
                if isinstance(output, (int, float)):
                    print(f"Current heater output: {output:.3f}%")
                else:
                    print(f"Heater output: {output}")

            if args.heater_range is not None:
                print(f"Command: HTRRNG {args.heater_range}")
                success = output_ctrl.set_heater_range(args.heater_range)
                if not success:
                    print("Failed to set heater range")

            if args.get_heater_range:
                print("Command: HTRRNG?")
                range_code = output_ctrl.get_heater_range()
                if isinstance(range_code, int):
                    range_names = {
                        0: "Off", 1: "31.6 µA (0.1 µW)", 2: "100 µA (1 µW)", 3: "316 µA (10 µW)",
                        4: "1 mA (100µW)", 5: "3.16 mA (1 mW)", 6: "10 mA (10 mW)", 
                        7: "31.6 mA (100 mW)", 8: "100 mA (1 W)"
                    }
                    print(f"Current heater range: {range_code} - {range_names.get(range_code, 'Unknown')}")
                else:
                    print(f"Heater range: {range_code}")

            if args.get_heater_status:
                print("Command: HTRST?")
                status = output_ctrl.get_heater_status()
                if isinstance(status, int):
                    print(f"Heater status: {status} (0x{status:02X})")
                else:
                    print(f"Heater status: {status}")

            # Analog output operations
            if args.analog_config is not None:
                try:
                    if len(args.analog_config) < 3:
                        print("Error: --analog-config requires at least channel, polarity, and mode")
                        print("Usage: --analog-config <channel> <polarity> <mode> [additional args based on mode]")
                        return
                    
                    channel = int(args.analog_config[0])
                    polarity = int(args.analog_config[1])
                    mode = int(args.analog_config[2])
                    
                    if mode == 0:  # Off
                        print(f"Command: ANALOG {channel},{polarity},{mode},0,0,0,0,0")
                        success = output_ctrl.set_analog_output(channel, polarity, mode)
                    elif mode == 1:  # Channel
                        if len(args.analog_config) < 7:
                            print("Error: Channel mode requires: <channel> <polarity> <mode> <input_channel> <data_source> <high_value> <low_value>")
                            return
                        input_channel = int(args.analog_config[3])
                        data_source = int(args.analog_config[4])
                        high_value = float(args.analog_config[5])
                        low_value = float(args.analog_config[6])
                        print(f"Command: ANALOG {channel},{polarity},{mode},{input_channel},{data_source},{high_value},{low_value},0")
                        success = output_ctrl.set_analog_output(channel, polarity, mode, input_channel, data_source, high_value, low_value)
                    elif mode == 2:  # Manual
                        if len(args.analog_config) < 4:
                            print("Error: Manual mode requires: <channel> <polarity> <mode> <manual_value>")
                            return
                        manual_value = float(args.analog_config[3])
                        print(f"Command: ANALOG {channel},{polarity},{mode},0,0,0,0,{manual_value}")
                        success = output_ctrl.set_analog_output(channel, polarity, mode, manual_value=manual_value)
                    elif mode == 3:  # Zone
                        print(f"Command: ANALOG {channel},{polarity},{mode},0,0,0,0,0")
                        success = output_ctrl.set_analog_output(channel, polarity, mode)
                    elif mode == 4:  # Still (channel 2 only)
                        print(f"Command: ANALOG {channel},{polarity},{mode},0,0,0,0,0")
                        success = output_ctrl.set_analog_output(channel, polarity, mode)
                    else:
                        print("Error: Mode must be 0-4")
                        return
                    
                    if success:
                        print(f"Analog output {channel} configuration set successfully")
                    else:
                        print(f"Failed to set analog output {channel} configuration")
                        
                except (ValueError, IndexError) as e:
                    print(f"Error parsing analog configuration: {e}")
                    print("Usage: --analog-config <channel> <polarity> <mode> [additional args based on mode]")

            if args.get_analog_config is not None:
                print(f"Command: ANALOG? {args.get_analog_config}")
                config = output_ctrl.get_analog_output_config(args.get_analog_config)
                if isinstance(config, dict):
                    print(f"Analog output {args.get_analog_config} configuration:")
                    mode_names = {0: "Off", 1: "Channel", 2: "Manual", 3: "Zone", 4: "Still"}
                    polarity_names = {0: "Unipolar", 1: "Bipolar"}
                    source_names = {1: "Kelvin", 2: "Ohms", 3: "Linear Data"}
                    
                    print(f"  Polarity: {config['polarity']} ({polarity_names.get(config['polarity'], 'Unknown')})")
                    print(f"  Mode: {config['mode']} ({mode_names.get(config['mode'], 'Unknown')})")
                    print(f"  Channel: {config['channel']}")
                    print(f"  Data Source: {config['data_source']} ({source_names.get(config['data_source'], 'Unknown')})")
                    print(f"  High Value: {config['high_value']}")
                    print(f"  Low Value: {config['low_value']}")
                    print(f"  Manual Value: {config['manual_value']}")
                else:
                    print(f"Analog output {args.get_analog_config} configuration: {config}")

            if args.get_analog_output is not None:
                print(f"Command: AOUT? {args.get_analog_output}")
                output = output_ctrl.get_analog_output_value(args.get_analog_output)
                if isinstance(output, (int, float)):
                    print(f"Analog output {args.get_analog_output} current value: {output:.3f}%")
                else:
                    print(f"Analog output {args.get_analog_output} value: {output}")
                    
            # Close the output controller connection
            try:
                output_ctrl.close()
            except:
                pass

        # Range scanning and all inputs
        if args.scan_range is not None or args.all:
            if args.scan_range:
                start, stop = args.scan_range
                input_list = list(range(start, stop + 1))
                print(f"Commands: RDGK?, RDGR?, RDGPWR?, RDGST? for inputs {start}-{stop}")
                print(f"Scanning input range {start} to {stop}:")
            else:  # args.all
                input_list = [1, 2]  # Model 370 has only 2 inputs
                print("Commands: RDGK?, RDGR?, RDGPWR? for inputs 1-2")
                print("Reading all inputs (1-2):")
                
            results = temp_reader.scan_inputs(input_list)
            
            for input_ch, data in results.items():
                temp = data['temperature']
                resistance = data['resistance']
                power = data['power']
                status = data.get('status')  # status might not be in 'all' mode
                
                # Only print inputs that have valid data
                if temp != "NO_RESPONSE" or resistance != "NO_RESPONSE":
                    print(f"Input {input_ch:2d}:", end="")
                    
                    # Temperature formatting
                    if isinstance(temp, (int, float)):
                        print(f" Temp: {temp:8.3f} K", end="")
                    else:
                        print(f" Temp: {temp:>12s}", end="")
                        
                    # Resistance formatting  
                    if isinstance(resistance, (int, float)):
                        print(f" | Res: {resistance:10.4f} Ω", end="")
                    else:
                        print(f" | Res: {resistance:>12s}", end="")
                        
                    # Power formatting
                    if isinstance(power, (int, float)):
                        if power < 1e-12:
                            print(f" | Pwr: {power*1e15:8.1f} fW", end="")
                        elif power < 1e-9:
                            print(f" | Pwr: {power*1e12:8.1f} pW", end="")
                        else:
                            print(f" | Pwr: {power*1e9:8.1f} nW", end="")
                    else:
                        print(f" | Pwr: {power:>10s}", end="")

                    # Status formatting (only for scan_range)
                    if args.scan_range and status is not None:
                        if isinstance(status, int):
                            print(f" | St: 0x{status:02X}")
                        else:
                            print(f" | St: {status:>6s}")
                    else:
                        print()  # Just newline for 'all' mode

        # Multiple input scanning (detailed view)
        if args.scan is not None:
            if len(args.scan) == 0:
                input_list = [1, 2]  # Default scan inputs 1-2 (Model 370 has only 2 inputs)
            else:
                try:
                    input_list = [int(x) for x in args.scan]
                except ValueError:
                    print("Error: Invalid input numbers for --scan")
                    return

            print(f"Commands: RDGK?, RDGR?, RDGS?, RDGPWR?, RDGST? for inputs {input_list}")
            print(f"Scanning inputs: {input_list}")
            results = temp_reader.scan_inputs(input_list)
            
            for input_ch, data in results.items():
                print(f"Input {input_ch}:")
                temp = data['temperature']
                resistance = data['resistance']
                sensor = data['sensor']
                power = data['power']
                status = data['status']
                
                # Helper function for power formatting
                def format_power(p):
                    if isinstance(p, (int, float)):
                        if p < 1e-12:
                            return f"{p*1e15:.3f} fW"
                        elif p < 1e-9:
                            return f"{p*1e12:.3f} pW"
                        elif p < 1e-6:
                            return f"{p*1e9:.3f} nW"
                        else:
                            return f"{p*1e6:.3f} µW"
                    return str(p)
                
                # Print formatted results
                print(f"  Temperature: {temp:.3f} K" if isinstance(temp, (int, float)) else f"  Temperature: {temp}")
                print(f"  Resistance:  {resistance:.4f} Ω" if isinstance(resistance, (int, float)) else f"  Resistance:  {resistance}")
                print(f"  Sensor:      {sensor:.6f}" if isinstance(sensor, (int, float)) else f"  Sensor:      {sensor}")
                print(f"  Power:       {format_power(power)}")
                print(f"  Status:      {status} (0x{status:02X})" if isinstance(status, int) else f"  Status:      {status}")
                print()

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

# Examples:
#   lakeshore370 --info                          Get device information (*IDN?, BAUD?)
#   lakeshore370 --read-temp 1                   Read temperature from input 1 (RDGK? 1)
#   lakeshore370 --read-resistance 2             Read resistance from input 2 (RDGR? 2)
#   lakeshore370 --read-power 1                  Read excitation power from input 1 (RDGPWR? 1)
#   lakeshore370 --read-status 2                 Read status from input 2 (RDGST? 2)
#   lakeshore370 --get-range 1                   Get resistance range for input 1 (RDGRNG? 1)
#   lakeshore370 --set-range 1 1,10,22,0,0      Set resistance range for input 1 (RDGRNG 1,1,10,22,0,0)
#   
#   Heater Control:
#   lakeshore370 --heater-output 50.5            Set heater output to 50.5% (MOUT 50.5)
#   lakeshore370 --get-heater-output             Get current heater output (HTR?)
#   lakeshore370 --heater-range 5                Set heater range to 5 (HTRRNG 5)
#   lakeshore370 --get-heater-range              Get current heater range (HTRRNG?)
#   lakeshore370 --get-heater-status             Get heater status (HTRST?)
#   
#   Analog Output Control:
#   lakeshore370 --analog-config 1 0 2 0 0 0 0 50.5  Set analog output 1 to manual mode, 50.5% output
#   lakeshore370 --analog-config 2 1 1 2 1 10.0 0.0 0  Set analog output 2 to monitor input 2 Kelvin, bipolar 0-10K range
#   lakeshore370 --get-analog-config 1           Get analog output 1 configuration (ANALOG? 1)
#   lakeshore370 --get-analog-output 2           Get analog output 2 current value (AOUT? 2)
#   
#   lakeshore370 --scan                          Scan default inputs (1-2) (RDGK?, RDGR?, RDGPWR?, RDGST?)
#   lakeshore370 --all                           Read all inputs (1-2) (RDGK?, RDGR?, RDGPWR?)
#   lakeshore370 --raw-command "RDGK? 1"         Send raw command

# Range Configuration Format (for --set-range):
#   <input> <mode>,<excitation>,<range>,<autorange>,<cs_off>
#   input: 1 or 2 (Model 370 has 2 inputs only)
#   mode: 0=manual, 1=current excitation, 2=voltage excitation
#   excitation: 1-22 (excitation level)
#   range: 1-22 (resistance range)
#   autorange: 0=off (manual range), 1=on (automatic range selection)
#   cs_off: 0=current source on, 1=current source off
#   ** You cannot adjust heater range if autorange is enabled ** 

# Heater Ranges:
#   0=Off, 1=31.6µA (0.1µW), 2=100µA (1µW), 3=316µA (10µW), 4=1mA (100µW)
#   5=3.16mA (1mW), 6=10mA (10mW), 7=31.6mA (100mW), 8=100mA (1W)

# Serial Commands:
#   *IDN? - Device identification    BAUD? - Baud rate query
#   RDGK? - Kelvin reading          RDGR? - Resistance reading
#   RDGS? - Sensor reading          RDGPWR? - Power reading
#   RDGST? - Status reading         RDGRNG? - Range query
#   RDGRNG - Range command          INPT? - Input config
#   HTR? - Heater output query      MOUT - Set heater output
#   HTRRNG? - Heater range query    HTRRNG - Set heater range
#   HTRST? - Heater status query    ANALOG - Set analog output config
#   ANALOG? - Analog output query   AOUT? - Analog output value query

# Analog Output Modes:
#   0=Off, 1=Channel (monitor input), 2=Manual, 3=Zone, 4=Still (channel 2 only)
#   Polarity: 0=Unipolar (0 to +10V), 1=Bipolar (-10V to +10V)  
#   Data Source: 1=Kelvin, 2=Ohms, 3=Linear Data

# Analog Configuration Examples:
#   Channel mode: --analog-config 1 0 1 2 1 10.0 0.0  (monitor input 2, Kelvin, 0-10K range)
#   Manual mode:  --analog-config 2 1 2 50.5           (manual 50.5% output, bipolar)
#   Still mode:   --analog-config 2 0 4                (channel 2 still heater mode)

# Serial Settings:
#   Default: 9600 baud, 7-bit data, odd parity, 1 stop bit
#   Port: /dev/ttyUSB1 (use --port to change)