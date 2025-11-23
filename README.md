# FTP Server and Client Project
## CPSC 471 - Network Programming Project

### Authors

## Project Overview
- A multi-client FTP server and client implemention in Python that supports basic file transfer operations

### Requirements:
- Python 3.7 or higher
- No external dependences (uses standard library only)

### Server:
- Stores files in a server data directory
- Handles multiple clients (thread-per-connection)
- Error Handling: error messages and connection management

### Client:
- Command-line interface for FTP operations
- Error Handling: error messages and connection management

### FTP Commands
| Command | Description | Example |
|---------|-------------|---------|
| `LS` | List all files on the server | `ftp> LS` |
| `GET <file>` | Download a file from server | `ftp> GET welcome.txt` |
| `PUT <file>` | Upload a file to server | `ftp> PUT document.txt` |
| `EXIT` | Disconnect and quit | `ftp> EXIT` |
| `HELP` | Show available commands | `ftp> HELP` |

Client use cases examples:
- `ftp> LS` = list server files
- `ftp> GET notes.txt` = download a file to client's current directory
- `ftp> PUT image.jpg` = uploads a local file to the server's data directory
- `ftp> EXIT` = closes the session

## Instructions
### 1) (optional) Create virtual environment
- macOS/Linx
```bash
python3 -m venv .venv
source .venv/bin/activate
```
- Windows
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
- Install requirements
```bash
pip install -r requirements.txt
```
### 2) Start the server (in one terminal)
```bash
cd src
python -m server.main --host 0.0.0.0 --port 5050
```
### 3) Start the client (in another terminal)
```bash
cd src
python -m client.main 127.0.0.1 5050`
```

## User Guide: File Storage

### Directory Structure
```
src/
├── client_data/    ← Your local files (uploads and downloads)
└── server_data/    ← Server files
```

Both directories are created automatically when you first run the server and client.

### Uploading Files (PUT)
1. Place files you want to upload in the `client_data/` directory
2. Use the `PUT` command with just the filename:
   ```bash
   ftp> PUT myfile.txt
   ```
3. The client reads from `client_data/myfile.txt` and uploads to `server_data/myfile.txt`

### Downloading Files (GET)
1. Use `LS` to see available files on the server
2. Use the `GET` command with the filename:
   ```bash
   ftp> GET serverfile.txt
   ```
3. The file downloads to `client_data/serverfile.txt`
