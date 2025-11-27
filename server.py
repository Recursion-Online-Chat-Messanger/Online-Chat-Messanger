#!/usr/bin/env python3
import socket
import time
from typing import Dict, Tuple

MAX_PACKET_SIZE = 4096
IDLE_TIMEOUT = 60  # seconds


class ChatServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 5000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # key: (ip, port), value: last_seen_timestamp
        self.clients: Dict[Tuple[str, int], float] = {}

    def bind(self) -> None:
        self.sock.bind((self.host, self.port))
        print(f"[SERVER] UDP chat server listening on {self.host}:{self.port}")

    @staticmethod
    def decode_packet(data: bytes):
        """
        Packet format:
        [0]       : 1 byte, username length (0–255)
        [1:1+N]   : username bytes (UTF-8)
        [1+N: ]   : message bytes (UTF-8)
        """
        if not data:
            return None, None

        username_len = data[0]
        if len(data) < 1 + username_len:
            return None, None

        username_bytes = data[1:1 + username_len]
        message_bytes = data[1 + username_len:]

        username = username_bytes.decode("utf-8", errors="replace")
        message = message_bytes.decode("utf-8", errors="replace")
        return username, message

    def cleanup_clients(self, now: float) -> None:
        stale = [addr for addr, last in self.clients.items()
                 if now - last > IDLE_TIMEOUT]
        for addr in stale:
            print(f"[INFO] Removing idle client {addr}")
            del self.clients[addr]

    def broadcast(self, data: bytes) -> None:
        for client_addr in list(self.clients.keys()):
            try:
                self.sock.sendto(data, client_addr)
            except OSError as e:
                print(f"[WARN] Failed to send to {client_addr}: {e}")

    def serve_forever(self) -> None:
        self.bind()
        try:
            while True:
                try:
                    data, addr = self.sock.recvfrom(MAX_PACKET_SIZE)
                except KeyboardInterrupt:
                    print("\n[SERVER] Shutting down.")
                    break

                now = time.time()
                # register/update client
                self.clients[addr] = now

                username, message = self.decode_packet(data)
                if username is None:
                    print(f"[WARN] Received malformed packet from {addr}")
                    continue

                ts = time.strftime("%H:%M:%S", time.localtime(now))
                print(f"[{ts}] {addr} {username}: {message}")

                # cleanup idle clients
                self.cleanup_clients(now)

                # relay original packet (username + message) to all
                self.broadcast(data)
        finally:
            self.sock.close()


def main():
    server = ChatServer(host="0.0.0.0", port=5000)
    server.serve_forever()


if __name__ == "__main__":
    main()

