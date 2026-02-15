import mysql.connector
from mysql.connector import errorcode

def get_db_connection():
    """
    Establishes and returns a connection object to the MySQL database.
    This function does NOT return a cursor.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="onkar",
            database="cms_db"
        )
        print("Database connection successful!")
        return conn
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Error: Invalid username or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Error: Database does not exist.")
        else:
            print(f"Error: {err}")
        return None