import socket
import threading

HOST = "127.0.0.1" 
PORT = 65432
lock = threading.Lock()

class Client:
  client_s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  client_s1.bind(("127.0.0.1", 0))
  def input_text(self,min, max, str_mes):
    try:
      text = input(f"{str_mes}を入力してください:")
      while len(text.encode('utf-8')) > max or len(text.encode('utf-8')) < min:
        print(f"{str_mes}は{min}文字以上{max}文字以内で入力してください")
        print(len(text.encode('utf-8')))
        text = input(f"{str_mes}を入力してください:")
      return text
    except KeyboardInterrupt as e:
        print(e)

  def create_mes(self, username):
    mes = self.input_text(1, 4096, "メッセージ")
    username_len = len(username.encode('utf-8'))
    self.client_s1.sendto(username_len.to_bytes(1, "big") + username.encode('utf-8') + mes.encode('utf-8'), (HOST, PORT))
  
  def receive_mes(self):
    try:
      while True:
          server_mes = self.client_s1.recvfrom(4096)
          if server_mes != None:
            server_mes = server_mes[0].decode('utf-8')
            print(f'サーバーのメッセージ: {server_mes}')
    except KeyboardInterrupt as e:
        print(e)
        self.client_s1.close()

  def client(self):
    username = self.input_text(1, 255, "ユーザー名")
    thread2 = threading.Thread(target=self.receive_mes)
    thread2.start()
    while True:
      self.create_mes(username)
      

client = Client()
client.client()