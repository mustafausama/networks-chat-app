from pymongo import MongoClient

# Singleton class DB (to prevent the creation of multiple instances of the DB)
class DB:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DB, cls).__new__(cls)
            cls._instance.client = MongoClient('mongodb://localhost:27017/')
            cls._instance.db = cls._instance.client['p2p-chat']
        return cls._instance

    def is_account_exist(self, username):
        user_data = self.db.accounts.find_one({'username': username})
        if user_data is None:
            return None
        else:
            return {
                "username": user_data["username"],
                "hashed_password": user_data["hashed_password"],
                "salt": user_data["salt"],
            }

    def register(self, username, hashed_password, salt="123456"):
        account = {
            "username": username,
            "hashed_password": hashed_password,
            "salt": salt
        }
        inserted = self.db.accounts.insert_one(account)
        return inserted

    def set_user_online(self, username, ip, port):
        online_peer = {
            "username": username,
            "ip": ip,
            "port": port
        }
        self.db.online_peers.insert_one(online_peer)

    def set_user_offline(self, username):
        self.db.online_peers.delete_one({"username": username})

    def get_peer_ip_port(self, username):
        res = self.db.online_peers.find_one({"username": username})
        return (res["ip"], res["port"])
