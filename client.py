#!/usr/bin/env python3
import socket
import threading
import sys
from typing import Tuple

MAX_PACKET_SIZE = 4096


class ChatClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 5000):
        self.server_addr: Tuple[str, int] = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # UDP でも connect するとデフォルト送信先が設定される
        self.sock.connect(self.server_addr)
        self.username: str = ""
        self.stop_event = threading.Event()

    @staticmethod
    def build_packet(username: str, message: str) -> bytes:
        """
        Packet:
        [0]       : 1 byte, username length
        [1:1+N]   : username bytes (UTF-8)
        [1+N: ]   : message bytes (UTF-8)
        """
        username_bytes = username.encode("utf-8")
        if len(username_bytes) > 255:
            raise ValueError("Username is too long (<= 255 bytes required).")

        message_bytes = message.encode("utf-8")
        packet = bytes([len(username_bytes)]) + username_bytes + message_bytes

        if len(packet) > MAX_PACKET_SIZE:
            raise ValueError("Message too long (packet > 4096 bytes).")

        return packet

    def recv_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                data = self.sock.recv(MAX_PACKET_SIZE)
            except OSError:
                break

            if not data:
                continue

            username_len = data[0]
            if len(data) < 1 + username_len:
                print("\n[CLIENT] Received malformed packet.")
                print("> ", end="", flush=True)
                continue

            username_bytes = data[1:1 + username_len]
            message_bytes = data[1 + username_len:]

            username = username_bytes.decode("utf-8", errors="replace")
            message = message_bytes.decode("utf-8", errors="replace")

            # 空メッセージ（参加通知など）は無視
            if not message.strip():
                print("> ", end="", flush=True)
                continue

            print(f"\nusername: {username} | message: {message}")
            print("> ", end="", flush=True)

    def input_username(self) -> None:
        while True:
            name = input("Choose a username: ").strip()
            if name:
                self.username = name
                return
            print("Username cannot be empty.")

    def send_join_packet(self) -> None:
        """空メッセージのパケットを送り、サーバーに自分を登録させる。"""
        try:
            packet = self.build_packet(self.username, "")
            self.sock.send(packet)
        except ValueError as e:
            print(f"[ERROR] Failed to send join packet: {e}")

    def run(self) -> None:
        self.input_username()
        self.send_join_packet()

        receiver = threading.Thread(target=self.recv_loop, daemon=True)
        receiver.start()

        print("Connected. Type messages and press Enter to send.")
        print("Type /quit or /exit to leave.")

        try:
            while True:
                try:
                    message = input("> ")
                except EOFError:
                    break

                if message.strip().lower() in ("/quit", "/exit"):
                    break

                if not message:
                    continue

                try:
                    packet = self.build_packet(self.username, message)
                except ValueError as e:
                    print(f"[ERROR] {e}")
                    continue

                try:
                    self.sock.send(packet)
                except OSError as e:
                    print(f"[ERROR] Failed to send: {e}")
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_event.set()
            self.sock.close()
            print("\nDisconnected.")


def main():
    # --- 1. まず host / port の元の値を決める ---
    if len(sys.argv) >= 3:
        host = sys.argv[1]
        port_str = sys.argv[2]
    else:
        host = input("Server host (default 127.0.0.1): ").strip() or "127.0.0.1"
        port_str = input("Server port (default 5000): ").strip() or "5000"

    # --- 2. ホストのバリデーション（この課題ではローカルのみ許可） ---
    while True:
        if host in ("127.0.0.1", "localhost"):
            break
        print("For this project, server host must be 127.0.0.1 or localhost.")
        host = input("Server host (default 127.0.0.1): ").strip() or "127.0.0.1"

    # --- 3. ポート番号のバリデーション（この課題では 5000 のみ） ---
    while True:
        if port_str.isdigit():
            port = int(port_str)
            if port == 5000:
                break
        print("For this project, server port must be 5000.")
        port_str = input("Server port (default 5000): ").strip() or "5000"

    client = ChatClient(host=host, port=port)
    client.run()


if __name__ == "__main__":
    main()

