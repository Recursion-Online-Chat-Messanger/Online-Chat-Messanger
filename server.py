#!/usr/bin/env python3
import socket
import time
from typing import Dict, Tuple

MAX_PACKET_SIZE = 4096
IDLE_TIMEOUT = 60  # 秒


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
        Header: RoomNameSize (1 byte) | TokenSize (1 byte)
        Body:   room_name bytes | token bytes | message bytes
        """

        if len(data) < 2:
            return None, None, None

        room_len = data[0]
        token_len = data[1]

        header_len = 2 + room_len + token_len
        if len(data) < header_len:
            return None, None, None

        room_bytes = data[2:2 + room_len]
        token_bytes = data[2 + room_len:2 + room_len + token_len]
        message_bytes = data[header_len:]

        room = room_bytes.decode("utf-8", errors="replace")
        token = token_bytes.decode("utf-8", errors="replace")
        # message はログ用に decode するが、クライアントには bytes をそのまま送る
        message = message_bytes.decode("utf-8", errors="replace")

        return room, token, message_bytes, message

    def cleanup_clients(self, now: float) -> None:
        stale = [addr for addr, last in self.clients.items()
                 if now - last > IDLE_TIMEOUT]
        for addr in stale:
            print(f"[INFO] Removing idle client {addr}")
            del self.clients[addr]

    def broadcast(self, message_bytes: bytes) -> None:
        for client_addr in list(self.clients.keys()):
            try:
                self.sock.sendto(formatted, client_addr)
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
                # クライアントの登録、更新
                self.clients[addr] = now

                room, token, message_bytes, message = self.decode_packet(data)
                if room is None:
                    print(f"[WARN] Received malformed packet from {addr}")
                    continue

                ts = time.strftime("%H:%M:%S", time.localtime(now))
                print(f"[{ts}] room={room} token={token} {addr}: {message}")

                # クライアントのクリーンアップ
                self.cleanup_clients(now)

                # ★ メッセージ部分だけを送る（ヘッダーなし、4094 バイト以内）
                self.broadcast(message_bytes)

        finally:
            self.sock.close()


def main():
    server = ChatServer(host="0.0.0.0", port=5000)
    server.serve_forever()


if __name__ == "__main__":
    main()

