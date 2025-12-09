from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, login, password, name):
        self.id = id
        self.login = login
        self.password = password
        self.name = name

    def get_id(self):
        return str(self.id)