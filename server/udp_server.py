# server/udp_server.py
# 動作確認用

import socket
from .room_manager import RoomManager

print(">>> udp_server.py LOADED")

class UDPServer:
    """
    Stage2 完全版 UDP サーバ。
    - op = 0: 通常メッセージ
    - op = 1: exit/leave
    """

    def __init__(self, host="0.0.0.0", port=9001, manager=None):
        self.host = host
        self.port = port
        self.manager: RoomManager = manager
        self.sock = None

        # room_name -> { token -> (ip, port) }
        self.room_clients = {}

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        print(f"[UDP SERVER] Listening on {(self.host, self.port)}")

        while True:
            data, addr = self.sock.recvfrom(4096)
            self.handle_packet(data, addr)

    def handle_packet(self, data, addr):
        if len(data) < 3:
            return

        op = data[0]
        room_size = data[1]
        token_size = data[2]

        if len(data) < 3 + room_size + token_size:
            return

        room_name = data[3 : 3 + room_size].decode("utf-8")
        token = data[3 + room_size : 3 + room_size + token_size].decode("utf-8")
        message = data[3 + room_size + token_size :].decode("utf-8")

        # token 認証
        if not self.manager.is_valid_token(room_name, token, addr):
            print(f"[UDP] Invalid token from {addr}")
            return

        self.room_clients.setdefault(room_name, {})
        self.room_clients[room_name][token] = addr

        # op = 1 → exit/leave
        if op == 1:
            self.process_leave(room_name, token)
            return

        # 通常メッセージ broadcast
        self.broadcast(room_name, addr, message)

    def broadcast(self, room_name, sender_addr, message):
        """room 内の全クライアントへメッセージ送信"""
        if room_name not in self.room_clients:
            return

        for tkn, caddr in self.room_clients[room_name].items():
            if caddr != sender_addr:
                self.sock.sendto(message.encode("utf-8"), caddr)

    def process_leave(self, room_name, token):
        """ユーザー退出処理"""
        result = self.manager.leave_room(room_name, token)

        # ホスト退出 → 部屋削除 → 全員通知
        if result == "host_closed":
            print(f"[UDP] Host left. Closing room: {room_name}")

            if room_name in self.room_clients:
                for tkn, addr in self.room_clients[room_name].items():
                    self.sock.sendto(b"[SERVER] Room closed", addr)

            self.room_clients.pop(room_name, None)
            return

        # 参加者退出
        if result is True:
            print(f"[UDP] User left room {room_name}")
            self.room_clients[room_name].pop(token, None)
