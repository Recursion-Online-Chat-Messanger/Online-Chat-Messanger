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

        # 受信ソケット（送受信両方に使用）
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 任意のポートにバインド
        self.sock.bind(("", 0))
        local_addr = self.sock.getsockname()
        print(f"[UDP CLIENT] Listening on {local_addr}")
        print(f"[UDP CLIENT] Room='{room}', Token='{token[:8]}...', User='{username}'")
        # 接続確認メッセージを送信（サーバーに自分のアドレスを登録）
        self.send_join_notification()

    # ---- 送信（通常メッセージ） ----
    def send_join_notification(self):
        """接続確認メッセージを送信（サーバーに自分を登録）"""
        room_b = self.room.encode()
        token_b = self.token.encode()
        user_b = self.username.encode()
        msg_b = "".encode()  # 空メッセージ

        packet = (
            bytes([0, len(room_b), len(token_b), len(user_b)]) +
            room_b + token_b + user_b + msg_b
        )

        print(f"[UDP CLIENT] Sending join notification to {self.host}:{self.port}")
        
        try:
            self.sock.sendto(packet, (self.host, self.port))
            print(f"[UDP CLIENT] Join notification sent successfully")
        except Exception as e:
            print(f"[UDP CLIENT] Failed to send join notification: {e}")

    def send_message(self, text):
        room_b = self.room.encode()
        token_b = self.token.encode()
        user_b = self.username.encode()
        msg_b = text.encode()

        packet = (
            bytes([0, len(room_b), len(token_b), len(user_b)]) +
            room_b + token_b + user_b + msg_b
        )

        print(f"[UDP CLIENT] Sending message: '{text}' to {self.host}:{self.port}")
        print(f"[UDP CLIENT] Packet details: op=0, room_len={len(room_b)}, token_len={len(token_b)}, user_len={len(user_b)}, msg_len={len(msg_b)}")
        
        try:
            self.sock.sendto(packet, (self.host, self.port))
            print(f"[UDP CLIENT] Message sent successfully")
        except Exception as e:
            print(f"[UDP CLIENT] Failed to send message: {e}")

    # ---- 退出（op = 1） ----
    def send_leave(self):
        room_b = self.room.encode()
        token_b = self.token.encode()
        user_b = self.username.encode()

        packet = (
            bytes([1, len(room_b), len(token_b), len(user_b)]) +
            room_b + token_b + user_b
        )

        print(f"[UDP CLIENT] Sending leave request")
        try:
            self.sock.sendto(packet, (self.host, self.port))
            print(f"[UDP CLIENT] Leave request sent")
        except Exception as e:
            print(f"[UDP CLIENT] Failed to send leave: {e}")

    # ---- 非同期受信 ----
    def receive_loop(self):
        print("[UDP CLIENT] Starting receive loop...")
        self.running = True
        while self.running:
            try:
                msg, addr = self.sock.recvfrom(4096)
                decoded_msg = msg.decode()
                
                # ルーム終了通知をチェック
                if decoded_msg == "[UDP SERVER] Room closed by host":
                    print(f"\n{decoded_msg}")
                    print("[UDP SERVER] The host has left. Room is now closed.")
                    print("[UDP CLIENT] Press Enter to exit...")
                    self.running = False
                    break
                
                print(f"\n{decoded_msg}")
                print("> ", end="", flush=True)  # プロンプトを再表示
            except Exception as e:
                if self.running:
                    print(f"\n[UDP SERVER] ERROR: {e}")
                break
    
    def stop(self):
        """受信ループを停止"""
        self.running = False
        self.sock.close()


# 手動実行テスト (main.py 経由が通常)
if __name__ == "__main__":
    print("Use main.py client")