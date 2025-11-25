# server/room_manager.py

import threading
from user import User
from room import Room
import os
import hashlib

class RoomManager:
    def __init__(self):
        self.rooms = {}
        self.lock = threading.Lock()

    '''
    クライアントを識別するための「トークン（セッションID）」を生成する
    
    ・予測困難なランダム値をtokenとして使用する
    ・16バイトの乱数を生成後、SHA-256でハッシュ化し、32バイト以内に切り詰めて使用する
    '''
    def _generate_token(self):
        raw = os.urandom(16)
        return hashlib.sha256(raw).hexdigest()[:32]

    def create_room(self, room_name, username):
        with self.lock:
            if room_name in self.rooms:
                return None   # 既に存在

            token = self._generate_token()
            user = User(username, token)
            room = Room(room_name, user)
            self.rooms[room_name] = room
            return token

    def join_room(self, room_name, username):
        with self.lock:
            room = self.rooms.get(room_name)
            if not room:
                return None

            token = self._generate_token()
            user = User(username, token)
            room.add_user(user)
            return token

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

    def validate(self, room_name, token, ip, port):
        with self.lock:
            room = self.rooms.get(room_name)
            if not room:
                return False

            user = room.get_user(token)
            if not user:
                return False

            return user.address() == (ip, port)

    def is_valid_token(self, room_name, token, addr):
        """UDP通信で token と IP の一致を確認する"""
        if room_name not in self.rooms:
            return False
        
        if token not in self.rooms[room_name]["tokens"]:
            return False

        # まだIPが登録されていない場合 → このクライアントを正式に登録
        if self.rooms[room_name]["tokens"][token] is None:
            self.rooms[room_name]["tokens"][token] = addr
            return True

        # 既に登録されている → addr の一致を確認
        return self.rooms[room_name]["tokens"][token] == addr

