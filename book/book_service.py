from flask import Flask, jsonify
import mysql.connector
import os
from mysql.connector import errorcode

app = Flask(__name__)

# --- Database Connection Function ---
def get_db():
    """
    Establishes a connection to the MySQL database.
    
    It explicitly reads DB_PORT (required for the fix) and includes error handling
    for connection failures.
    """
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "db"),
            # Read DB_PORT explicitly and convert to int for robust connection
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "root"),
            database=os.getenv("DB_NAME", "digital_library")
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        # Re-raise the exception to be caught by the route handler
        raise

@app.route("/books", methods=["GET"])
def get_books():
    """Fetches all books from the database, wrapped in error handling."""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        print("Successfully fetched all books.")
        return jsonify(books)
    except mysql.connector.Error as err:
        # Handles errors during the query (e.g., table not found)
        print(f"Database Error during get_books: {err}")
        return jsonify({"message": "Failed to fetch books due to a database error."}), 500
    except Exception as e:
        # Handles non-database related unexpected errors (e.g., get_db failure)
        print(f"An unexpected error occurred: {e}")
        return jsonify({"message": "An unexpected server error occurred."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
