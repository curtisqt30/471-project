from __future__ import annotations
import argparse
import os
import signal
import socket
import threading
import json
from typing import Tuple, List
from pathlib import Path

# Global stop event for graceuful shutdown
stop = threading.Event()
workers: List[threading.Thread] = []

# Server data directory for file storage
DATA_DIR = Path("server_data")

# Simple FTP protocol handler with JSON
class FTPProtocol:
    @staticmethod
    def create_response(status: str, message: str = "", data: dict = None) -> bytes:
        """Create JSON response message"""
        response = {
            "status": status,
            "message": message
        }
        if data:
            response["data"] = data
        return (json.dumps(response) + "\n").encode('utf-8')
    
    @staticmethod
    def parse_command(data: bytes) -> dict:
        """Parse the incoming command from client"""
        try:
            text = data.decode('utf-8').strip()
            parts = text.split(maxsplit=1)
            command = parts[0].upper() if parts else ""
            argument = parts[1] if len(parts) > 1 else ""
            return {"command": command, "argument": argument}
        except Exception:
            return {"command": "", "argument": ""}

# Handle individual client connections
def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    peer = f"{addr[0]}:{addr[1]}"
    print(f"[+] connected: {peer}")

    protocol = FTPProtocol()

    try:
        with conn:
            # Welcome message
            welcome = protocol.create_response("OK", f"Welcome to FTP Server. Commands: LS, GET <file>, PUT <file>, EXIT")
            conn.sendall(welcome)

            while not stop.is_set():
                # Receive command (up to 4KB)
                data = conn.recv(4096)
                if not data:
                    break
                
                # Parse commands
                cmd_data = protocol.parse_command(data)
                command = cmd_data["command"]
                argument = cmd_data["argument"]

                print(f"[{peer}] Command: {command} {argument}")

                # Process commands
                if command == "EXIT":
                    response = protocol.create_response("OK", "Goodbye")
                    conn.sendall(response)
                    break
                elif command == "LS":
                    # TODO list files in server data directory
                    pass
                elif command == "GET":
                    # TODO send file to client
                    pass
                elif command == "PUT":
                    # TODO receive file from client
                    pass 
                
    except ConnectionResetError:
        print(f"[!] Connection reset by {peer}")
    except Exception as e:
        print(f"[!] Error with {peer}: {e}")
    finally:
        print(f"[-] Disconnected: {peer}")

# Create server data directory if it doesn't exist
def setup_server_directory():
    DATA_DIR.mkdir(exist_ok=True)
    print(f"[server] Data directory: {DATA_DIR.absolute()}")

# Setup signal handlers for graceful shutdonw
def setup_signals() -> None:
    def signal_handler(signum, frame):
        print(f"\n[server] Received signal {signum}; shutting down...")
        stop.set()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, signal_handler)
        except Exception:
            pass

def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-client FTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5050, help="Port to bind to")
    args = parser.parse_args()

    # Setup
    setup_signals()
    setup_server_directory()

    # Create server socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen(5)  # Allow up to 5 pending connections
        server_socket.settimeout(1.0)  # Timeout for checking stop event
        
        print(f"[server] FTP Server listening on {args.host}:{args.port}")
        print(f"[server] Commands: LS, GET <file>, PUT <file>, EXIT")
        print(f"[server] Press Ctrl+C to stop")
        
        try:
            while not stop.is_set():
                try:
                    conn, addr = server_socket.accept()
                except socket.timeout:
                    continue
                
                # Create thread for each client
                thread = threading.Thread(
                    target=handle_client, 
                    args=(conn, addr), 
                    daemon=True
                )
                thread.start()
                workers.append(thread)
                
        finally:
            # Cleanup
            print("[server] Shutting down...")
            try:
                server_socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            
            # Wait for worker threads
            for thread in workers:
                thread.join(timeout=1.0)
            
            print("[server] Server stopped")

if __name__ == "__main__":
    main()
