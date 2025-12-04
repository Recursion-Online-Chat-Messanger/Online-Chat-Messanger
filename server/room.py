# server/room.py

class Room:
    def __init__(self, name, host_user):
        self.name = name
        self.host_token = host_user.token
        self.users = {host_user.token: host_user}

    def add_user(self, user):
        self.users[user.token] = user

    def remove_user(self, token):
        if token in self.users:
            del self.users[token]

    def is_member(self, token):
        return token in self.users

    def get_user(self, token):
        return self.users.get(token)

    def get_all_users(self):
        return list(self.users.values())
