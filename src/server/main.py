from __future__ import annotations
import argparse
import os
import signal
import socket
import threading
import json
from typing import Tuple, List
from pathlib import Path
from server.handlers import LoggingHandler

# Global stop event for graceful shutdown
stop = threading.Event()
workers: List[threading.Thread] = []

# Server data directory for file storage
DATA_DIR = Path("server_data")

# Create Logger instance
logger = LoggingHandler()

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
    print(f"[+] Connected: {peer}")

    # Log connection
    logger.log_connection(addr)
    
    protocol = FTPProtocol()
    
    try:
        with conn:
            # Send welcome message
            welcome = protocol.create_response("OK", f"Welcome to FTP Server. Commands: LS, GET <file>, PUT <file>, EXIT")
            conn.sendall(welcome)
            
            while not stop.is_set():
                # Receive command (up to 4KB)
                data = conn.recv(4096)
                if not data:
                    break
                
                # Parse command
                cmd_data = protocol.parse_command(data)
                command = cmd_data["command"]
                argument = cmd_data["argument"]
                
                print(f"[{peer}] Command: {command} {argument}")

                # Log command
                logger.log_command(addr, command, argument)
                
                # Process commands
                if command == "EXIT":
                    response = protocol.create_response("OK", "Goodbye")
                    conn.sendall(response)
                    break
                    
                elif command == "LS":
                    # List files in server data directory
                    try:
                        if DATA_DIR.exists():
                            files = [f.name for f in DATA_DIR.iterdir() if f.is_file()]
                            response = protocol.create_response(
                                "OK", 
                                f"Files: {len(files)}", 
                                {"files": files}
                            )
                        else:
                            response = protocol.create_response("OK", "No files", {"files": []})
                    except Exception as e:
                        logger.log_error(addr, f"LS failed: {e}")
                        response = protocol.create_response("ERROR", f"Failed to list files: {e}")
                    conn.sendall(response)
                    
                elif command == "GET":
                    # Send file to client
                    if not argument:
                        response = protocol.create_response("ERROR", "GET requires filename")
                        conn.sendall(response)
                    else:
                        file_path = DATA_DIR / argument
                        if file_path.exists() and file_path.is_file():
                            try:
                                # First send metadata
                                file_size = file_path.stat().st_size
                                metadata = protocol.create_response(
                                    "OK", 
                                    f"Sending {argument}",
                                    {"filename": argument, "size": file_size}
                                )
                                conn.sendall(metadata)
                                
                                # Then send file content
                                with open(file_path, 'rb') as f:
                                    file_content = f.read()
                                    # For now, if it's a text file and small, send as JSON
                                    if file_size < 1024:  # Less than 1KB
                                        try:
                                            text_content = file_content.decode('utf-8')
                                            response = protocol.create_response(
                                                "FILE_DATA",
                                                "",
                                                {"content": text_content}
                                            )
                                            conn.sendall(response)
                                            
                                            # Log successful download
                                            logger.log_download(addr, argument, file_size)
                                        except UnicodeDecodeError:
                                            response = protocol.create_response(
                                                "ERROR",
                                                "Binary file transfer not yet implemented"
                                            )
                                            conn.sendall(response)
                                            logger.log_error(addr, f"Binary file not supported: {argument}")
                                    else:
                                        response = protocol.create_response(
                                            "ERROR",
                                            "Large file transfer not yet implemented"
                                        )
                                        conn.sendall(response)
                                        logger.log_error(addr, f"File too large: {argument} ({file_size} bytes)")
                            except Exception as e:
                                # Log error
                                logger.log_error(addr, f"GET failed: {e}")
                                response = protocol.create_response("ERROR", f"Failed to read file: {e}")
                                conn.sendall(response)
                        else:
                            error_msg = f"File not found: {argument}"
                            logger.log_error(addr, error_msg)
                            response = protocol.create_response("ERROR", error_msg)
                            conn.sendall(response)
                    
                elif command == "PUT":
                    # Receive file from client
                    if not argument:
                        response = protocol.create_response("ERROR", "PUT requires filename")
                        conn.sendall(response)
                    else:
                        # Send ready signal
                        response = protocol.create_response(
                            "READY", 
                            f"Ready to receive {argument}"
                        )
                        conn.sendall(response)
                        
                        # Wait for file data (simplified version)
                        file_data = conn.recv(8192)  # Receive up to 8KB
                        if file_data:
                            try:
                                # Try to parse as JSON first (for text files)
                                json_data = json.loads(file_data.decode('utf-8'))
                                if "content" in json_data:
                                    file_path = DATA_DIR / argument
                                    file_path.write_text(json_data["content"])
                                    file_size = len(json_data["content"])
                                    
                                    # Log successful upload
                                    logger.log_upload(addr, argument, file_size)
                                    
                                    response = protocol.create_response(
                                        "OK",
                                        f"File {argument} saved successfully"
                                    )
                                else:
                                    response = protocol.create_response(
                                        "ERROR",
                                        "Invalid file data format"
                                    )
                                    logger.log_error(addr, f"Invalid PUT data format: {argument}")
                            except json.JSONDecodeError:
                                # Handle as binary data
                                file_path = DATA_DIR / argument
                                file_path.write_bytes(file_data)
                                file_size = len(file_data)
                                
                                # Log successful upload
                                logger.log_upload(addr, argument, file_size)
                                
                                response = protocol.create_response(
                                    "OK",
                                    f"File {argument} saved successfully"
                                )
                            except Exception as e:
                                logger.log_error(addr, f"PUT failed: {e}")
                                response = protocol.create_response("ERROR", f"Failed to save file: {e}")
                        else:
                            error_msg = "No file data received"
                            logger.log_error(addr, error_msg)
                            response = protocol.create_response("ERROR", error_msg)
                        conn.sendall(response)
                    
                else:
                    error_msg = f"Unknown command: {command}"
                    logger.log_error(addr, error_msg)
                    response = protocol.create_response(
                        "ERROR", 
                        f"{error_msg}. Use LS, GET, PUT, or EXIT"
                    )
                    conn.sendall(response)
                    
    except ConnectionResetError:
        print(f"[!] Connection reset by {peer}")
        logger.log_error(addr, "Connection reset")
    except Exception as e:
        print(f"[!] Error with {peer}: {e}")
        logger.log_error(addr, f"Unexpected error: {e}")
    finally:
        print(f"[-] Disconnected: {peer}")
        # Log disconnection
        logger.log_disconnect(addr)

# Create server data directory if it doesn't exist
def setup_server_directory():
    DATA_DIR.mkdir(exist_ok=True)
    print(f"[server] Data directory: {DATA_DIR.absolute()}")

    # Create a sample file for testing
    sample_file = DATA_DIR / "TestFile.txt"
    if not sample_file.exists():
        sample_file.write_text("This is a sample file.")
        print(f"[server] Created sample file: TestFile.txt")


# Setup signal handlers for graceful shutdown
def setup_signals() -> None:
    def signal_handler(signum, frame):
        print(f"\n[server] Received signal {signum}; shutting down...")
        logger.log_server_event("Shutdown signal received")
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

    # Log server startup
    logger.log_server_event(f"Server starting on {args.host}:{args.port}")

    # Create server socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((args.host, args.port))
        server_socket.listen(5)  # Allow up to 5 pending connections
        server_socket.settimeout(1.0)  # Timeout for checking stop event
        
        print(f"[server] FTP Server listening on {args.host}:{args.port}")
        print(f"[server] Commands: LS, GET <file>, PUT <file>, EXIT")
        print(f"[server] Press Ctrl+C to stop")
        
        # Log server ready
        logger.log_server_event(f"Server listening on {args.host}:{args.port}")
        
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
            logger.log_server_event("Server shutting down")
            
            try:
                server_socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            
            # Wait for worker threads
            for thread in workers:
                thread.join(timeout=1.0)
            
            print("[server] Server stopped")
            logger.log_server_event("Server stopped")

if __name__ == "__main__":
    main()