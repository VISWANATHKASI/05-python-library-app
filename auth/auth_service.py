from flask import Flask, request, jsonify
import mysql.connector
import os
from mysql.connector import errorcode

app = Flask(__name__)

# --- Database Connection Function ---
def get_db():
    """
    Establishes a connection to the MySQL database.
    
    It now explicitly reads DB_PORT, making it more robust, 
    and includes error handling for failed connections.
    """
    try:
        # DB_HOST: 'flm_db' (Read from docker-compose.yml)
        # DB_PORT: '3306' (Read from docker-compose.yml)
        # Default user/password are assumed to be 'root'/'root'
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "db"),
            # Read DB_PORT explicitly and convert to int
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

@app.route("/signup", methods=["POST"])
def signup():
    """Handles user sign-up, including specific error handling for duplicate emails."""
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # NOTE: This uses the 'password' field directly, which is highly insecure.
        # In a real app, this should be a hashed password (e.g., using bcrypt).
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (data["name"], data["email"], data["password"])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "User created"}), 201

    except mysql.connector.Error as err:
        # Check for IntegrityError, which often indicates a duplicate entry (e.g., unique email constraint)
        if err.errno == errorcode.ER_DUP_ENTRY:
            # Return 409 Conflict for a user-friendly message on the frontend
            return jsonify({"message": "Signup failed: Email address is already registered."}), 409
        
        # Catch connection errors or other general database failures
        print(f"Database Error during signup: {err}")
        return jsonify({"message": "Signup failed due to server error or connection failure."}), 500

@app.route("/signin", methods=["POST"])
def signin():
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM users WHERE email=%s AND password=%s",
                       (data["email"], data["password"]))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            # Ensure the primary key column name is 'id' as used in the query
            return jsonify({"message": "Login success", "user_id": user["id"], "name": user["name"]})
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    except mysql.connector.Error as err:
        print(f"Database Error during signin: {err}")
        return jsonify({"message": "Login failed due to server error."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
