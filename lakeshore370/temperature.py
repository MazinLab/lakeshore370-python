#!/usr/bin/env python3
"""
This file will handle all channel/input reading functionality for the lakeshore370 

All serial commands will be here

Main Functions: 
- read_temperature(): Main function - returns temp in K or resistance in Ω
- read_resistance(): Direct resistance reading in Ω
- read_sensor(): Direct sensor reading 
- send_command(): Sends command over serial 

Lakeshore 370 Hardware:
- Input 1-16: Resistance inputs for various sensors
- AC Resistance Bridge with multiple excitation modes
- Support for various resistance thermometer types

Serial Communication:
- Port: /dev/ttyUSB4 (default)
- Baud: 9600 (default, can be 300, 1200, or 9600)
- Parity: Odd
- Data bits: 8
- Stop bits: 1

This file is in progress and most of this functionality doesn't work, I'm just getting it set up
"""

import serial
import time

class TemperatureReader:
    """
    Lakeshore 370 AC Resistance Bridge Interface
    
    Usage Examples:
        temp_reader = TemperatureReader()
        
        # Temperature readings (returns float in Kelvin or "T_OVER")
        temp = temp_reader.read_temperature(1)      # Reads Input 1
        temp = temp_reader.read_temperature(5)      # Reads Input 5
        
        # Resistance readings (returns float in Ohms or "R_OVER")
        resistance = temp_reader.read_resistance(1)  # Input 1 resistance in Ohms
        resistance = temp_reader.read_resistance(8)  # Input 8 resistance in Ohms
        
        # Device info
        info = temp_reader.get_identification()     # Get device ID
        baud = temp_reader.get_baud_rate()          # Get current baud rate
        
        # Serial Commands Used:
        #   KRDG? - Kelvin temperature reading
        #   RDGR? - Resistance reading  
        #   RDGST? - Status reading (detects over-range conditions)
        #   *IDN? - Device identification
        #   BAUD? - Baud rate query
    """

    def __init__(self, port="/dev/ttyUSB4", baudrate=9600, timeout=2):
        """
        Initialize connection to Lakeshore 370
        
        Args:
            port (str): Serial port (default: /dev/ttyUSB4)
            baudrate (int): Baud rate - 300, 1200, or 9600 (default: 9600)  
            timeout (int): Serial timeout in seconds (default: 2)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=8,        # 370 uses 8 data bits
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

    # Kinda works? Not really
    def send_command(self, command):
        """
        Send a command to the Lakeshore 370 and return response
        
        Args:
            command (str): Command to send (without terminator)
            
        Returns:
            str: Response from device, or None if error
        """
        try:
            # Send command with newline terminator
            self.ser.write((command + '\n').encode('ascii'))
            time.sleep(0.2)  # Allow time for device to respond
            
            # Read response
            response = self.ser.readline()
            if response:
                decoded = response.decode('ascii', errors='ignore').strip()
                return decoded
            return None
        except Exception as e:
            print(f"Communication error: {e}")
            return None

    # Works but prints out weird
    def get_identification(self):
        """
        Get device identification string
        
        Returns:
            str: Device identification or "NO_RESPONSE"
        """
        response = self.send_command("*IDN?")
        return response if response else "NO_RESPONSE"

    # Works
    def get_baud_rate(self):
        """
        Get current baud rate setting
        
        Returns:
            str: Baud rate code (0=300, 1=1200, 2=9600) or "NO_RESPONSE"
        """
        response = self.send_command("BAUD?")
        return response if response else "NO_RESPONSE"

    # Works
    def set_baud_rate(self, rate_code):
        """
        Set baud rate (use with caution - may break communication)
        
        Args:
            rate_code (int): 0=300 baud, 1=1200 baud, 2=9600 baud
        """
        if rate_code not in [0, 1, 2]:
            raise ValueError("Rate code must be 0 (300), 1 (1200), or 2 (9600)")
        
        response = self.send_command(f"BAUD {rate_code}")
        print(f"Baud rate set to code {rate_code}")

    # DOESN'T REALLY WORK
    def read_resistance(self, input_channel):
        """
        Read resistance from specified input channel
        
        Args:
            input_channel (int): Input channel number (1-16 typically)
            
        Returns:
            float: Resistance in Ohms
            str: "R_OVER" if over-range
            str: "NO_RESPONSE" if no communication
        """
        if not isinstance(input_channel, int) or input_channel < 1:
            raise ValueError("Input channel must be an integer >= 1")
            
        # Check status first for over-range condition
        status_response = self.send_command(f"RDGST? {input_channel}")
        try:
            if status_response:
                status_code = int(status_response)
                # Check for over-range flag (bit patterns may differ from 350)
                if status_code & 32:  # Over-range bit
                    return "R_OVER"
        except (ValueError, TypeError):
            pass

        # Read resistance value
        response = self.send_command(f"RDGR? {input_channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        # Check for over-range indicators in response
        if len(response) > 15 or any(char in response for char in ['`', '\x00']):
            return "R_OVER"
            
        try:
            resistance_value = float(response)
            # Check for obvious over-range values
            if resistance_value <= 0.0:
                return "R_OVER"
            return resistance_value
        except ValueError:
            # Check for text indicators of over-range
            if any(indicator in response.upper() for indicator in ['OVER', 'R.', 'R_', 'OVERLD']):
                return "R_OVER"
            return response

    # Doesn't really work yet 
    def read_temperature(self, input_channel):
        """
        Main Temperature Reading Function
        
        Args:
            input_channel (int): Input channel number (1-16 typically)
            
        Returns:
            float: Temperature in Kelvin
            str: "T_OVER" if temperature is over-range  
            str: "NO_RESPONSE" if no communication
            
        Note: For inputs without temperature calibration curves, 
              this will return the resistance value instead.
        """
        if not isinstance(input_channel, int) or input_channel < 1:
            raise ValueError("Input channel must be an integer >= 1")

        # Check status first for over-range condition
        status_response = self.send_command(f"RDGST? {input_channel}")
        try:
            if status_response:
                status_code = int(status_response)
                # Check for over-range flag
                if status_code & 32:  # Over-range bit
                    return "T_OVER"
        except (ValueError, TypeError):
            pass

        # Read temperature value
        response = self.send_command(f"KRDG? {input_channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        # Check for over-range indicators in response
        if len(response) > 15 or any(char in response for char in ['`', '\x00']):
            return "T_OVER"
            
        try:
            temp_value = float(response)
            # Check for obvious invalid temperature values
            if temp_value == 0.0:
                # Zero might indicate no calibration curve or over-range
                # Try reading resistance instead
                resistance = self.read_resistance(input_channel)
                if isinstance(resistance, (int, float)) and resistance > 0:
                    return resistance  # Return resistance if temperature is unavailable
                return "T_OVER"
            return temp_value
        except ValueError:
            # Check for text indicators of over-range
            if any(indicator in response.upper() for indicator in ['OVER', 'T.', 'T_', 'OVERLD']):
                return "T_OVER"
            return response

    # Doesn't really work yet
    def read_sensor(self, input_channel):
        """
        Generic sensor reading
        
        Args:
            input_channel (int): Input channel number
            
        Returns:
            float: Resistance in Ohms or temperature in Kelvin
            str: Error message if over-range or no response
        """
        # For the 370, sensor readings are primarily resistance
        return self.read_resistance(input_channel)

    def scan_inputs(self, input_list=None):
        """
        Scan multiple inputs and return results
        
        Args:
            input_list (list): List of input channels to scan (default: [1,2,3,4,5])
            
        Returns:
            dict: Dictionary of {input: value} pairs
        """
        if input_list is None:
            input_list = [1, 2, 3, 4, 5]  # Default inputs to scan
        
        results = {}
        for input_ch in input_list:
            try:
                temp = self.read_temperature(input_ch)
                resistance = self.read_resistance(input_ch)
                results[input_ch] = {
                    'temperature': temp,
                    'resistance': resistance
                }
            except Exception as e:
                results[input_ch] = {
                    'temperature': f'ERROR: {e}',
                    'resistance': f'ERROR: {e}'
                }
        
        return results

    # Doesn't work yet
    def get_status(self, input_channel):
        """
        Get status of specified input channel
        
        Args:
            input_channel (int): Input channel number
            
        Returns:
            int: Status code
            str: "NO_RESPONSE" if communication error
        """
        response = self.send_command(f"RDGST? {input_channel}")
        if response is None or response == "":
            return "NO_RESPONSE"
        
        try:
            return int(response)
        except ValueError:
            return response

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



if __name__ == "__main__":
    # Example usage when run directly
    print("Lakeshore 370 Temperature Reader Test")
    print("=" * 40)
    
    try:
        with TemperatureReader() as reader:
            # Get device info
            print(f"Device ID: {reader.get_identification()}")
            print(f"Baud Rate: {reader.get_baud_rate()}")
            print()
            
            # Scan first 5 inputs
            print("Scanning inputs 1-5:")
            results = reader.scan_inputs([1, 2, 3, 4, 5])
            
            for input_ch, data in results.items():
                print(f"Input {input_ch}:")
                print(f"  Temperature: {data['temperature']}")
                print(f"  Resistance: {data['resistance']}")
                print()
                
    except Exception as e:
        print(f"Error: {e}")