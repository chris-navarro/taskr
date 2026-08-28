"""
Task Update Repository

Handles historical progress/activity records associated
with tasks.

A task document represents the CURRENT state of a task.

A task_update document represents an EVENT that happened
during the life of that task.

Example:

Task:
    progress = 75
    status = "In Progress"

Task Updates:
    2026-08-20 -> 20%
    2026-08-23 -> 45%
    2026-08-27 -> 75%

This historical information can later be used for:

- Activity timeline
- Gantt chart
- Progress analytics
- Time tracking
- Weekly reports
- Monthly reports
- Mid-year performance reports
- Year-end performance reports
"""

from datetime import datetime

from bson import ObjectId

from flask_backend.database import mongo


class TaskUpdate:
    """
    Repository for the task_updates MongoDB collection.
    """

    COLLECTION = "task_updates"

    #####################################################################
    # COLLECTION
    #####################################################################

    @classmethod
    def collection(cls):
        """
        Return the MongoDB collection.

        Keeping this in one method means the rest of the
        application doesn't need to know how MongoDB is configured.
        """

        return mongo.db[cls.COLLECTION]

    #####################################################################
    # CREATE
    #####################################################################

    @classmethod
    def create(
        cls,
        task_id,
        user_id,
        progress,
        hours_worked=0,
        status=None,
        accomplishment="",
        blockers="",
        next_steps="",
        remarks="",
        worked_at=None
    ):
        """
        Create a historical update for a task.

        Parameters
        ----------
        task_id : str
            MongoDB ID of the task.

        user_id : str
            MongoDB ID of the user submitting the update.

        progress : int
            Current task progress from 0 to 100.

        hours_worked : float
            Number of hours worked during this update.

        status : str
            Current task status.

        accomplishment : str
            Work completed during this update.

        blockers : str
            Problems or dependencies encountered.

        next_steps : str
            Planned next actions.

        remarks : str
            Additional notes.

        worked_at : datetime
            Date/time when the work occurred.
        """

        if worked_at is None:

            worked_at = datetime.utcnow()

        document = {

            "task_id": ObjectId(task_id),

            "user_id": ObjectId(user_id),

            "progress": int(progress),

            "hours_worked": float(hours_worked),

            "status": status,

            "accomplishment": accomplishment.strip(),

            "blockers": blockers.strip(),

            "next_steps": next_steps.strip(),

            "remarks": remarks.strip(),

            "worked_at": worked_at,

            "created_at": datetime.utcnow()

        }

        return cls.collection().insert_one(document)

    #####################################################################
    # GET ONE
    #####################################################################

    @classmethod
    def get(cls, update_id):
        """
        Return a single task update.
        """

        try:

            return cls.collection().find_one({

                "_id": ObjectId(update_id)

            })

        except Exception:

            return None

    #####################################################################
    # GET ALL UPDATES FOR A TASK
    #####################################################################

    @classmethod
    def for_task(
        cls,
        task_id,
        limit=None
    ):
        """
        Return task updates ordered from newest to oldest.
        """

        try:

            query = {

                "task_id": ObjectId(task_id)

            }

        except Exception:

            return []

        cursor = (

            cls.collection()

            .find(query)

            .sort("worked_at", -1)

        )

        if limit:

            cursor = cursor.limit(limit)

        return list(cursor)

    #####################################################################
    # GET CHRONOLOGICAL UPDATES
    #####################################################################

    @classmethod
    def timeline(cls, task_id):
        """
        Return updates from oldest to newest.

        Useful for displaying a chronological timeline.
        """

        try:

            task_object_id = ObjectId(task_id)

        except Exception:

            return []

        cursor = (

            cls.collection()

            .find({

                "task_id": task_object_id

            })

            .sort("worked_at", 1)

        )

        return list(cursor)

    #####################################################################
    # UPDATE
    #####################################################################

    @classmethod
    def update(cls, update_id, values):
        """
        Update an existing activity record.
        """

        allowed_fields = {

            "progress",

            "hours_worked",

            "status",

            "accomplishment",

            "blockers",

            "next_steps",

            "remarks",

            "worked_at"

        }

        clean_values = {

            key: value

            for key, value in values.items()

            if key in allowed_fields

        }

        if not clean_values:

            return None

        clean_values["updated_at"] = datetime.utcnow()

        try:

            return cls.collection().update_one(

                {

                    "_id": ObjectId(update_id)

                },

                {

                    "$set": clean_values

                }

            )

        except Exception:

            return None

    #####################################################################
    # DELETE
    #####################################################################

    @classmethod
    def delete(cls, update_id):
        """
        Permanently delete a task update.

        Unlike tasks, historical updates are not soft deleted
        in this initial implementation.

        We can change this to soft deletion later if audit
        requirements demand it.
        """

        try:

            return cls.collection().delete_one({

                "_id": ObjectId(update_id)

            })

        except Exception:

            return None

    #####################################################################
    # TOTAL HOURS
    #####################################################################

    @classmethod
    def total_hours(cls, task_id):
        """
        Calculate the total number of hours recorded
        against a task.
        """

        try:

            task_object_id = ObjectId(task_id)

        except Exception:

            return 0

        result = cls.collection().aggregate([

            {

                "$match": {

                    "task_id": task_object_id

                }

            },

            {

                "$group": {

                    "_id": None,

                    "total_hours": {

                        "$sum": "$hours_worked"

                    }

                }

            }

        ])

        result = list(result)

        if not result:

            return 0

        return result[0].get(

            "total_hours",

            0

        )

    #####################################################################
    # LATEST UPDATE
    #####################################################################

    @classmethod
    def latest(cls, task_id):
        """
        Return the most recent update for a task.
        """

        try:

            return cls.collection().find_one(

                {

                    "task_id": ObjectId(task_id)

                },

                sort=[

                    ("worked_at", -1)

                ]

            )

        except Exception:

            return None

    #####################################################################
    # UPDATE COUNT
    #####################################################################

    @classmethod
    def count(cls, task_id):
        """
        Return the number of updates recorded for a task.
        """

        try:

            return cls.collection().count_documents({

                "task_id": ObjectId(task_id)

            })

        except Exception:

            return 0

    #####################################################################
    # DATE RANGE
    #####################################################################

    @classmethod
    def between(
        cls,
        task_id,
        start_date,
        end_date
    ):
        """
        Return updates between two dates.

        This will be important for:

        - Weekly reports
        - Monthly reports
        - Mid-year reports
        - Year-end reports
        """

        try:

            task_object_id = ObjectId(task_id)

        except Exception:

            return []

        return list(

            cls.collection()

            .find({

                "task_id": task_object_id,

                "worked_at": {

                    "$gte": start_date,

                    "$lte": end_date

                }

            })

            .sort(

                "worked_at",

                1

            )

        )

    #####################################################################
    # USER ACTIVITY
    #####################################################################

    @classmethod
    def by_user(
        cls,
        user_id,
        start_date=None,
        end_date=None
    ):
        """
        Return all task activity created by a user.

        This is particularly useful for performance reporting.
        """

        try:

            user_object_id = ObjectId(user_id)

        except Exception:

            return []

        query = {

            "user_id": user_object_id

        }

        if start_date or end_date:

            query["worked_at"] = {}

            if start_date:

                query["worked_at"]["$gte"] = start_date

            if end_date:

                query["worked_at"]["$lte"] = end_date

        return list(

            cls.collection()

            .find(query)

            .sort(

                "worked_at",

                -1

            )

        )

    #####################################################################
    # USER TOTAL HOURS
    #####################################################################

    @classmethod
    def user_total_hours(
        cls,
        user_id,
        start_date=None,
        end_date=None
    ):
        """
        Calculate total hours worked by a user.

        Useful for performance reports and productivity analytics.
        """

        try:

            user_object_id = ObjectId(user_id)

        except Exception:

            return 0

        match = {

            "user_id": user_object_id

        }

        if start_date or end_date:

            match["worked_at"] = {}

            if start_date:

                match["worked_at"]["$gte"] = start_date

            if end_date:

                match["worked_at"]["$lte"] = end_date

        result = cls.collection().aggregate([

            {

                "$match": match

            },

            {

                "$group": {

                    "_id": None,

                    "total_hours": {

                        "$sum": "$hours_worked"

                    }

                }

            }

        ])

        result = list(result)

        if not result:

            return 0

        return result[0].get(

            "total_hours",

            0

        )

    #####################################################################
    # ACCOMPLISHMENTS
    #####################################################################

    @classmethod
    def accomplishments(
        cls,
        user_id,
        start_date=None,
        end_date=None
    ):
        """
        Return updates containing accomplishments.

        This gives the reporting module a clean source for
        generating performance summaries.
        """

        try:

            user_object_id = ObjectId(user_id)

        except Exception:

            return []

        query = {

            "user_id": user_object_id,

            "accomplishment": {

                "$nin": [

                    "",

                    None

                ]

            }

        }

        if start_date or end_date:

            query["worked_at"] = {}

            if start_date:

                query["worked_at"]["$gte"] = start_date

            if end_date:

                query["worked_at"]["$lte"] = end_date

        return list(

            cls.collection()

            .find(query)

            .sort(

                "worked_at",

                -1

            )

        )

    #####################################################################
    # BLOCKERS
    #####################################################################

    @classmethod
    def blockers(
        cls,
        user_id,
        start_date=None,
        end_date=None
    ):
        """
        Return updates containing blockers.

        Useful for identifying recurring impediments.
        """

        try:

            user_object_id = ObjectId(user_id)

        except Exception:

            return []

        query = {

            "user_id": user_object_id,

            "blockers": {

                "$nin": [

                    "",

                    None

                ]

            }

        }

        if start_date or end_date:

            query["worked_at"] = {}

            if start_date:

                query["worked_at"]["$gte"] = start_date

            if end_date:

                query["worked_at"]["$lte"] = end_date

        return list(

            cls.collection()

            .find(query)

            .sort(

                "worked_at",

                -1

            )

        )

    #####################################################################
    # MONTHLY SUMMARY
    #####################################################################

    @classmethod
    def monthly_summary(
        cls,
        user_id,
        year
    ):
        """
        Aggregate task activity by month.

        Example result:

        January   -> 32 hours
        February  -> 41 hours
        March     -> 37 hours

        This will eventually feed performance dashboards.
        """

        try:

            user_object_id = ObjectId(user_id)

        except Exception:

            return []

        pipeline = [

            {

                "$match": {

                    "user_id": user_object_id

                }

            },

            {

                "$project": {

                    "month": {

                        "$month": "$worked_at"

                    },

                    "year": {

                        "$year": "$worked_at"

                    },

                    "hours_worked": 1

                }

            },

            {

                "$match": {

                    "year": year

                }

            },

            {

                "$group": {

                    "_id": "$month",

                    "hours": {

                        "$sum": "$hours_worked"

                    },

                    "updates": {

                        "$sum": 1

                    }

                }

            },

            {

                "$sort": {

                    "_id": 1

                }

            }

        ]

        return list(

            cls.collection().aggregate(

                pipeline

            )

        )

    #####################################################################
    # CREATE INDEXES
    #####################################################################

    @classmethod
    def create_indexes(cls):
        """
        Create indexes required for efficient task history queries.

        This method can be called during application startup.
        """

        collection = cls.collection()

        collection.create_index(

            [

                ("task_id", 1),

                ("worked_at", -1)

            ]

        )

        collection.create_index(

            [

                ("user_id", 1),

                ("worked_at", -1)

            ]

        )

        collection.create_index(

            [

                ("worked_at", -1)

            ]

        )