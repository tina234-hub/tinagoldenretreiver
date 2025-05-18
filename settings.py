from flask import Blueprint,render_template,jsonify,request,current_app,session
from db.connection import get_connection
from werkzeug.utils import secure_filename
from utils import login_required
import os
settings=Blueprint("settings",__name__)


@settings.route("/admin/get_settings",methods=['GET'])
@login_required
def get_settings():
    db = get_connection(True)
    try:
        db.execute("SELECT * FROM settings WHERE username=%s", (session['username'],))
        row = db.fetchone()
        try:
            row.pop('password')
        except:
            pass
        
        return jsonify(row if row else {})
    except Exception as e:
        print("Error fetching settings:", e)
        return jsonify({})
    finally:
        db.close()

@settings.route("/admin/update_settings", methods=["POST"])
@login_required
def update_settings():
    if "username" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.form
    file = request.files.get("logo")

    logo_filename = None
    if file:
        logo_filename = secure_filename("logo.png")
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], logo_filename))

    db = get_connection(True)
    try:
        # Start constructing the base update query
        update_query = """
            UPDATE settings SET 
                phonenumber=%s, site_name=%s, 
                email=%s, username=%s
        """
        params = [
            data["phonenumber"],
            data["site_name"],
            data["email"],
            data["username"]
        ]

        # Add the logo if provided
        if logo_filename:
            update_query += ", logo=%s"
            params.append(logo_filename)

        # Only add password if it's provided
        if data.get("password"):
            update_query += ", password=%s"
            params.append(data["password"])

        # Add the Facebook link if it's provided
        if data.get("facebook_link"):
            update_query += ", facebook_link=%s"
            params.append(data["facebook_link"])

        # Add the Instagram link if it's provided
        if data.get("ig_link"):
            update_query += ", ig_link=%s"
            params.append(data["ig_link"])

        # Add the call number if it's provided
        if data.get("call_no"):
            update_query += ", call_number=%s"
            params.append(data["call_no"])

        # Complete the query by specifying where the username matches the session username
        update_query += " WHERE username=%s"
        params.append(session["username"])

        # Execute the query
        db.execute(update_query, tuple(params))

        # Update session username if changed
        session["username"] = data["username"]
    finally:
        db.close()

    return jsonify({"success": True})