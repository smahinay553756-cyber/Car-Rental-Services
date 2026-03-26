from model.database import Database

class AuthController:
    """Handles user authentication with an efficient connection."""
    def __init__(self):
        self.db = Database()

    def login(self, username, password):
        # Attempt to connect only if necessary
        if not self.db.connect():
            return None, "Database connection failed."

        try:
            with self.db.connection.cursor() as cursor:
                query = "SELECT * FROM staff WHERE username = %s AND password = %s"
                cursor.execute(query, (username, password))
                result = cursor.fetchone()
                if result:
                    return "staff", None

                query = "SELECT * FROM users WHERE username = %s AND password = %s"
                cursor.execute(query, (username, password))
                result = cursor.fetchone()
                if result:
                    return "customer", None

            return None, "Invalid username or password."
        except Exception as e:
            return None, f"An error occurred: {e}"
        # We no longer disconnect here, to allow the connection to be reused.
        # The connection will be closed when the application exits.
