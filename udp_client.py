#!/usr/bin/env python3
import socket
import threading
import sys

MAX_PACKET_SIZE = 4096


class ChatClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 5000):
        self.server_addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # UDP でも connect するとデフォルト送信先が設定される
        self.sock.connect(self.server_addr)
        self.username: str = ""
        self.room: str = ""
        self.token: str = ""
        self.stop_event = threading.Event()

    def input_room_and_token(self) -> None:
        self.room = input("Room name (default: lobby): ").strip() or "lobby"
        self.token = input("Token (optional, can be empty): ").strip()

    @staticmethod
    def build_packet(room: str, token: str, message: str) -> bytes:
        """
        Packet:
        Header:  [0] RoomNameSize (1 byte) | [1] TokenSize (1 byte)
        Body:    room_name bytes | token bytes | message bytes
        """
        room_bytes = room.encode("utf-8")
        if len(room_bytes) > 255:
            raise ValueError("Room name is too long (<= 255 bytes required).")

        token_bytes = token.encode("utf-8")
        if len(token_bytes) > 255:
            raise ValueError("Token is too long (<= 255 bytes required).")

        message_bytes = message.encode("utf-8")
        header = bytes([len(room_bytes), len(token_bytes)])
        packet = header + room_bytes + token_bytes + message_bytes

        if len(packet) > MAX_PACKET_SIZE:
            raise ValueError("Packet too long (packet > 4096 bytes).")

        return packet

    def recv_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                data = self.sock.recv(MAX_PACKET_SIZE)
            except OSError:
                break

            if not data:
                continue

            message = data.decode("utf-8", errors="replace")

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
            packet = self.build_packet(self.room, self.token, "")
            self.sock.send(packet)
        except ValueError as e:
            print(f"[ERROR] Failed to send join packet: {e}")

    def run(self) -> None:
        self.input_username()
        self.input_room_and_token()   # 変更

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

                # 実際に送るメッセージは「username> message」の形にする
                text = f"{self.username}> {message}"

                try:
                    packet = self.build_packet(self.room, self.token, text)
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

