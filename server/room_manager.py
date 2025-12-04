import threading
from .user import User
from .room import Room
import os
import hashlib

class RoomManager:
    def __init__(self):
        self.rooms = {}
        self.lock = threading.Lock()

    def _generate_token(self):
        raw = os.urandom(16)
        return hashlib.sha256(raw).hexdigest()[:32]

    # ルーム作成（ホスト）
    def create_room(self, room_name, username):
        with self.lock:
            if room_name in self.rooms:
                return None  # 既に存在

            token = self._generate_token()
            user = User(username, token)
            room = Room(room_name, user)   # host を含んだ Room を生成
            self.rooms[room_name] = room
            return token

    # ルーム参加（ゲスト）
    def join_room(self, room_name, username):
        with self.lock:
            room = self.rooms.get(room_name)
            if not room:
                return None

            token = self._generate_token()
            user = User(username, token)
            room.add_user(user)
            return token

    # UDP 用：接続元 IP/Port を登録
    def register_address(self, room_name, token, ip, port):
        with self.lock:
            room = self.rooms.get(room_name)
            if not room:
                return False

            user = room.get_user(token)
            if not user:
                return False

            user.set_address(ip, port)
            return True

    # UDP 用：token と IP/Port の一致確認
    def is_valid_token(self, room_name, token, addr):
        """
        UDP 認証：
        - room_name が存在すること
        - token を持つ user が存在すること
        - その user の address を初回登録 or 一致確認する
        """
        room = self.rooms.get(room_name)
        if not room:
            return False

        user = room.get_user(token)
        if not user:
            return False

        # 初回 → address 未登録なので登録
        if user.address() is None:
            user.set_address(addr[0], addr[1])
            return True

        # 2回目以降 → 一致確認
        return user.address() == addr

    # 参加者退出
    def leave_room(self, room_name, token):
        with self.lock:
            room = self.rooms.get(room_name)
            if not room:
                return False

            # ホスト退出 → ルーム削除
            if token == room.host_token:
                self.rooms.pop(room_name, None)
                return "host_closed"

            # 通常参加者退出
            if token in room.users:
                room.users.pop(token)
                return True

            return False

    # 明示的なルーム削除
    def close_room(self, room_name):
        with self.lock:
            if room_name in self.rooms:
                self.rooms.pop(room_name)
                return True
            return False
