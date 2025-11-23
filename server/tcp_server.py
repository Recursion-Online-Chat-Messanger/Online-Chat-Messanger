class TCPServer:
    def __init__(self, room_manager):
        self.room_manager = room_manager
        self.sock = None

    def start(self):
        self.sock = socket.socket(...)
        self.sock.bind(...)
        self.sock.listen(...)

        while True:
            conn, addr = self.sock.accept()
            threading.Thread(
                target=self.handle_client,
                args=(conn, addr),
                daemon=True
            ).start()

    def handle_client(self, conn, addr):
        header = conn.recv(32)
        room_size, op, state, payload_size = parse_tcrp_header(header)
        payload = conn.recv(payload_size)

        room_name, username = parse_tcrp_body(room_size, payload)

        if op == 1:
            token = self.room_manager.create_room(room_name, username)
        elif op == 2:
            token = self.room_manager.join_room(room_name, username)

        response = build_tcrp_response(room_name, token)
        conn.sendall(response)
        conn.close()
