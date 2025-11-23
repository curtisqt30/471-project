from __future__ import annotations
import argparse
import socket
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# FTP client with command handling
class FTPClient: 
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket: Optional[Socket.socket] = None
        self.connected = False

    # Connect to the FTP SErver
    def connect(self) -> bool:
        try:
            self.socket = socket.create_connection((self.host, self.port), timeout=10)
            self.connected = True
            
            # Receive welcome message
            response = self.receive_response()
            if response:
                print(f"[server] {response.get('message', 'Connected')}")
                return True
            return False
        except Exception as e:
            print(f"[error] Failed to connect: {e}")
            return False

    # Disconnect from the server
    def disconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False

    # Send a command to the server
    def send_command(self, command: str) -> bool:
        pass

    # Receive and parse JSON server response
    def receive_response(self) -> Optional[Dict[str, Any]]:
        if not self.socket:
            return None
        
        try:
            # Receive up to 8KB of data
            data = self.socket.recv(8192)
            if not data:
                self.connected = False
                return None
            
            # Parse JSON response
            response_text = data.decode('utf-8').strip()
            # Handle multiple JSON objects (split by newlines)
            for line in response_text.split('\n'):
                if line:
                    return json.loads(line)
            return None
        except json.JSONDecodeError as e:
            print(f"[error] Invalid response format: {e}")
            print(f"[debug] Raw response: {data.decode('utf-8', errors='replace')}")
            return None
        except Exception as e:
            print(f"[error] Failed to receive response: {e}")
            self.connected = False
            return None

    # LS command - view server data directory
    def command_ls(self) -> bool:
        if not self.send_command("LS"):
            return False
        
        response = self.receive_response()
        if response:
            if response.get('status') == 'OK':
                files = response.get('data', {}).get('files', [])
                print(f"\n[server] {response.get('message', '')}")
                if files:
                    print("Files on server:")
                    for file in files:
                        print(f"  - {file}")
                else:
                    print("  (no files)")
                return True
            else:
                print(f"[server] Error: {response.get('message', 'Unknown error')}")
        return False

    # GET Command - download files
    def command_get(self, filename: str) -> bool:
        if not filename:
            print("[error] GET requires a filename")
            return False
        
        if not self.send_command(f"GET {filename}"):
            return False
        
        # Receive metadata response
        response = self.receive_response()
        if response:
            if response.get('status') == 'OK':
                file_info = response.get('data', {})
                print(f"[server] {response.get('message', '')}")
                print(f"  File: {file_info.get('filename', filename)}")
                print(f"  Size: {file_info.get('size', 0)} bytes")
                
                # Receive file data
                data_response = self.receive_response()
                if data_response and data_response.get('status') == 'FILE_DATA':
                    content = data_response.get('data', {}).get('content', '')
                    
                    # Save to local file
                    local_path = Path(filename)
                    try:
                        local_path.write_text(content)
                        print(f"[client] File saved: {local_path.absolute()}")
                        return True
                    except Exception as e:
                        print(f"[error] Failed to save file: {e}")
                elif data_response:
                    print(f"[server] {data_response.get('message', 'Failed to receive file')}")
            else:
                print(f"[server] Error: {response.get('message', 'Unknown error')}")
        return False

    # PUT Command - upload files
    def command_put(self, filename: str) -> bool:
        if not filename:
            print("[error] PUT requires a filename")
            return False
        
        # Check if local file exists
        local_path = Path(filename)
        if not local_path.exists():
            print(f"[error] Local file not found: {filename}")
            return False
        
        if not local_path.is_file():
            print(f"[error] Not a file: {filename}")
            return False
        
        # Send PUT command
        if not self.send_command(f"PUT {local_path.name}"):
            return False
        
        # Wait for ready response
        response = self.receive_response()
        if response and response.get('status') == 'READY':
            print(f"[server] {response.get('message', '')}")
            
            try:
                # Read file content
                file_size = local_path.stat().st_size
                
                if file_size < 8192:  # Small file (< 8KB)
                    try:
                        # Try to send as text
                        content = local_path.read_text()
                        file_data = json.dumps({"content": content})
                        self.socket.sendall(file_data.encode('utf-8'))
                    except UnicodeDecodeError:
                        # Send as binary
                        content = local_path.read_bytes()
                        self.socket.sendall(content)
                    
                    # Receive confirmation
                    response = self.receive_response()
                    if response:
                        if response.get('status') == 'OK':
                            print(f"[server] {response.get('message', 'File uploaded')}")
                            return True
                        else:
                            print(f"[server] Error: {response.get('message', 'Upload failed')}")
                else:
                    print(f"[error] File too large for current implementation (max 8KB)")
                    print(f"[error] File size: {file_size} bytes")
            except Exception as e:
                print(f"[error] Failed to read/send file: {e}")
        elif response:
            print(f"[server] Error: {response.get('message', 'Server not ready')}")
        
        return False

    # EXIT command - disconnect
    def command_exit(self) -> bool:
        if not self.send_command("EXIT"):
            return False

        response = self.receive_response()
        if response:
            print(f"[server] {response.get('message', 'Disconnecting')}")
        
        self.disconnect()
        return True

    # run interactive command loop
    def run_interactive(self):
        print("\nFTP Client Commands:")
        print("  LS              - List files on server")
        print("  GET <filename>  - Download file from server")
        print("  PUT <filename>  - Upload file to server")
        print("  EXIT            - Disconnect and quit")
        print("  HELP            - Show this help")
        print()
        
        while self.connected:
            try:
                # Get user input
                user_input = input("ftp> ").strip()
                
                if not user_input:
                    continue
                
                # Parse command
                parts = user_input.split(maxsplit=1)
                command = parts[0].upper()
                argument = parts[1] if len(parts) > 1 else ""
                
                # Execute command
                if command == "LS":
                    self.command_ls()
                elif command == "GET":
                    self.command_get(argument)
                elif command == "PUT":
                    self.command_put(argument)
                elif command == "EXIT" or command == "QUIT":
                    self.command_exit()
                    break
                elif command == "HELP":
                    print("\nCommands:")
                    print("  LS              - List files on server")
                    print("  GET <filename>  - Download file from server")
                    print("  PUT <filename>  - Upload file to server")
                    print("  EXIT            - Disconnect and quit")
                else:
                    print(f"[error] Unknown command: {command}")
                    print("Type HELP for available commands")
                    
            except KeyboardInterrupt:
                print("\n[client] Interrupted by user")
                self.command_exit()
                break
            except EOFError:
                print("\n[client] End of input")
                self.command_exit()
                break
            except Exception as e:
                print(f"[error] Unexpected error: {e}")
                
        print("[client] Disconnected")

def main() -> None:
    parser = argparse.ArgumentParser(description="FTP Client")
    parser.add_argument("host", help="FTP server host/IP")
    parser.add_argument("port", type=int, help="FTP server port")
    parser.add_argument("--command", "-c", help="Execute single command and exit")
    args = parser.parse_args()

    # Create Client
    client = FTPClient(args.host, args.port)

    # Connect to Server
    print(f"[client] Connecting to {args.host}:{args.port}...")
    if not client.connect():
        print("[client] Failed to connect to server")
        sys.exit(1)
    
    print("[client] Connected successfully")

    if args.command:
        # Execute single command
        parts = args.command.split(maxsplit=1)
        command = parts[0].upper()
        argument = parts[1] if len(parts) > 1 else ""
        
        if command == "LS":
            client.command_ls()
        elif command == "GET":
            client.command_get(argument)
        elif command == "PUT":
            client.command_put(argument)
        elif command == "EXIT":
            client.command_exit()
        else:
            print(f"[error] Unknown command: {command}")
    else:
        # Run interactive mode
        client.run_interactive()

    # ensure disconnection
    if client.connected:
        client.disconnect()

if __name__ == "__main__":
    main()
