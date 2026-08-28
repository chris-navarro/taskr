from pymongo import MongoClient
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

client = MongoClient("mongodb://localhost:27017")

db = client.taskr

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