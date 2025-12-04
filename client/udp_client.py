# Client/udp_client.py
import socket
import threading


class UDPClient:
    def __init__(self, host="127.0.0.1", port=9001, room="", token="", username=""):
        self.host = host
        self.port = port
        self.room = room
        self.token = token
        self.username = username

        # 受信ソケット
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", 0))
        print("[UDP CLIENT] Listening on", self.sock.getsockname())

    # ---- 送信（通常メッセージ） ----
    def send_message(self, text):
        room_b = self.room.encode()
        token_b = self.token.encode()
        user_b = self.username.encode()
        msg_b = text.encode()

        packet = (
            bytes([0, len(room_b), len(token_b), len(user_b)]) +
            room_b + token_b + user_b + msg_b
        )

        self.sock.sendto(packet, (self.host, self.port))

    # ---- 退出（op = 1） ----
    def send_leave(self):
        room_b = self.room.encode()
        token_b = self.token.encode()
        user_b = self.username.encode()

        packet = (
            bytes([1, len(room_b), len(token_b), len(user_b)]) +
            room_b + token_b + user_b
        )

        self.sock.sendto(packet, (self.host, self.port))

    # ---- 非同期受信 ----
    def receive_loop(self):
        while True:
            msg, _ = self.sock.recvfrom(4096)
            print(msg.decode())


# 手動実行テスト (main.py 経由が通常)
if __name__ == "__main__":
    print("Use main.py client")
