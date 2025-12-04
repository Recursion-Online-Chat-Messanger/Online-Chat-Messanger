# Server/user.py
# ユーザー情報の管理

class User:
    def __init__(self, username, token):
        self.username = username        # 表示名
        self.token = token              # サーバが発行
        self.ip = None
        self.port = None

    def set_address(self, ip, port):
        self.ip = ip
        self.port = port
        
    def address(self):
        if self.ip is None:
            return None
        return (self.ip, self.port)
