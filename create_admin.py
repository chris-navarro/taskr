from flask_bcrypt import Bcrypt
from config import Config
from flask_backend.database import SQLiteDatabase
from pymongo import MongoClient

bcrypt = Bcrypt()

if Config.DB_BACKEND == "sqlite":
    db = SQLiteDatabase(Config.SQLITE_PATH)
else:
    client = MongoClient(Config.MONGO_URI)
    db = client.get_database()

password = bcrypt.generate_password_hash(

    "devpasswd"

).decode("utf-8")

db.users.insert_one({

    "username": "devuser",

    "password": password,

    "fullname": "Administrator",

    "role": "Administrator"

})

print("Admin Created")