from flask import Flask, request, jsonify
import mysql.connector
import os
from mysql.connector import errorcode

app = Flask(__name__)

# --- Database Connection Function ---
def get_db():
    """
    Establishes a connection to the MySQL database.
    
    It explicitly reads DB_PORT and includes error handling for connection failures.
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

@app.route("/borrow", methods=["POST"])
def borrow_book():
    """Handles borrowing a book, with specific error handling for foreign key issues."""
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        print(f"Attempting to borrow book_id {data['book_id']} for user_id {data['user_id']}")

        cursor.execute("INSERT INTO borrow_records (user_id, book_id) VALUES (%s, %s)",
                       (data["user_id"], data["book_id"]))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Book borrowed"}), 201

    except mysql.connector.Error as err:
        # Check for Foreign Key constraint failure (e.g., user_id or book_id does not exist)
        if err.errno == errorcode.ER_NO_REFERENCED_ROW_2 or err.errno == errorcode.ER_NO_REFERENCED_ROW:
            print(f"Borrow failed: User or Book ID does not exist. Error: {err}")
            return jsonify({"message": "Borrow failed: Invalid User ID or Book ID."}), 400
        
        print(f"Database Error during borrow_book: {err}")
        return jsonify({"message": "Borrow failed due to server error."}), 500
    except Exception as e:
        print(f"An unexpected error occurred during borrow_book: {e}")
        return jsonify({"message": "An unexpected server error occurred."}), 500

@app.route("/mybooks/<int:user_id>", methods=["GET"])
def my_books(user_id):
    """Retrieves all borrowed books for a specific user, with error handling."""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        print(f"Fetching books for user ID: {user_id}")

        cursor.execute("""
            SELECT b.title, b.author, br.borrow_date 
            FROM borrow_records br
            JOIN books b ON br.book_id = b.id
            WHERE br.user_id=%s
        """, (user_id,))
        
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"Found {len(books)} books for user ID: {user_id}")
        return jsonify(books)

    except mysql.connector.Error as err:
        print(f"Database Error during my_books: {err}")
        return jsonify({"message": "Failed to fetch borrowed books due to a database error."}), 500
    except Exception as e:
        print(f"An unexpected error occurred during my_books: {e}")
        return jsonify({"message": "An unexpected server error occurred."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
