import pymysql

class Database:
    """A stable database connector using pymysql."""
    def __init__(self):
        self.connection = None
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "", # Assuming empty password
            "database": "se_enterprise",
            "cursorclass": pymysql.cursors.DictCursor,
            "connect_timeout": 5 # Add a 5-second timeout
        }

    def connect(self):
        try:
            # Only connect if there isn't an active connection
            if not self.connection:
                self.connection = pymysql.connect(**self.db_config)
            return True
        except pymysql.MySQLError as e:
            print(f"DATABASE ERROR: {e}")
            self.connection = None # Ensure connection is reset on failure
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
