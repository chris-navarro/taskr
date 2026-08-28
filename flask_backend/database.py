import json
import sqlite3
import uuid
from datetime import datetime

from pymongo import MongoClient


class SQLiteResult:
    def __init__(self, inserted_id=None, matched_count=0, modified_count=0, deleted_count=0, upserted_id=None):
        self.inserted_id = inserted_id
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.deleted_count = deleted_count
        self.upserted_id = upserted_id


def _encode(value):
    if isinstance(value, datetime):
        return {"__taskr_type__": "datetime", "value": value.isoformat()}
    if value.__class__.__name__ == "ObjectId":
        return {"__taskr_type__": "objectid", "value": str(value)}
    if isinstance(value, dict):
        return {key: _encode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_encode(item) for item in value]
    return value


def _decode(value):
    if isinstance(value, dict) and value.get("__taskr_type__") == "datetime":
        return datetime.fromisoformat(value["value"])
    if isinstance(value, dict) and value.get("__taskr_type__") == "objectid":
        return value["value"]
    if isinstance(value, dict):
        return {key: _decode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decode(item) for item in value]
    return value


def _matches(document, query):
    for key, expected in query.items():
        actual = document.get(key)
        if actual is not None and actual.__class__.__name__ == "ObjectId":
            actual = str(actual)
        if expected is not None and expected.__class__.__name__ == "ObjectId":
            expected = str(expected)
        if isinstance(expected, dict):
            for operator, value in expected.items():
                if operator == "$options":
                    continue
                if operator == "$ne" and actual == value:
                    return False
                if operator == "$lt" and not (actual is not None and actual < value):
                    return False
                if operator == "$lte" and not (actual is not None and actual <= value):
                    return False
                if operator == "$gt" and not (actual is not None and actual > value):
                    return False
                if operator == "$gte" and not (actual is not None and actual >= value):
                    return False
                if operator == "$in" and actual not in value:
                    return False
                if operator == "$nin" and actual in value:
                    return False
                if operator == "$regex":
                    import re
                    flags = re.IGNORECASE if expected.get("$options") == "i" else 0
                    if actual is None or re.search(value, str(actual), flags) is None:
                        return False
        elif actual != expected:
            return False
    return True


class SQLiteCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, field, direction):
        self.documents.sort(key=lambda item: (item.get(field) is None, item.get(field)), reverse=direction < 0)
        return self

    def skip(self, amount):
        self.documents = self.documents[amount:]
        return self

    def limit(self, amount):
        self.documents = self.documents[:amount]
        return self

    def __iter__(self):
        return iter(self.documents)


class SQLiteCollection:
    def __init__(self, database, name):
        self.database = database
        self.name = name
        self.database.execute("CREATE TABLE IF NOT EXISTS documents (collection TEXT NOT NULL, id TEXT NOT NULL, body TEXT NOT NULL, PRIMARY KEY (collection, id))")
        self.database.commit()

    def _documents(self):
        rows = self.database.execute("SELECT id, body FROM documents WHERE collection = ?", (self.name,)).fetchall()
        documents = []
        for document_id, body in rows:
            document = _decode(json.loads(body))
            document["_id"] = document_id
            documents.append(document)
        return documents

    def _save(self, document):
        document = dict(document)
        document_id = str(document.get("_id") or uuid.uuid4().hex[:24])
        document["_id"] = document_id
        body = json.dumps(_encode({key: value for key, value in document.items() if key != "_id"}))
        self.database.execute("INSERT OR REPLACE INTO documents (collection, id, body) VALUES (?, ?, ?)", (self.name, document_id, body))
        self.database.commit()
        return document_id

    def find(self, query=None, projection=None):
        return SQLiteCursor([document for document in self._documents() if _matches(document, query or {})])

    def find_one(self, query=None, sort=None):
        cursor = self.find(query)
        if sort:
            for field, direction in reversed(sort):
                cursor.sort(field, direction)
        return next(iter(cursor), None)

    def insert_one(self, document):
        return SQLiteResult(inserted_id=self._save(document))

    def update_one(self, query, changes, upsert=False):
        document = self.find_one(query)
        upserted_id = None
        if document is None:
            if not upsert:
                return SQLiteResult()
            document = {key: value for key, value in query.items() if not isinstance(value, dict)}
            upserted_id = self._save(document)
            document["_id"] = upserted_id
        before = json.dumps(_encode(document), sort_keys=True)
        for operator, values in changes.items():
            if operator == "$set":
                document.update(values)
            elif operator == "$inc":
                for key, value in values.items():
                    document[key] = (document.get(key) or 0) + value
            elif operator == "$addToSet":
                for key, value in values.items():
                    items = document.setdefault(key, [])
                    if value not in items:
                        items.append(value)
            elif operator == "$pull":
                for key, value in values.items():
                    document[key] = [item for item in document.get(key, []) if item != value]
        self._save(document)
        changed = before != json.dumps(_encode(document), sort_keys=True)
        return SQLiteResult(matched_count=1, modified_count=int(changed), upserted_id=upserted_id)

    def delete_one(self, query):
        document = self.find_one(query)
        if not document:
            return SQLiteResult()
        self.database.execute("DELETE FROM documents WHERE collection = ? AND id = ?", (self.name, document["_id"]))
        self.database.commit()
        return SQLiteResult(deleted_count=1)

    def count_documents(self, query):
        return sum(1 for _ in self.find(query))

    def aggregate(self, pipeline):
        documents = self._documents()
        for stage in pipeline:
            if "$match" in stage:
                documents = [document for document in documents if _matches(document, stage["$match"])]
            elif "$group" in stage:
                spec = stage["$group"]
                result = {"_id": spec.get("_id")}
                for key, expression in spec.items():
                    if key != "_id" and "$sum" in expression:
                        source = expression["$sum"]
                        result[key] = sum((document.get(source[1:], 0) or 0) for document in documents if isinstance(source, str) and source.startswith("$"))
                documents = [result]
        return SQLiteCursor(documents)


class SQLiteDatabase:
    def __init__(self, path):
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.collections = {}

    def execute(self, *args):
        return self.connection.execute(*args)

    def commit(self):
        self.connection.commit()

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = SQLiteCollection(self, name)
        return self.collections[name]


class Database:
    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app):
        if app.config.get("DB_BACKEND", "mongo").lower() == "sqlite":
            self.db = SQLiteDatabase(app.config["SQLITE_PATH"])
            return
        self.client = MongoClient(app.config["MONGO_URI"])
        self.db = self.client.get_database()


mongo = Database()
