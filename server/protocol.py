import struct
import json


class Operation:
    CREATE = 1
    JOIN = 2


class State:
    REQUEST = 0
    CONFORM = 1
    COMPLETE = 2


class TCRPProtocol:
    HEADER_FORMAT = "!BBB29s"

    @classmethod
    def parse_header(cls, header_bytes):
        room_size, op, state, raw_payload_size = struct.unpack(
            cls.HEADER_FORMAT, header_bytes
        )
        payload_size = int(raw_payload_size.decode().strip() or 0)
        return room_size, op, state, payload_size

    @classmethod
    def parse_body(cls, room_size, body_bytes):
        room_name = body_bytes[:room_size].decode("utf-8")
        payload_raw = body_bytes[room_size:].decode("utf-8")
        payload = json.loads(payload_raw) if payload_raw else None
        return room_name, payload

    @classmethod
    def build_request(cls, room_name, op, payload_dict):
        room_b = room_name.encode("utf-8")
        payload_b = json.dumps(payload_dict).encode("utf-8")
        payload_size_b = str(len(payload_b)).encode().ljust(29, b" ")

        header = struct.pack(
            cls.HEADER_FORMAT,
            len(room_b),
            op,
            State.REQUEST,
            payload_size_b
        )
        return header + room_b + payload_b

    @classmethod
    def build_response(cls, room_name, op, state, payload_dict):
        room_b = room_name.encode("utf-8")
        payload_b = json.dumps(payload_dict).encode("utf-8")
        payload_size_b = str(len(payload_b)).encode().ljust(29, b" ")

        header = struct.pack(
            cls.HEADER_FORMAT,
            len(room_b),
            op,
            state,
            payload_size_b
        )
        return header + room_b + payload_b
