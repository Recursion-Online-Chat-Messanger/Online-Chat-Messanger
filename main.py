# main.py
import argparse
import threading
import sys

# Server
from server.tcp_server import TCPServer
from server.udp_server import UDPServer
from server.room_manager import RoomManager

# Client
from client.tcp_client import TCPClient
from client.udp_client import UDPClient


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
    print(f"[TCP SERVER] Listening on {args.host}:{args.tcp_port}")
    print(f"[UDP SERVER] Listening on {args.host}:{args.udp_port}")

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
    mode = input("Choose number -- 1(create) or 2(join): ").strip()

    if mode not in ("1", "2"):
        print("Invalid mode")
        return

    op = 1 if mode == "1" else 2
    is_host = (op == 1)

    tcp = TCPClient(host=args.host, port=args.tcp_port)

    # TCP request → token を受け取る
    try:
        token = tcp.request(room, user, op)
        print("[TCP SERVER] TCP token =", token)
        
        if is_host:
            print("[TCP SERVER] You are the HOST of this room")
            print("[TCP SERVER] If you exit, the room will be closed for all participants")
        else:
            print("[TCP SERVER] You joined as a GUEST")
        
        print("[UDP SERVER] Starting UDP messaging...")
    except Exception as e:
        print(f"[TCP SERVER ERROR] {e}")
        return

    udp = UDPClient(
        host=args.host,
        port=args.udp_port,
        room=room,
        token=token,
        username=user
    )

    # 非同期で受信
    recv_thread = threading.Thread(target=udp.receive_loop, daemon=True)
    recv_thread.start()

    print("\nCommands:")
    print("  - Type a message and press Enter to send")
    print("  - Type 'exit' to leave the room")
    if is_host:
        print("  - (HOST) Exiting will close the room for everyone")
    print()

    # メッセージ送信ループ
    try:
        while udp.running:
            try:
                msg = input("> ").strip()

                if not udp.running:
                    break

                if msg.lower() == "exit":
                    if is_host:
                        confirm = input("You are the HOST. Closing room will disconnect all users. Continue? (yes/no): ").strip().lower()
                        if confirm != "yes":
                            print("Exit cancelled.")
                            continue
                    
                    udp.send_leave()
                    print("[UDP SERVER] Leaving room...")
                    break

                if msg:  # 空メッセージは送信しない
                    udp.send_message(msg)
            except EOFError:
                # Ctrl+D などで入力が終了した場合
                break
    except KeyboardInterrupt:
        print("\n[UDP SERVER] Interrupted by user")
    
    udp.stop()
    print("[UDP SERVER] Disconnected.")


# CLI エントリーポイント
def main():
    parser = argparse.ArgumentParser(
        description="Online Chat Messenger",
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
