#!/usr/bin/env python3
"""
This script handles all serial commands for controlling heaters and analog outputs on the lakeshore370 

Its functions are called upon in main.py for command line operations
"""

import serial
import time

class OutputController:
    
    def __init__(self, ser=None, port='/dev/ttyUSB1', baudrate=9600):
        if ser is not None:
            self.ser = ser
        else:
            self.ser = serial.Serial(
                port=port, 
                baudrate=baudrate, 
                bytesize=7, 
                parity='O', 
                stopbits=1, 
                timeout=2
            )
    
    def send_command(self, command):
        try:
            self.ser.reset_input_buffer()
            
            self.ser.write((command + '\r\n').encode('ascii'))
            time.sleep(0.2)
            
            response = self.ser.readline().decode('ascii', errors='ignore').strip()
            return response
            
        except Exception as e:
            print(f"Communication error: {e}")
            return None

    def set_heater_output(self, percent):
        if not isinstance(percent, (int, float)) or percent < 0.0 or percent > 100.0:
            raise ValueError("Percent must be a number between 0.0 and 100.0")
        
        try:
            self.ser.reset_input_buffer()
            
            command = f"MOUT {percent:.3f}"
            self.ser.write((command + '\r\n').encode('ascii'))
            time.sleep(0.2) 
            
            print(f"Set heater output to {percent:.3f}%")
            return True
            
        except Exception as e:
            print(f"Communication error sending MOUT command: {e}")
            return False

    def get_heater_output(self):
        response = self.send_command("HTR?")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        try:
            return float(response)
        except ValueError:
            return response

    def set_heater_range(self, range_code):
        """
        
        Args:
            range_code (int): Heater range (0=off, 1=31.6µA, 2=100µA, 3=316µA, 4=1mA, 5=3.16mA, 6=10mA, 7=31.6mA, 8=100mA)
            
        """
        if not isinstance(range_code, int) or range_code < 0 or range_code > 8:
            raise ValueError("Range code must be an integer between 0 and 8")
        
        try:
            self.ser.reset_input_buffer()

            command = f"HTRRNG {range_code}"
            self.ser.write((command + '\r\n').encode('ascii'))
            time.sleep(0.2) 
            
            range_names = {
                0: "Off",
                1: "31.6 µA (0.1 µW into 100 Ω)",
                2: "100 µA (1 µW into 100 Ω)", 
                3: "316 µA (10 µW into 100 Ω)",
                4: "1 mA (100 µW into 100 Ω)",
                5: "3.16 mA (1 mW into 100 Ω)",
                6: "10 mA (10 mW into 100 Ω)",
                7: "31.6 mA (100 mW into 100 Ω)",
                8: "100 mA (1 W into 100 Ω)"
            }
            
            print(f"Set heater range to {range_code}: {range_names.get(range_code, 'Unknown')}")
            return True
            
        except Exception as e:
            print(f"Communication error sending HTRRNG command: {e}")
            return False

    def get_heater_range(self):
        response = self.send_command("HTRRNG?")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        try:
            return int(response)
        except ValueError:
            return response

    def get_heater_status(self):
        response = self.send_command("HTRST?")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        try:
            return int(response)
        except ValueError:
            return response

    def set_analog_output(self, channel, polarity, mode, input_channel=None, data_source=None, high_value=None, low_value=None, manual_value=None):
        """
        Set analog output configuration using ANALOG command
        
        Args:
            channel (int): Analog output channel (1 or 2)
            polarity (int): 0=unipolar, 1=bipolar
            mode (int): 0=off, 1=channel, 2=manual, 3=zone, 4=still (channel 2 only)
            input_channel (int): Input channel to monitor (1-16) if mode=1
            data_source (int): 1=Kelvin, 2=Ohms, 3=Linear Data if mode=1
            high_value (float): High endpoint value if mode=1, or manual value if mode=2
            low_value (float): Low endpoint value if mode=1
            manual_value (float): Manual output value if mode=2
    
        """
        if channel not in [1, 2]:
            raise ValueError("Channel must be 1 or 2")
        if polarity not in [0, 1]:
            raise ValueError("Polarity must be 0 (unipolar) or 1 (bipolar)")
        if mode not in [0, 1, 2, 3, 4]:
            raise ValueError("Mode must be 0-4")
        if mode == 4 and channel != 2:
            raise ValueError("Still mode (4) only available for channel 2")
            
        try:
            self.ser.reset_input_buffer()
            
            if mode == 0:  # Off
                command = f"ANALOG {channel},{polarity},{mode},0,0,0,0,0"
            elif mode == 1:  # Channel
                if input_channel is None or data_source is None or high_value is None or low_value is None:
                    raise ValueError("Channel mode requires input_channel, data_source, high_value, and low_value")
                if input_channel not in range(1, 17):
                    raise ValueError("Input channel must be 1-16")
                if data_source not in [1, 2, 3]:
                    raise ValueError("Data source must be 1 (Kelvin), 2 (Ohms), or 3 (Linear Data)")
                command = f"ANALOG {channel},{polarity},{mode},{input_channel},{data_source},{high_value},{low_value},0"
            elif mode == 2:  # Manual
                if manual_value is None:
                    raise ValueError("Manual mode requires manual_value")
                command = f"ANALOG {channel},{polarity},{mode},0,0,0,0,{manual_value}"
            elif mode == 3:  # Zone
                command = f"ANALOG {channel},{polarity},{mode},0,0,0,0,0"
            elif mode == 4:  # Still (channel 2 only)
                command = f"ANALOG {channel},{polarity},{mode},0,0,0,0,0"
            
            self.ser.write((command + '\r\n').encode('ascii'))
            time.sleep(0.2) 
            
            print(f"Set analog output {channel} configuration")
            return True
            
        except Exception as e:
            print(f"Communication error sending ANALOG command: {e}")
            return False

    def get_analog_output_config(self, channel):
        if channel not in [1, 2]:
            raise ValueError("Channel must be 1 or 2")
            
        response = self.send_command(f"ANALOG? {channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        try:
            parts = response.split(',')
            if len(parts) >= 7:
                return {
                    'polarity': int(parts[0]),
                    'mode': int(parts[1]),
                    'channel': int(parts[2]),
                    'data_source': int(parts[3]),
                    'high_value': float(parts[4]),
                    'low_value': float(parts[5]),
                    'manual_value': float(parts[6])
                }
            else:
                return response
        except (ValueError, IndexError):
            return response

    def get_analog_output_value(self, channel):
        
        if channel not in [1, 2]:
            raise ValueError("Channel must be 1 or 2")
            
        response = self.send_command(f"AOUT? {channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        try:
            return float(response)
        except ValueError:
            return response

    def close(self):
        """Close serial connection"""
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()