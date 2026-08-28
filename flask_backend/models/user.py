from bson import ObjectId
from flask_login import UserMixin
from datetime import datetime
from ..database import mongo


class User(UserMixin):
    def __init__(self, document):
        self.id = str(document.get("_id", document.get("id")))
        self.username = document.get("username", "")
        self.fullname = document.get("fullname", self.username)
        self.role = document.get("role", "Employee").title()

    @classmethod
    def from_id(cls, user_id, collection):
        try:
            document = collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            document = collection.find_one({"id": user_id})
        return cls(document) if document else None

    def has_role(self, *roles):
        return self.role in {role.title() for role in roles}