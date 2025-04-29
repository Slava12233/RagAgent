"""
Test script for verifying direct database connection.

This is a simple test script to check the connection to the Supabase PostgreSQL database.
It's not part of the main application and is kept for reference purposes only.
"""

import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

print(f"Connecting to PostgreSQL database...")
print(f"Host: {HOST}")
print(f"Database: {DBNAME}")
print(f"User: {USER}")

# Connect to the database
try:
    connection = psycopg2.connect(
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        dbname=DBNAME,
        sslmode='require'  # Important for Supabase
    )
    print("Connection successful!")
    
    # Create a cursor to execute SQL queries
    cursor = connection.cursor()
    
    # Example query
    cursor.execute("SELECT NOW();")
    result = cursor.fetchone()
    print("Current Time:", result[0])

    # Another example: check PostgreSQL version
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print("PostgreSQL Version:", version[0])

    # Close the cursor and connection
    cursor.close()
    connection.close()
    print("Connection closed.")

except Exception as e:
    print(f"Failed to connect: {e}") 