from flask import Blueprint, request, jsonify, current_app
from difflib import get_close_matches
from db.connection import get_connection

api = Blueprint('api', __name__)

# Register the close_connection function with Flask's teardown

@api.route('/api/puppies', methods=['GET'])
def get_puppy_by_name():
    try:
        name_query = request.args.get('name', '').strip().lower()
        if not name_query:
            return jsonify({"error": "Name query parameter is required"}), 400

        db = get_connection()
        # Get all puppy names
        db.execute("SELECT name FROM puppy")
        names = [row['name'].lower() for row in db.fetchall()]  # Extract strings

        # Use difflib to find the closest match
        matches = get_close_matches(name_query, names, n=1, cutoff=0.6)

        if not matches:
            return jsonify({"error": "No matching puppy found"}), 404

        matched_name = matches[0]

        # Fetch full puppy info for the matched name
        db.execute("""
            SELECT name, gender, price, dob, color, variety, about, mom_weight, dad_weight,age
            FROM puppy
            WHERE LOWER(name) = ?
            LIMIT 1
        """, (matched_name,))
        row = db.fetchone()

        if row:
            puppy_data = {
                "name": row['name'],
                "gender": row['gender'],
                "price": row['price'],
                "dob": row['dob'],
                "age": row['age'],
                "color": row['color'],
                "variety": row['variety'],
                "about": row['about'],
                "mom_weight": row['mom_weight'],
                "dad_weight": row['dad_weight']

            }
            return jsonify(puppy_data)
        else:
            return jsonify({"error": "Match not found"}), 404

    except Exception as e:
        current_app.logger.error(f"Error in get_puppy_by_name: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500