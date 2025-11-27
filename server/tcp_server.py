# server/tcp_server.py

import socket
import threading
from .protocol import TCRPProtocol, Operation, State
from .room_manager import RoomManager

print(">>> tcp_server.py LOADED")


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

    # N バイトちょうど受信（TCP の分割受信対策）
    def recv_n(self, conn, n):
        buf = b""
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("connection closed prematurely")
            buf += chunk
        return buf

    
    # サーバ起動
    
    def start(self):
        print(">>> TCPServer.start() CALLED")

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

    # クライアント処理
    def handle_client(self, conn, addr):
        try:
            # ヘッダー受信（32 byte）
            header_bytes = self.recv_n(conn, 32)
            print(">>> SERVER RECEIVED HEADER:", header_bytes, "LEN:", len(header_bytes))
            room_size, op, state, payload_size = TCRPProtocol.parse_header(header_bytes)

            # client → server の REQUEST
            if state != State.REQUEST:
                self.send_ng(conn, "", op, "Invalid state")
                return

            # body 受信
            body_bytes = self.recv_n(conn, room_size + payload_size)
            room_name, payload = TCRPProtocol.parse_body(room_size, body_bytes)

            if not payload or "username" not in payload:
                self.send_ng(conn, room_name, op, "username missing")
                return

            username = payload["username"]

            # リクエストの受付結果を返す
            conform_packet = TCRPProtocol.build_response(
                room_name, op, State.CONFORM, {"status": 0}
            )
            conn.sendall(conform_packet)

            # create / join
            if op == Operation.CREATE:
                token = self.manager.create_room(room_name, username)
            elif op == Operation.JOIN:
                token = self.manager.join_room(room_name, username)
            else:
                self.send_ng(conn, room_name, op, "Invalid op")
                return

            if token is None:
                self.send_ng(conn, room_name, op, "Room error")
                return

            # 完了応答
            complete_packet = TCRPProtocol.build_response(
                room_name,
                op,
                State.COMPLETE, {"token": token}
            )
            print(f"[TCP SERVER] COMPLETE: room={room_name}, user={username}, token={token}")
            conn.sendall(complete_packet)

        except Exception as e:
            print("[TCP SERVER] Error:", e)

        finally:
            conn.close()

    # NG 応答
    def send_ng(self, conn, room_name, op, msg):
        packet = TCRPProtocol.build_response(
            room_name,
            op,
            State.CONFORM,   # エラー時も CONFORM 相当で返す
            {"status": 1, "error": msg}
        )
        conn.sendall(packet)


# 実行
if __name__ == "__main__":
    server = TCPServer(manager=RoomManager())
    server.start()