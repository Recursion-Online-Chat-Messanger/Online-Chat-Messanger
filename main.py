# main.py
import argparse
import threading
import sys

# Server
from Server.tcp_server import TCPServer
from Server.udp_server import UDPServer
from Server.room_manager import RoomManager

# Client
from Client.tcp_client import TCPClient
from Client.udp_client import UDPClient


# サーバ起動
def run_server(args):
    print("[MAIN] Starting Server...")

    manager = RoomManager()

    tcp = TCPServer(host=args.host, port=args.tcp_port, manager=manager)
    udp = UDPServer(host=args.host, port=args.udp_port, manager=manager)

    # TCP server thread
    t1 = threading.Thread(target=tcp.start, daemon=True)
    t1.start()

    # UDP server thread
    t2 = threading.Thread(target=udp.start, daemon=True)
    t2.start()

    print(f"[MAIN] Server running: TCP={args.tcp_port}, UDP={args.udp_port}")
    print("[MAIN] CTRL+C to exit.")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[MAIN] Server stopped.")
        sys.exit(0)

# クライアント起動
def run_client(args):
    print("[MAIN] Starting Client...")

    room = input("Room name: ").strip()
    user = input("Username: ").strip()
    mode = input("create/join (1/2): ").strip()

    if mode not in ("1", "2"):
        print("Invalid mode")
        return

    op = 1 if mode == "1" else 2

    tcp = TCPClient(host=args.host, port=args.tcp_port)

    # TCP request → token を受け取る
    token = tcp.request(room, user, op)
    print("[CLIENT] TCP token =", token)
    print("[CLIENT] Starting UDP messaging...")

    udp = UDPClient(
        host=args.host,
        port=args.udp_port,
        room=room,
        token=token,
        username=user
    )

    # 非同期で受信
    threading.Thread(target=udp.receive_loop, daemon=True).start()

    # メッセージ送信ループ
    while True:
        msg = input("> ").strip()

        if msg.lower() == "exit":
            udp.send_leave()
            print("[CLIENT] Exiting room...")
            break

        udp.send_message(msg)


# CLI エントリーポイント
def main():
    parser = argparse.ArgumentParser(
        description="Online Chat Messenger (TCP+UDP) / Nunchi Team",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("mode", choices=["server", "client"],
                        help="server or client mode")

    parser.add_argument("--host", default="127.0.0.1",
                        help="Server host")

    parser.add_argument("--tcp-port", type=int, default=9000,
                        help="TCP server port")

    parser.add_argument("--udp-port", type=int, default=9001,
                        help="UDP server port")

    args = parser.parse_args()

    if args.mode == "server":
        run_server(args)
    else:
        run_client(args)


if __name__ == "__main__":
    main()
