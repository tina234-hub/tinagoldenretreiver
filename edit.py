from flask import Blueprint,render_template,jsonify,request,current_app
from db.connection import get_connection
from werkzeug.utils import secure_filename
from utils import login_required
import os
edit=Blueprint("edit",__name__)


@edit.route("/admin/get_puppy/<int:id>")
@login_required
def get_puppy(id):
    cursor = get_connection(True)
    try:
        cursor.execute("SELECT * FROM puppy WHERE id = %s", (id,))
        puppy = cursor.fetchone()
    finally:
        cursor.close()
    return jsonify(puppy)

@edit.route("/admin/update_puppy", methods=["POST"])
@login_required
def update_puppy():
    data = request.form
    cursor = get_connection(True)
    try:
        cursor.execute("""
            UPDATE puppy
            SET name=%s, gender=%s, age=%s, price=%s, dob=%s, color=%s, variety=%s, about=%s
            WHERE id=%s
        """, (
            data['name'], data['gender'], data['age'], data['price'], data['dob'],
            data.get('color', ''), data.get('variety', ''), data.get('about', ''), data['id']
        ))
    finally:
        cursor.close()
        
    return jsonify({"success": True})


#####reveiw
@edit.route("/admin/reviews")
@login_required
def review():
    return render_template("admin/reviews.html")
@edit.route("/admin/show_reviews", methods=["GET"])
def fetch_reviews():
    cursor = get_connection(True)
    try:
        cursor.execute("SELECT * FROM review ORDER BY date DESC")
        reviews = cursor.fetchall()
    finally:
        cursor.close()
    return jsonify(reviews)

@edit.route("/admin/add_review", methods=["POST"])
@login_required
def add_review():
    name = request.form["name"]
    review_text = request.form["review_text"]
    date = request.form["date"]

    # Handle image
    image_file = request.files.get("picture")
    filename = None
    if image_file:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)

    cursor = get_connection(True)
    try:
       
        cursor.execute("""
            INSERT INTO review (name, picture, review_text, date)
            VALUES (%s, %s, %s, %s)
        """, (name, filename, review_text, date))
    finally:
        cursor.close()
    return jsonify({"success": True})
@edit.route("/admin/delete_review/<int:review_id>", methods=["POST"])
@login_required
def delete_review(review_id):
    cursor = get_connection(True)
    try:
        cursor.execute("DELETE FROM review WHERE id = %s", (review_id,))
        
    finally:
        cursor.close()
    return jsonify({"success": True})

@edit.route("/admin/update_review", methods=["POST"])
@login_required
def update_review():
    data = request.form
    review_id = data["id"]
    name = data["name"]
    review_text = data["review_text"]
    date = data["date"]

    picture = None
    if "picture" in request.files:
        picture_file = request.files["picture"]
        if picture_file:
            picture = secure_filename(picture_file.filename)
            picture_path = os.path.join(current_app.config["UPLOAD_FOLDER"], picture)
            picture_file.save(picture_path)

    cursor = get_connection(True)
    try:
        if picture:
            cursor.execute("""
                UPDATE review SET name=%s, picture=%s, review_text=%s, date=%s WHERE id=%s
            """, (name, picture, review_text, date, review_id))
        else:
            cursor.execute("""
                UPDATE review SET name=%s, review_text=%s, date=%s WHERE id=%s
            """, (name, review_text, date, review_id))
    finally:
        cursor.close()
        
    return jsonify({"success": True})
