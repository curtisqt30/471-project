from __future__ import annotations
import argparse
import signal
import socket
import threading
from typing import Tuple, List

stop = threading.Event()
workers: List[threading.Thread] = []

def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    peer = f"{addr[0]}:{addr[1]}"
    print(f"[+] connected: {peer}")
    try:
        with conn:
            while not stop.is_set():
                data = conn.recv(4096)
                if not data:
                    break
                print(f"[{peer}] {data.decode('utf-8', errors='replace')}", end="")
    except Exception as e:
        print(f"[!] error with {peer}: {e}")
    finally:
        print(f"[-] disconnected: {peer}")

def _set_signals() -> None:
    def _handler(signum, frame):
        print(f"\n[server] received signal {signum}; shutting down…")
        stop.set()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handler)
        except Exception:
            pass  

def main() -> None:
    parser = argparse.ArgumentParser(description="Basic print server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()

    _set_signals()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.host, args.port))
        s.listen()
        s.settimeout(1.0)  
        print(f"[server] listening on {args.host}:{args.port} (Ctrl+C to stop)")

        try:
            while not stop.is_set():
                try:
                    conn, addr = s.accept()
                except socket.timeout:
                    continue
                t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                t.start()
                workers.append(t)
        finally:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            s.close()
            for t in list(workers):
                t.join(timeout=1.5)
            print("[server] stopped")

if __name__ == "__main__":
    main()
