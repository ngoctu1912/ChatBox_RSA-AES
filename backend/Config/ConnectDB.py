import mysql.connector
from mysql.connector import errorcode

def connect_to_database():
    """
    Kết nối đến MySQL database
    Returns: (connection, cursor) với cursor dictionary=True
    """
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='projects',
            password='12345678',
            database='chatbox'
        )
        
        if conn.is_connected():
            cursor = conn.cursor(dictionary=True)
            return conn, cursor  
        else:
            print("Failed to connect to database")
            return None, None
            
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
        return None, None  