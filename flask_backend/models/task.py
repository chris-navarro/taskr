"""
Task Repository

All database operations for the Task collection
are centralized in this file.
"""

from datetime import datetime

from bson import ObjectId

from flask_backend.database import mongo


class Task:

    COLLECTION = "tasks"

    @classmethod
    def collection(cls):
        """
        Returns the Mongo collection.
        """
        return mongo.db[cls.COLLECTION]

    ####################################################################
    # CREATE
    ####################################################################

    @classmethod
    def create(cls, document):

        document.setdefault("created_at", datetime.utcnow())
        document.setdefault("updated_at", datetime.utcnow())
        document.setdefault("deleted", False)

        return cls.collection().insert_one(document)

    ####################################################################
    # GET ONE
    ####################################################################

    @classmethod
    def get(cls, task_id):

        try:

            return cls.collection().find_one(

                {
                    "_id": ObjectId(task_id),
                    "deleted": False
                }

            )

        except Exception:

            return None

    ####################################################################
    # GET ALL
    ####################################################################

    @classmethod
    def all(cls, owner_id=None):

        query = {

            "deleted": False

        }

        if owner_id:

            query["owner_id"] = ObjectId(owner_id)

        return list(

            cls.collection()

            .find(query)

            .sort("created_at", -1)

        )

    ####################################################################
    # UPDATE
    ####################################################################

    @classmethod
    def update(cls, task_id, values):

        values["updated_at"] = datetime.utcnow()

        return cls.collection().update_one(

            {

                "_id": ObjectId(task_id),

                "deleted": False

            },

            {

                "$set": values

            }

        )

    ####################################################################
    # SOFT DELETE
    ####################################################################

    @classmethod
    def delete(cls, task_id):

        return cls.collection().update_one(

            {

                "_id": ObjectId(task_id)

            },

            {

                "$set": {

                    "deleted": True,

                    "updated_at": datetime.utcnow()

                }

            }

        )

    ####################################################################
    # SEARCH
    ####################################################################

    @classmethod
    def search(cls, keyword="", owner_id=None):

        query = {

            "deleted": False

        }

        if owner_id:

            query["owner_id"] = ObjectId(owner_id)

        if keyword:

            query["subject"] = {

                "$regex": keyword,

                "$options": "i"

            }

        return list(

            cls.collection()

            .find(query)

            .sort("created_at", -1)

        )

    ####################################################################
    # PAGINATION
    ####################################################################

    @classmethod
    def paginate(

        cls,

        keyword="",

        page=1,

        per_page=10,

        owner_id=None

    ):

        query = {

            "deleted": False

        }

        if owner_id:

            query["owner_id"] = ObjectId(owner_id)

        if keyword:

            query["subject"] = {

                "$regex": keyword,

                "$options": "i"

            }

        skip = (page - 1) * per_page

        cursor = (

            cls.collection()

            .find(query)

            .sort("created_at", -1)

            .skip(skip)

            .limit(per_page)

        )

        total = cls.collection().count_documents(query)

        return list(cursor), total

    ####################################################################
    # UPDATE PROGRESS
    ####################################################################

    @classmethod
    def update_progress(

        cls,

        task_id,

        progress,

        status=None,

        hours_worked=0

    ):

        status = status or "In Progress"

        completed_date = None

        if progress >= 100:

            progress = 100

            status = "Completed"

            completed_date = datetime.utcnow()

        values = {
            "progress": progress,
            "status": status,
            "completed_date": completed_date,
            "updated_at": datetime.utcnow()
        }
        update = {"$set": values}
        if hours_worked:
            update["$inc"] = {"actual_hours": hours_worked}

        return cls.collection().update_one(

            {

                "_id": ObjectId(task_id)

            },

            update

        )

    ####################################################################
    # DASHBOARD COUNTS
    ####################################################################

    @classmethod
    def dashboard_counts(cls, owner_id):

        query = {

            "deleted": False,

            "owner_id": ObjectId(owner_id)

        }

        total = cls.collection().count_documents(query)

        completed = cls.collection().count_documents(

            {

                **query,

                "status": "Completed"

            }

        )

        planning = cls.collection().count_documents(

            {

                **query,

                "status": "Planning"

            }

        )

        in_progress = cls.collection().count_documents(

            {

                **query,

                "status": "In Progress"

            }

        )

        overdue = cls.collection().count_documents(

            {

                **query,

                "status": {

                    "$ne": "Completed"

                },

                "due_date": {

                    "$lt": datetime.utcnow()

                }

            }

        )

        return {

            "total": total,

            "completed": completed,

            "planning": planning,

            "in_progress": in_progress,

            "overdue": overdue

        }

    ####################################################################
    # GANTT DATA
    ####################################################################

    @classmethod
    def gantt(cls, owner_id):

        cursor = cls.collection().find(

            {

                "owner_id": ObjectId(owner_id),

                "deleted": False

            }

        )

        data = []

        for task in cursor:

            data.append({

                "id": str(task["_id"]),

                "name": task["subject"],

                "start": task["start_date"].strftime("%Y-%m-%d"),

                "end": task["due_date"].strftime("%Y-%m-%d"),

                "progress": task["progress"]

            })

        return data