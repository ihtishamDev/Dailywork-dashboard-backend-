import mysql.connector

def get_connection():

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Ihtisham@123",
        database="dailytask"
    )
    return conn
