import socket
from datetime import datetime
HOST = "127.0.0.1" 
PORT = 65432
clients = {}

def server():
  server_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  server_s.bind((HOST, PORT))
  while True:
    try:
      client_mes, received_client_address = server_s.recvfrom(4096)
      if received_client_address not in clients:
        print(f"新しいアドレスが接続された:{received_client_address}") 
      now = datetime.now()      
      clients[received_client_address] = now
          
          
      diff = datetime.now() - clients[received_client_address]
      print(diff)
      if (diff.seconds >= 60):
        clients.pop(received_client_address)
        print(clients)
  
      username_len = int.from_bytes(client_mes[:1], 'big')
      username = client_mes[1:1+username_len].decode('utf-8')
      mes = client_mes[1+username_len:].decode('utf-8')
      print(client_mes)
      print(received_client_address)
      print(username_len)
      print(username)
      print(mes)
      for client_address in clients:
          if client_address != received_client_address:
            server_s.sendto(mes.encode('utf-8'), client_address)  
    except KeyboardInterrupt as e:
      print(e)
      server_s.close()
      break
    except Exception as e:
      print(e)
      break

server()