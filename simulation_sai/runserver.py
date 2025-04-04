import asyncio
import serial
import json
import threading
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer

class SerialConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serial_threads = {}  # Store threads for each COM port
        self.serial_connections = {}  # Store serial connection objects

    async def connect(self):
        self.group_name = 'serial_group'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print("WebSocket Connection Established.")

    async def disconnect(self, close_code):
        # Stop all threads and close serial ports on disconnect
        for com_port, ser in self.serial_connections.items():
            if ser and ser.is_open:
                ser.close()
        self.serial_threads.clear()
        self.serial_connections.clear()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("WebSocket Connection Closed.")

    async def receive(self, text_data):
        try:
            print(f"Received raw data: {text_data}")  # Log the raw WebSocket data
            data = json.loads(text_data)
            command = data.get('command')

            # Access 'com_port' instead of 'com_ports'
            com_ports = data.get("com_port")
            print(f"Received com_ports: {com_ports}")

            if com_ports is None:
                print("No COM ports found in the data!")
            else:
                # Process the com_ports (assuming it's a list)
                print(f"COM Ports to process: {com_ports}")

            if command in ['start_serial', 'start_communication']:
                await self.start_serial_communication(data)
        except Exception as e:
            print(f"Error processing received data: {e}")


    async def start_serial_communication(self, data):
        """
        Starts serial communication on multiple COM ports in separate threads.
        """
        
        self.card = data.get("card")  # Store card type for validation
        com_ports = data.get('com_port')  # Expecting a list of COM ports
        baud_rate = data.get('baud_rate')
        parity = data.get('parity')
        stopbit = data.get('stopbit')
        databit = data.get('databit')

        # If com_ports is not a list, convert it into one
        if isinstance(com_ports, str):
            com_ports = [com_ports]  # Convert string to list if it's a single port
        elif com_ports is None:
            print("Error: 'com_ports' cannot be None.")
            return

        # Now check if com_ports is a list (this is no longer necessary if it's already converted)
        if not isinstance(com_ports, list) or not com_ports:
            print("Error: 'com_ports' must be a list of COM port names.")
            return

        # Now com_ports is guaranteed to be a list, so we proceed
        print(f"COM Ports to process: {com_ports}")

        # Start separate thread for each COM port
        for com_port in com_ports:
            if com_port not in self.serial_threads:  # Avoid duplicate threads
                self.serial_threads[com_port] = threading.Thread(
                    target=self.serial_read_thread,
                    args=(com_port, baud_rate, parity, stopbit, databit),
                    daemon=True
                )
                self.serial_threads[com_port].start()
                print(f"✅ Serial thread started for {com_port}")


    def configure_serial_port(self, com_port, baud_rate, parity, stopbits, bytesize):
        """
        Configures and returns a serial port connection.
        """
        try:
            if not all([com_port, baud_rate, parity, stopbits, bytesize]):
                print(f"⚠️ Missing parameters for {com_port}.")
                return None

            ser = serial.Serial(
                port=com_port,
                baudrate=int(baud_rate),
                bytesize=int(bytesize),
                stopbits=float(stopbits),
                parity=parity[0].upper(),
                timeout=5  # Prevents excessive CPU usage
            )
            self.serial_connections[com_port] = ser  # Store connection
            print(f"✅ Connected to {com_port}.")
            return ser
        except (ValueError, serial.SerialException) as e:
            print(f"❌ Error opening {com_port}: {e}")
            return None

    def serial_read_thread(self, com_port, baud_rate, parity, stopbit, databit):
        """
        Reads data from each COM port in a separate thread.
        """
        try:
            ser = self.configure_serial_port(com_port, baud_rate, parity, stopbit, databit)
            if not ser:
                return

            accumulated_data = ""
            previous_data = ""  # Store last message to check for updates

            while ser and ser.is_open:
                print(f"📡 Listening on {com_port}...")  # Debugging

                received_data = ser.read_until(expected=b'\r').decode('ASCII').strip()
                if received_data:
                    accumulated_data += received_data

                    if '\r' in accumulated_data:
                        messages = accumulated_data.split('\r')
                        for message in messages:
                            if message.strip():
                                # Validate LVDT_4CH or PIEZO_4CH
                                if hasattr(self, 'card') and self.card in ["LVDT_4CH", "PIEZO_4CH"]:
                                    extracted_values = self.extract_values(message.strip())

                                    if len(extracted_values) > 4:
                                        print(f"⚠️ Invalid data ({len(extracted_values)} values) for {self.card}. Ignored!")
                                        continue  # Ignore invalid data

                                    # Send new or updated data
                                    if message.strip() != previous_data:
                                        previous_data = message.strip()
                                        print(f"📨 {com_port} Data: {message.strip()}")

                                        # Send valid message to WebSocket
                                        async_to_sync(self.channel_layer.group_send)(self.group_name, {
                                            'type': 'serial_message',
                                            'message': message.strip(),
                                            'com_port': com_port
                                        })

                        accumulated_data = ""  # Reset buffer

        except Exception as e:
            print(f"❌ Error in serial read thread ({com_port}): {str(e)}")
        finally:
            if ser and ser.is_open:
                ser.close()

    def extract_values(self, message):
        """
        Extracts values from serial message in format A+260000B+564765C+456345D+675678
        """
        import re
        pattern = r'[A-Za-z][^A-Za-z0-9\s]\d+'
        matches = re.findall(pattern, message)
        return matches

    async def serial_message(self, event):
        """
        Sends serial data to WebSocket clients.
        """
        await self.send(text_data=json.dumps({
            'com_port': event['com_port'],
            'message': event['message']
        }))



