# Import SQLAlchemy ORM for database connection and management
from flask_sqlalchemy import SQLAlchemy

# Define a Singleton class to manage the database connection
class DatabaseSingleton:
    # Class variable to hold the single instance
    _instance = None

    # __new__ is called when creating a new instance of the class
    def __new__(cls, app=None):
        # Check if an instance already exists
        if cls._instance is None:
            # If not, create a new instance
            cls._instance = super(DatabaseSingleton, cls).__new__(cls)

            # Initialize the database connection if Flask app is provided
            if app:
                cls._instance.db = SQLAlchemy(app)

        # Return the existing instance (or newly created one)
        return cls._instance
