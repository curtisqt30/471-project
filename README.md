# 471-project

## Create virtual environment
- macOS/Linx
`python3 -m venv .venv`
`source .venv/bin/activate`

- Windows
`python -m venv .venv`
`.\.venv\Scripts\Activate.ps1`

- Install requirements
`pip install -r requirements.txt`

## Run the server
`cd src`
`python -m server.main`

## Run the client
`cd src`
`python -m client.main <host> <port>`


## Project Overview
Server:
- Stores files in a server data directory
- Handles multiple clients (thread-per-connection)

Client use cases examples:
- `client> LS` = list server files
- `client> GET notes.txt` = download a file to client's current directory
- `client> PUT image.jpg` = uploads a local file to the server's data directory
- `client> EXIT` = closes the session