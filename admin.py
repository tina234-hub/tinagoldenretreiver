from flask import Blueprint,render_template,session,request,redirect,flash,jsonify,url_for,current_app
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from db.connection import get_connection
from utils import login_required
import os


admin=Blueprint("admin",__name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__),'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin.route("/admin/dashboard")
@login_required
def dashboard():
    cursor=get_connection(True)
   
    try:
        cursor.execute("SELECT date, visits FROM traffic ORDER BY date DESC LIMIT 7")  # Last 7 days of traffic
        data = cursor.fetchall()
        dates = [row[0] for row in data]
        visits = [row[1] for row in data]
    finally:
        cursor.close()
       
    
    return render_template("admin/dashboard.html",dates=dates, visits=visits)

@admin.route("/admin/settings")
@login_required
def settings():
    return render_template("admin/settings.html")

@admin.route("/admin/puppies", methods=["GET", "POST"])
@login_required
def puppies():
    cursor=get_connection(True)
    

    if request.method == "POST":
        # Get other form data
        name = request.form['name']
        gender = request.form['gender']
        age = request.form['age']
        price = request.form['price']
        dob = request.form['dob']
        color = request.form['color']
        variety = request.form['variety']
        about = request.form['about']
        mom_weight = request.form['mom_weight']
        mom_color = request.form['mom_color']
        dad_color = request.form['dad_color']
        dad_weight = request.form['dad_weight']
        # other fields...

        # Handle single mom image upload
        mom_image = request.files.get('mom_image')
        mom_image_filename = ''
        if mom_image and allowed_file(mom_image.filename):
            mom_image_filename = secure_filename(mom_image.filename)
            mom_image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], mom_image_filename))

        # Handle single dad image upload
        dad_image = request.files.get('dad_image')
        dad_image_filename = ''
        if dad_image and allowed_file(dad_image.filename):
            dad_image_filename = secure_filename(dad_image.filename)
            dad_image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], dad_image_filename))

        # Handle multiple general images
        general_images = request.files.getlist('images')
        general_image_names = []
        
        for image in general_images:
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                general_image_names.append(filename)

        # Convert general image filenames to a comma-separated string
        general_images_str = ','.join(general_image_names)

        try:
            # Insert the new puppy into the database
 
            cursor.execute("""
                INSERT INTO puppy (name, gender, age, price, dob, color, variety, images, about, mom_weight, mom_color, dad_color, dad_weight, mom_image, dad_image)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
            """, (name, gender, age, price, dob, color, variety, general_images_str, about, mom_weight, mom_color, dad_color, dad_weight, mom_image_filename, dad_image_filename))
           
           
            return jsonify({"success": True})
        except Exception as e:
            print(e)
            return jsonify({"success": False})
    cursor.execute("SELECT * FROM puppy")
    puppiess=cursor.fetchall()
    print(cursor.fetchall())
    return render_template("admin/puppies.html",puppies=puppiess)
@admin.route('/admin/get_puppies')
@login_required
def get_puppies():
    cursor = get_connection(True)
    try:
        cursor.execute("SELECT id, name, gender, age, price, dob FROM puppy ORDER BY id DESC")
        puppies = cursor.fetchall()
    finally:
        cursor.close()
    return jsonify(puppies)

@admin.route('/admin/delete_puppy/<int:puppy_id>', methods=['DELETE'])
@login_required
def delete_puppy(puppy_id):
    try:
        cursor = get_connection(True)
        cursor.execute("DELETE FROM puppy WHERE id = %s", (puppy_id,))
        return jsonify({"success": True})
    except Exception as e:
        print("Delete error:", e)
        return jsonify({"success": False})

@admin.route("/admin/login",methods=['GET','POST'])
def login():
    next_url=request.args.get("next") or ""
    next_=next_url.lower().split('admin')

    print(next_)
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_connection(True)
        try:
            db.execute("SELECT * FROM settings WHERE id = 1 AND username = %s", (username,))
            user = db.fetchone()
        finally:
            db.close()

        if user and check_password_hash(user["password"], password):
            session["admin_logged_in"] = True
            session['username']=username
            if next_url !="":
                next_=next_url.lower().split('admin')
                return redirect(f"/admin{next_[-1]}")
            return redirect(url_for("admin.dashboard"))  # Change to your dashboard route
        else:
            return render_template("admin/login.html", error="Invalid username or password.")


    return render_template("admin/login.html")


@admin.route("/admin/logout")
@login_required
def logout():
    session.clear()
    return redirect('admin.login')

