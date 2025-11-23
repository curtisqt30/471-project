from typing import Tuple, Optional, Dict, Any
import socket
import json
from pathlib import Path

# Handler for file transfer operations
class FileTransferHandler:

    # Initialize with server data directory
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    # Handle LS command
    def handle_ls(self) -> Tuple[str, Dict[str, Any]]:
        try:
            if self.data_dir.exists():
                files = [f.name for f in self.data_dir.iterdir() if f.is_file()]
                return "OK", {
                    "message": f"Files: {len(files)}",
                    "data": {"files": files}
                }
            else:
                return "OK", {
                    "message": "No files",
                    "data": {"files": []}
                }
        except Exception as e:
            return "ERROR", {"message": f"Failed to list files: {e}"}
    
    # Handle GET command
    def handle_get_metadata(self, filename: str) -> Tuple[str, Dict[str, Any]]:
        file_path = self.data_dir / filename
        
        if not file_path.exists():
            return "ERROR", {"message": f"File not found: {filename}"}
        
        if not file_path.is_file():
            return "ERROR", {"message": f"Not a file: {filename}"}
        
        try:
            file_size = file_path.stat().st_size
            return "OK", {
                "message": f"Sending {filename}",
                "data": {
                    "filename": filename,
                    "size": file_size
                }
            }
        except Exception as e:
            return "ERROR", {"message": f"Failed to get file info: {e}"}
    
    # Handle PUT command
    def read_file(self, filename: str, max_size: int = 8192) -> Tuple[bool, bytes]:
        file_path = self.data_dir / filename
        
        try:
            file_size = file_path.stat().st_size
            if file_size > max_size:
                return False, b"File too large"
            
            with open(file_path, 'rb') as f:
                return True, f.read()
        except Exception as e:
            return False, str(e).encode('utf-8')
    
    # Handle PUT command
    def write_file(self, filename: str, content: bytes) -> Tuple[bool, str]:
        file_path = self.data_dir / filename
        
        try:
            file_path.write_bytes(content)
            return True, f"File {filename} saved successfully"
        except Exception as e:
            return False, f"Failed to save file: {e}"

# Handler for FTP protocol operations
class BinaryTransferHandler:
    
    CHUNK_SIZE = 4096
    
    @staticmethod
    def send_file_chunked(sock: socket.socket, file_path: Path) -> bool:
        """Send file in chunks (not yet implemented)"""
        # TODO: Implement chunked transfer for large files
        # implemented in Part 2
        pass
    
    @staticmethod
    def receive_file_chunked(sock: socket.socket, file_path: Path, file_size: int) -> bool:
        """Receive file in chunks (not yet implemented)"""
        # TODO: Implement chunked receive for large files
        #  implemented in Part 2
        pass

# Handler for authentication and user management
class AuthenticationHandler:
    
    # Initialize with user store
    def __init__(self):
        # Simple in-memory user store for demonstration
        self.users = {
            "admin": "password123",
            "user1": "pass1",
            "guest": "guest"
        }
    
    # Authenticate user
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user (not yet integrated)"""
        return self.users.get(username) == password
    
    # Add new user
    def add_user(self, username: str, password: str) -> bool:
        """Add new user (not yet integrated)"""
        if username in self.users:
            return False
        self.users[username] = password
        return True

# Handler for command parsing and validation
class CommandParser:
    
    # List of valid commands
    VALID_COMMANDS = ["LS", "GET", "PUT", "EXIT", "HELP", "CD", "PWD", "MKDIR", "DELETE"]
    
    @classmethod
    def parse(cls, command_str: str) -> Tuple[str, str]:
        """Parse command string into command and argument"""
        parts = command_str.strip().split(maxsplit=1)
        command = parts[0].upper() if parts else ""
        argument = parts[1] if len(parts) > 1 else ""
        
        return command, argument
    
    @classmethod
    def validate(cls, command: str) -> bool:
        """Check if command is valid"""
        return command in cls.VALID_COMMANDS
    
    @classmethod
    def requires_argument(cls, command: str) -> bool:
        """Check if command requires an argument"""
        return command in ["GET", "PUT", "CD", "MKDIR", "DELETE"]

# Handler for error management
class ErrorHandler:
    
    @staticmethod
    def format_error(error_type: str, message: str) -> Dict[str, Any]:
        """Format error response"""
        return {
            "status": "ERROR",
            "error_type": error_type,
            "message": message
        }
    
    @staticmethod
    def log_error(client_addr: Tuple[str, int], error: Exception):
        """Log error to console (could be extended to file)"""
        print(f"[ERROR] Client {client_addr[0]}:{client_addr[1]} - {error}")


# TODO: these handlers rqeuired for Part 2
class DirectoryHandler:
    """Handle directory operations (CD, PWD, MKDIR)"""
    pass


class SecurityHandler:
    """Handle encryption and secure transfers"""
    pass


class LoggingHandler:
    """Handle server activity logging"""
    pass