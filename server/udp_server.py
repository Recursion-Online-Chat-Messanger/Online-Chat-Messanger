# Server/udp_server.py
import socket
from .room_manager import RoomManager

print(">>> udp_server.py LOADED")


class UDPServer:

    def __init__(self, host="0.0.0.0", port=9001, manager=None):
        self.host = host
        self.port = port
        self.manager: RoomManager = manager
        self.room_clients = {}   # room_name → { token → (ip, port) }
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        print(f"[UDP SERVER] Listening on {(self.host, self.port)}")

        while True:
            data, addr = self.sock.recvfrom(4096)
            self.handle_packet(data, addr)

    def handle_packet(self, data, addr):
        if len(data) < 4:
            return

        op = data[0]
        room_size = data[1]
        token_size = data[2]
        user_size = data[3]

        offset = 4
        room = data[offset : offset + room_size].decode()
        offset += room_size

        token = data[offset : offset + token_size].decode()
        offset += token_size

        username = data[offset : offset + user_size].decode()
        offset += user_size

        message = data[offset:].decode()

        # token 認証
        if not self.manager.is_valid_token(room, token, addr):
            print("[UDP] Invalid token from", addr)
            return

        self.room_clients.setdefault(room, {})
        self.room_clients[room][token] = addr

        # ---- exit（leave） ----
        if op == 1:
            self.process_leave(room, token)
            return

        # ---- 通常メッセージ ----
        self.broadcast(room, addr, username, message)

    # ---- 各クライアントへ配信 ----
    def broadcast(self, room, sender_addr, username, message):
        if room not in self.room_clients:
            return

        full_msg = f"{username}: {message}".encode()

        for tkn, caddr in self.room_clients[room].items():
            if caddr != sender_addr:
                self.sock.sendto(full_msg, caddr)

    # ---- 退出処理 ----
    def process_leave(self, room, token):
        result = self.manager.leave_room(room, token)

        # ホスト退出 → 部屋削除
        if result == "host_closed":
            print("[UDP] Host left. Closing room:", room)

            if room in self.room_clients:
                for tkn, addr in self.room_clients[room].items():
                    self.sock.sendto(b"[SERVER] Room closed", addr)

            self.room_clients.pop(room, None)
            return

        # 参加者退出
        if result:
            print(f"[UDP] User left room {room}")
            self.room_clients.get(room, {}).pop(token, None)
