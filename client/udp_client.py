# client/udp_client.py

import socket
import threading
import time


class UDPClient:
    def __init__(self, host="127.0.0.1", port=9001):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False

    def start(self, room_name, token):
        """UDPクライアントを起動し、受信スレッドをスタート"""
        self.room_name = room_name
        self.token = token

        # UDP ソケットを作成
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 0))  # 動的ポート割り当て

        print(f"[UDP CLIENT] Listening on {self.sock.getsockname()}")

        # 受信ループを別スレッドで開始
        self.running = True
        threading.Thread(target=self.receive_loop, daemon=True).start()

        # 入力ループ開始
        self.input_loop()

    def build_packet(self, room_name, token, message):
        room_b = room_name.encode("utf-8")
        token_b = token.encode("utf-8")
        msg_b = message.encode("utf-8")

        return (
            bytes([len(room_b), len(token_b)]) +
            room_b + token_b + msg_b
        )

    def send_message(self, message):
        packet = self.build_packet(self.room_name, self.token, message)
        self.sock.sendto(packet, (self.host, self.port))

    def receive_loop(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(4096)
                print("[MSG]", data.decode("utf-8"))
            except:
                continue

    def input_loop(self):
        while True:
            msg = input("> ").strip()

            if msg == "exit":
                print("[UDP CLIENT] Exit requested.")
                self.running = False
                break

            self.send_message(msg)


if __name__ == "__main__":
    room = input("Room name: ").strip()
    token = input("Token: ").strip()

    client = UDPClient()
    client.start(room, token)
