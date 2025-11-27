import threading
import os
import hashlib
from .user import User
from .room import Room


class RoomManager:
    def __init__(self):
        self.rooms = {}         # リクエストで受け取ったroom name
        self.lock = threading.Lock()

    def _generate_token(self):
        raw = os.urandom(16)
        return hashlib.sha256(raw).hexdigest()[:32]

    # ルーム作成
    def create_room(self, room_name, username):
        with self.lock:
            if room_name in self.rooms:
                return None  # 部屋が存在している

            token = self._generate_token()
            host = User(username, token)
            room = Room(room_name, host)
            self.rooms[room_name] = room
            return token

    # ルーム参加
    def join_room(self, room_name, username):
        with self.lock:
            if room_name not in self.rooms:
                return None

            room = self.rooms[room_name]
            token = self._generate_token()
            user = User(username, token)

            room.add_user(user)
            return token

    # UDP で token と IP をひもづける
    def register_address(self, room_name, token, ip, port):
        with self.lock:
            if room_name not in self.rooms:
                return False

            room = self.rooms[room_name]
            user = room.get_user(token)
            if not user:
                return False

            user.set_address(ip, port)
            return True

    # token + ip 一致確認
    def validate(self, room_name, token, ip, port):
        with self.lock:
            if room_name not in self.rooms:
                return False

            room = self.rooms[room_name]
            user = room.get_user(token)
            if not user:
                return False

            return user.address() == (ip, port)

    # 参加者退出
    def leave_room(self, room_name, token):
        with self.lock:
            if room_name not in self.rooms:
                return False

            room = self.rooms[room_name]

            # ホスト退出 → ルーム削除
            if token == room.host.token:
                del self.rooms[room_name]
                return "host_closed"

            # 参加者退出
            if token in room.users:
                del room.users[token]
                return True

            return False
