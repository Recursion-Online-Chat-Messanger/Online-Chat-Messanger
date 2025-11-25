# server/protocol.py

import struct
import json

class TCRP:
    """
    TCRP (Threaded Chat Room Protocol) を扱うためのクラス。

    - 32バイトのヘッダー構造
      RoomNameSize (1B)
      Operation    (1B)
      State        (1B)
      PayloadSize (29B)

    - Body は RoomName + Payload
    """

    # ----- OPERATION -----
    OP_CREATE = 1      # 新規でルームを作成する
    OP_JOIN   = 2      # 既存のルームに参加する

    # ----- STATE -----
    STATE_REQUEST  = 0   # client から server (payload に "username"が含まれる)
    STATE_CONFORM  = 1   # server から client (リクエストを受け付けたかどうかをOK/NGで応答する)
    STATE_COMPLETE = 2   # server から client (server側で生成したtokenをclientに返す)


class TCRPProtocol:
    """
    Handles TCRP encode/decode logic.
    """

    HEADER_FORMAT = "!BBB29s"

    @classmethod
    def parse_header(cls, header_bytes):
        room_size, op, state, raw_payload_size = struct.unpack(
            cls.HEADER_FORMAT,
            header_bytes
        )
        payload_size = int(raw_payload_size.decode().strip() or 0)
        return room_size, op, state, payload_size

    @classmethod
    def parse_body(cls, room_size, body_bytes):
        # room_name を切り出す
        room_name = body_bytes[:room_size].decode("utf-8")
        
        # 残りはJSON文字列
        payload_raw = body_bytes[room_size:].decode("utf-8")

        payload = json.loads(payload_raw) if payload_raw else None
        return room_name, payload

    @classmethod
    def build_response(cls, room_name, operation, state, payload_dict):
        room_bytes = room_name.encode("utf-8")

        # JSONペイロードをバイナリ化
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        
        # PayloadSize を ASCII 数値 + 空白埋め で 29 バイトに固定
        payload_size_str = str(len(payload_bytes)).encode().ljust(29, b" ")

        header = struct.pack(
            cls.HEADER_FORMAT,
            len(room_bytes),
            operation,
            state,
            payload_size_str
        )

        return header + room_bytes + payload_bytes
