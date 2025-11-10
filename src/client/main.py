from __future__ import annotations
import argparse
import socket
import sys

def main() -> None:
    parser = argparse.ArgumentParser(description="Basic text sender")
    parser.add_argument("host", help="server host/ip")
    parser.add_argument("port", type=int, help="server port")
    args = parser.parse_args()

    with socket.create_connection((args.host, args.port)) as sock:
        print(f"[client] connected to {args.host}:{args.port}")
        print("[client] type lines to send; Ctrl+C or empty line to quit.")
        try:
            for line in sys.stdin:
                if not line.strip():
                    break
                sock.sendall(line.encode("utf-8"))
            print(sock.recv(1024).decode("utf-8", errors="replace"))
        except KeyboardInterrupt:
            pass
        finally:
            print("[client] closing")

if __name__ == "__main__":
    main()
