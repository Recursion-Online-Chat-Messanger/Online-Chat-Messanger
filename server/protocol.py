# server/protocol.py

import struct
import json

# ==============================
# TCRP (TCP 用) 32バイトヘッダ
# ==============================

# ヘッダ形式： 1B room_size, 1B op, 1B state, 29B payload_size
HEADER_FORMAT = "!BBB29s"   # ! はネットワークバイトオーダー(big endian)


# ヘッダ解析
def parse_tcrp_header(header_bytes):
    room_size, op, state, payload_raw = struct.unpack(HEADER_FORMAT, header_bytes)
    payload_size = int(payload_raw.decode().strip() or 0)
    return room_size, op, state, payload_size



# ボディ解析
def parse_tcrp_body(room_size, body_bytes):
    room_name = body_bytes[:room_size].decode("utf-8")
    payload_raw = body_bytes[room_size:].decode("utf-8")
    payload = json.loads(payload_raw) if payload_raw else None
    return room_name, payload



# TCP レスポンス生成（token を返す用）

def build_tcrp_response(room_name, token):
    room_bytes = room_name.encode("utf-8")

    payload = {"token": token}
    payload_bytes = json.dumps(payload).encode("utf-8")

    # ヘッダ作成
    payload_size_str = str(len(payload_bytes)).encode().ljust(29, b" ")
    header = struct.pack(
        HEADER_FORMAT,
        len(room_bytes),
        1,          # op = 1 (response)
        2,          # state = 2 (complete)
        payload_size_str
    )

    return header + room_bytes + payload_bytes


# ==============================
# UDP プロトコル
# ==============================


# UDP エンコード
def build_udp_packet(room_name, token, message):
    room_b = room_name.encode("utf-8")
    token_b = token.encode("utf-8")
    msg_b   = message.encode("utf-8")

    header = bytes([len(room_b), len(token_b)])
    return header + room_b + token_b + msg_b



# UDP デコード

def parse_udp_packet(data):
    room_len  = data[0]
    token_len = data[1]

    room_start = 2
    token_start = 2 + room_len
    msg_start = token_start + token_len

    room_name = data[room_start:token_start].decode()
    token     = data[token_start:msg_start].decode()
    message
