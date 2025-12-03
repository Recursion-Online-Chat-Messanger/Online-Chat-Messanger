# Client/tcp_client.py

import socket

from common.protocol import TCRPProtocol, Operation, State


class TCPClient:
    """
    TCRP仕様に基づき、TCPを使ってルームの作成(create)または参加(join)を行い、
    サーバから発行される token を取得するクライアント。
    token は Stage2 の UDP 通信で必要となる認証情報。
    """

    def __init__(self, host="127.0.0.1", port=9000):
        self.host = host
        self.port = port

    def recv_n(self, conn, n):
        """
        TCPはストリームのため、一度のrecvで必要なバイト数が揃うとは限らないので
        ちょうどnバイトを受信できるまでブロックし続ける。
        """
        buf = b""
        while len(buf) < n:
            chunk = conn.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("connection closed during recv")
            buf += chunk
        return buf

    def request(self, room_name, username, op):

        """
        サーバに create/join 操作を依頼し、token を取得する。
        op は Operation.CREATE または Operation.JOIN。
        
        成功時: token（文字列）を返す
        失敗時: RuntimeError を投げる
        """
        payload = {"username": username}
        request_bytes = TCRPProtocol.build_request(room_name, op, payload)

        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.host, self.port))

        # リクエスト送信
        print(">>> SEND:", request_bytes)
        print(">>> SEND LEN:", len(request_bytes))
        conn.sendall(request_bytes)
        

        # ---------- conform 受信（state=1） ----------
        header_bytes = self.recv_n(conn, 32)
        room_size, op_recv, state, payload_size = TCRPProtocol.parse_header(header_bytes)
        if state != TCRPProtocol.STATE_CONFORM:
            raise RuntimeError("Expected conform(state=1) but got different state")

        body_bytes = self.recv_n(conn, room_size + payload_size)
        _, payload = TCRPProtocol.parse_body(room_size, body_bytes)

        if payload.get("status") != 0:
            raise RuntimeError("Server rejected operation in conform phase")

        # ---------- complete 受信（state=2） ----------
        header_bytes = self.recv_n(conn, 32)
        room_size, op_recv, state, payload_size = TCRPProtocol.parse_header(header_bytes)

        body_bytes = self.recv_n(conn, room_size + payload_size)
        _, payload = TCRPProtocol.parse_body(room_size, body_bytes)

        if state != TCRPProtocol.STATE_COMPLETE:
            error_msg = payload.get("error") if payload else None
            raise RuntimeError(
                f"Expected complete(state=2) but got state={state}"
                + (f": {error_msg}" if error_msg else "")
            )

        if payload.get("status", 0) != 0:
            raise RuntimeError(f"Server returned error: {payload.get('error')}")
        
        # デバッグ用
        # print("DEBUG op:", op)
        
        token = payload.get("token")
        if not token:
            raise RuntimeError("Token missing in complete response")
        conn.close()
        return token


if __name__ == "__main__":
    client = TCPClient()

    room = input("Room name: ").strip()
    user = input("Username: ").strip()
    mode = input("create/join: ").strip()

    if mode == "1":
        op = TCRPProtocol.OP_CREATE
    elif mode == "2":
        op = TCRPProtocol.OP_JOIN
    else:
        raise RuntimeError("Invalid input")


    try:
        token = client.request(room, user, op)
        print(f"[CLIENT] Token received: {token}")
    except Exception as e:
        print("[CLIENT ERROR]", e)