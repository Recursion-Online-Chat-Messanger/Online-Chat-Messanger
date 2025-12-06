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

        while True:
            data, addr = self.sock.recvfrom(4096)
            self.handle_packet(data, addr)

    def handle_packet(self, data, addr):
        try:
            if len(data) < 4:
                print(f"[UDP SERVER] Packet too short from {addr}")
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

            message = data[offset:].decode() if offset < len(data) else ""

            print(f"[UDP SERVER] Received from {addr}: op={op}, room='{room}', user='{username}', msg='{message[:50]}'")

            # token 認証（addrを含む3引数）
            if not self.manager.is_valid_token(room, token, addr):
                print(f"[UDP SERVER] Invalid token from {addr}, room='{room}', token='{token}'")
                return

            # クライアントアドレスを登録
            self.room_clients.setdefault(room, {})
            self.room_clients[room][token] = addr
            print(f"[UDP SERVER] Valid token. Registered: room='{room}', addr={addr}, clients_in_room={len(self.room_clients[room])}")

            # ---- exit（leave） ----
            if op == 1:
                print(f"[UDP SERVER] Processing leave for '{username}' in '{room}'")
                self.process_leave(room, token, username)
                return

            # ---- 通常メッセージ ----
            if message:  # メッセージが空でない場合のみブロードキャスト
                print(f"[UDP SERVER] Broadcasting message in room '{room}' from '{username}'")
                self.broadcast(room, sender_addr=addr, username=username, message=message)
            else:
                print(f"[UDP SERVER] Join notification received from '{username}' in '{room}' (no broadcast)")

        except Exception as e:
            print(f"[UDP SERVER] Error handling packet from {addr}: {e}")
            import traceback
            traceback.print_exc()

    # ---- 各クライアントへ配信 ----
    def broadcast(self, room, sender_addr, username, message):
        if room not in self.room_clients:
            print(f"[UDP SERVER] Room '{room}' not found in room_clients")
            return

        full_msg = f"[{username}] {message}".encode()
        client_count = len(self.room_clients[room])
        
        print(f"[UDP SERVER] Broadcasting to {client_count} clients in room '{room}'")
        print(f"[UDP SERVER] Sender addr: {sender_addr}")

        sent_count = 0
        for tkn, caddr in self.room_clients[room].items():
            print(f"[UDP SERVER] Checking client: token={tkn[:8]}..., addr={caddr}")
            try:
                # 送信者にもメッセージを送信
                # 送信者以外に送信したい場合は if caddr != sender_addr: を使用
                self.sock.sendto(full_msg, caddr)
                sent_count += 1
                print(f"[UDP SERVER] Sent to {caddr}")
            except Exception as e:
                print(f"[UDP SERVER] Failed to send to {caddr}: {e}")
        
        print(f"[UDP SERVER] Successfully sent to {sent_count}/{client_count} clients")

    # ---- 退出処理 ----
    def process_leave(self, room, token, username):
        result = self.manager.leave_room(room, token)

        # ホスト退出 → 部屋削除
        if result == "host_closed":
            print(f"[UDP SERVER] Host '{username}' left. Closing room: '{room}'")

            if room in self.room_clients:
                close_msg = b"[UDP SERVER] Room closed by host"
                for tkn, addr in self.room_clients[room].items():
                    if tkn != token:  # ホスト自身には送らない
                        try:
                            self.sock.sendto(close_msg, addr)
                            print(f"[UDP SERVER] Sent room closure notification to {addr}")
                        except Exception as e:
                            print(f"[UDP SERVER] Failed to notify {addr}: {e}")

            self.room_clients.pop(room, None)
            print(f"[UDP SERVER] Room '{room}' removed from room_clients")
            return

        # 参加者退出
        if result:
            print(f"[UDP SERVER] User '{username}' left room '{room}'")
            
            # room_clients から削除
            if room in self.room_clients:
                self.room_clients[room].pop(token, None)
                print(f"[UDP SERVER] Removed '{username}' from room_clients. Remaining clients: {len(self.room_clients[room])}")
            
            # 退出通知を他のユーザーに送信
            if room in self.room_clients:
                leave_msg = f"[UDP SERVER] {username} left the room".encode()
                for tkn, addr in self.room_clients[room].items():
                    try:
                        self.sock.sendto(leave_msg, addr)
                        print(f"[UDP SERVER] Sent leave notification to {addr}")
                    except Exception as e:
                        print(f"[UDP SERVER] Failed to notify {addr}: {e}")