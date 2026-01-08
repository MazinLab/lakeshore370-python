#!/usr/bin/env python3
"""
This file handles all of the input/output functionality for the lakeshore370 

All serial commands for reading resistance and temperature are located here. 

Control for analog outputs and heaters are in outputs.py 

Serial Communication:
- Port: /dev/ttyUSB1 (default)
- Baud: 9600, 7-bit data, odd parity, 1 stop bit

"""

import serial
import time

class TemperatureReader:
    def __init__(self, port="/dev/ttyUSB1", baudrate=9600, timeout=2):

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=7,        # 7 data bits
                parity='O',        # Odd parity
                stopbits=1,
                timeout=timeout
            )
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            time.sleep(0.1)
            print(f"Connected to Lakeshore 370 on {port} at {baudrate} baud")
        except Exception as e:
            print(f"Failed to connect to Lakeshore 370: {e}")
            raise

    # Use for sending direct serial commands
    def send_command(self, command):
        try:
            # Clear any leftover data
            self.ser.reset_input_buffer()
            
            # Send command 
            self.ser.write((command + '\r\n').encode('ascii'))
            time.sleep(0.1)  # Allow time for device to respond
            
            # Read response
            response = self.ser.read_until(b'\r\n')
            if response:
                decoded = response.decode('ascii', errors='ignore').strip()
                # Remove any extra whitespace or control characters
                decoded = decoded.replace('\r', '').replace('\n', '').strip()
                return decoded
            return None
        except Exception as e:
            print(f"Communication error: {e}")
            return None

    # Print out device info (good for verification)
    def get_identification(self):
        response = self.send_command("*IDN?")
        return response if response else "NO_RESPONSE"

    # Printing out baud rate
    def get_baud_rate(self):
        response = self.send_command("BAUD?")
        return response if response else "NO_RESPONSE"

    def set_baud_rate(self, rate_code):
        if rate_code not in [0, 1, 2]:
            raise ValueError("Rate code must be 0 (300), 1 (1200), or 2 (9600)")
        
        self.send_command(f"BAUD {rate_code}")
        print(f"Baud rate set to code {rate_code}")

    def read_kelvin_temperature(self, input_channel):
        if not isinstance(input_channel, int) or input_channel < 1 or input_channel > 16:
            raise ValueError("Input channel must be an integer between 1 and 16")

        response = self.send_command(f"RDGK? {input_channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        response_upper = response.upper()
        if "OVERLD" in response_upper or "OVER" in response_upper:
            return "T_OVER"
        if "NOT" in response_upper or "NONE" in response_upper:
            return "NOT_CONFIGURED"
            
        try:
            temp_value = float(response)
            # Check for reasonable temperature values
            if temp_value <= 0.0:
                return "T_OVER"
            return temp_value
        except ValueError:
            if any(indicator in response_upper for indicator in ['OVER', 'ERR', 'INVALID']):
                return "T_OVER"
            return response

    def read_resistance(self, input_channel):
        if not isinstance(input_channel, int) or input_channel < 1 or input_channel > 16:
            raise ValueError("Input channel must be an integer between 1 and 16")

        # Read resistance value using correct 370 command
        response = self.send_command(f"RDGR? {input_channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        # Handle common 370 error responses
        response_upper = response.upper()
        if "OVERLD" in response_upper or "OVER" in response_upper:
            return "R_OVER"
        if "NOT" in response_upper or "NONE" in response_upper:
            return "NOT_CONFIGURED"
            
        try:
            resistance_value = float(response)
            if resistance_value < 0.0:
                return "R_OVER"
            return resistance_value
        except ValueError:
            return response

    def read_excitation_power(self, input_channel):
        if not isinstance(input_channel, int) or input_channel < 1 or input_channel > 16:
            raise ValueError("Input channel must be an integer between 1 and 16")

        response = self.send_command(f"RDGPWR? {input_channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        response_upper = response.upper()
        if "OVERLD" in response_upper or "OVER" in response_upper:
            return "PWR_OVER"
        if "NOT" in response_upper or "NONE" in response_upper:
            return "NOT_CONFIGURED"
            
        try:
            power_value = float(response)
            return power_value
        except ValueError:
            return response

    def read_status(self, input_channel):
        if not isinstance(input_channel, int) or input_channel < 1 or input_channel > 16:
            raise ValueError("Input channel must be an integer between 1 and 16")

        response = self.send_command(f"RDGST? {input_channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        try:
            return int(response)
        except ValueError:
            return response

    def get_resistance_range(self, input_channel):
        if not isinstance(input_channel, int) or input_channel < 1 or input_channel > 16:
            raise ValueError("Input channel must be an integer between 1 and 16")

        response = self.send_command(f"RDGRNG? {input_channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        try:
            parts = response.split(',')
            if len(parts) == 5:
                return {
                    'mode': int(parts[0]),
                    'excitation': int(parts[1]),
                    'range': int(parts[2]),
                    'autorange': int(parts[3]),
                    'cs_off': int(parts[4])
                }
            else:
                return response
        except (ValueError, IndexError):
            return response

    def set_resistance_range(self, input_channel, mode, excitation, range_code, autorange, cs_off):
        if not isinstance(input_channel, int) or input_channel < 1 or input_channel > 16:
            raise ValueError("Input channel must be an integer between 1 and 16")
        
        if not isinstance(mode, int) or mode < 0 or mode > 2:
            raise ValueError("Mode must be an integer between 0 and 2")
            
        if not isinstance(excitation, int) or excitation < 1 or excitation > 22:
            raise ValueError("Excitation must be an integer between 1 and 22")
            
        if not isinstance(range_code, int) or range_code < 1 or range_code > 22:
            raise ValueError("Range code must be an integer between 1 and 22")
            
        if not isinstance(autorange, int) or autorange < 0 or autorange > 1:
            raise ValueError("Autorange must be 0 (off) or 1 (on)")
            
        if not isinstance(cs_off, int) or cs_off < 0 or cs_off > 1:
            raise ValueError("Current source off must be 0 (on) or 1 (off)")

        # Get the current configuration first
        print(f"Current configuration for input {input_channel}:")
        current_config = self.get_resistance_range(input_channel)
        if isinstance(current_config, dict):
            print(f"  Before: {current_config['mode']},{current_config['excitation']},{current_config['range']},{current_config['autorange']},{current_config['cs_off']}")

        # Send the RDGRNG command
        command = f"RDGRNG {input_channel},{mode},{excitation},{range_code},{autorange},{cs_off}"
        
        try:
            # Clear any leftover data
            self.ser.reset_input_buffer()
            
            # Send command
            self.ser.write((command + '\r\n').encode('ascii'))
            time.sleep(0.5)  # Longer delay for write commands
            
            print(f"Sent command: {command}")
            
            time.sleep(0.2) 
            new_config = self.get_resistance_range(input_channel)
            if isinstance(new_config, dict):
                print(f"  After:  {new_config['mode']},{new_config['excitation']},{new_config['range']},{new_config['autorange']},{new_config['cs_off']}")
                
                # Check if the configuration actually changed
                expected = {'mode': mode, 'excitation': excitation, 'range': range_code, 'autorange': autorange, 'cs_off': cs_off}
                if new_config == expected:
                    print("Configuration changed!")
                    return True
                else:
                    print("Configuration did not change")
                    return False
            else:
                print(f"Could not verify configuration: {new_config}")
                return False
            
        except Exception as e:
            print(f"Communication error sending RDGRNG command: {e}")
            return False

    def read_sensor(self, input_channel):
        if not isinstance(input_channel, int) or input_channel < 1 or input_channel > 16:
            raise ValueError("Input channel must be an integer between 1 and 16")

        # Read sensor value using correct 370 command
        response = self.send_command(f"RDGS? {input_channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        # Handle common 370 error responses
        response_upper = response.upper()
        if "OVERLD" in response_upper or "OVER" in response_upper:
            return "SENSOR_OVER"
        if "NOT" in response_upper or "NONE" in response_upper:
            return "NOT_CONFIGURED"
            
        try:
            sensor_value = float(response)
            return sensor_value
        except ValueError:
            return response

    def scan_inputs(self, input_list=None):
        if input_list is None:
            input_list = [1, 2, 3, 4]  # Default inputs to scan
        
        results = {}
        for input_ch in input_list:
            try:
                # Read all types of data for each input
                temp = self.read_kelvin_temperature(input_ch)
                resistance = self.read_resistance(input_ch)
                sensor = self.read_sensor(input_ch)
                power = self.read_excitation_power(input_ch)
                status = self.read_status(input_ch)
                
                results[input_ch] = {
                    'temperature': temp,
                    'resistance': resistance,
                    'sensor': sensor,
                    'power': power,
                    'status': status
                }
            except Exception as e:
                results[input_ch] = {
                    'temperature': f'ERROR: {e}',
                    'resistance': f'ERROR: {e}',
                    'sensor': f'ERROR: {e}',
                    'power': f'ERROR: {e}',
                    'status': f'ERROR: {e}'
                }
        return results

    def close(self):
        """Close serial connection"""
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            self.ser.close()
            print("Lakeshore 370 connection closed")

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()