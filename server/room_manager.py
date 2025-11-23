# server/room_manager.py

import os
import hashlib
import threading


class RoomManager:
    def __init__(self):
        # 全ルームの状態を保持
        self.rooms = {}
        # 複数のスレッドが同じリソースにアクセスしないようにロックする
        self.lock = threading.Lock()


    # トークン生成（最大255バイトを制限）

    def generate_token(self):
        raw = os.urandom(16)
        token = hashlib.sha256(raw).hexdigest()[:32]  # 32字 = 32バイト以内
        return token


    # ルーム作成

    def create_room(self, room_name, username):
        with self.lock:
            if room_name in self.rooms:
                raise ValueError("Room already exists")

            token = self.generate_token()

            self.rooms[room_name] = {
                "host_token": token,
                "tokens": {
                    token: None  # IP未登録
                }
            }
            return token


    # ルーム参加

    def join_room(self, room_name, username):
        with self.lock:
            if room_name not in self.rooms:
                raise ValueError("Room not found")

            token = self.generate_token()
            self.rooms[room_name]["tokens"][token] = None
            return token


