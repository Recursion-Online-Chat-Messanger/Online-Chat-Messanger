# server/tcp_server.py

import socket
import threading
import json

from protocol import TCRPProtocol, Operation, State
from room_manager import RoomManager


class TCPServer:
    """
    TCRP仕様に準拠したTCPサーバ。
    - operation=1: create room
    - operation=2: join room
    """

    def __init__(self, host="0.0.0.0", port=9000, manager=None):
        self.host = host
        self.port = port
        self.manager: RoomManager = manager
        self.sock = None


    # TCP はストリームなので分割受信に備え、必ず recv_n を使う
    def recv_n(self, conn, n):
        """ちょうど n バイト受信する。TCP の分割受信に対応するため必須。"""
        buf = b""
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("connection closed prematurely")
            buf += chunk
        return buf

    
    # サーバ起動
    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(20)

        print(f"[TCP SERVER] Listening on {(self.host, self.port)}")

        while True:
            conn, addr = self.sock.accept()
            print(f"[TCP SERVER] Connection from {addr}")

            threading.Thread(
                target=self.handle_client,
                args=(conn, addr),
                daemon=True
            ).start()


    # クライアント処理のメイン
    def handle_client(self, conn, addr):
        try:
            # ヘッダ受信（32B）
            header_bytes = self.recv_n(conn, 32)
            room_size, op, state, payload_size = TCRPProtocol.parse_header(header_bytes)

            # 必ず state=0 であること（クライアントの request）
            if state != State.REQUEST:
                self.send_ng(conn, "", op, "Invalid initial state")
                return

            # body受信：room_name + payload
            body_bytes = self.recv_n(conn, room_size + payload_size)
            room_name, payload = TCRPProtocol.parse_body(room_size, body_bytes)

            # username チェック
            if not payload or "username" not in payload:
                self.send_ng(conn, room_name, op, "username missing")
                return
            username = payload["username"]

            # conform（処理可能）を返す
            conform_packet = TCRPProtocol.build_response(
                room_name,
                op,
                State.CONFORM,
                {"status": 0}
            )
            conn.sendall(conform_packet)

            # create / join 実行
            try:
                if op == Operation.CREATE:
                    token = self.manager.create_room(room_name, username)
                elif op == Operation.JOIN:
                    token = self.manager.join_room(room_name, username)
                else:
                    self.send_ng(conn, room_name, op, "Invalid operation")
                    return

            except ValueError as e:
                # RoomManager 側のエラーは ValueError で返す
                self.send_ng(conn, room_name, op, str(e))
                return

            # 完了応答 (server側で生成したtokenを送付)
            complete_packet = TCRPProtocol.build_response(
                room_name,
                op,
                State.COMPLETE,
                {"token": token}
            )
            conn.sendall(complete_packet)

        except Exception as e:
            print("[TCP SERVER] Error:", e)

        finally:
            conn.close()
