import os
from flask import Flask, render_template,request,jsonify,Response,make_response,session
from werkzeug.utils import secure_filename
from admin import admin,UPLOAD_FOLDER
from edit import edit
from checkout import checkout
import requests
from settings import settings
from db.connection import get_connection
import secrets
from admin_orders import admin_order
from tracking import tracking
from payment import payment
from api import api
from admin_smtp import admin_smtp
app= Flask(__name__)
app.secret_key=secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] =  os.path.join(os.path.dirname(__file__),'static/uploads')
app.register_blueprint(admin)
app.register_blueprint(edit)
app.register_blueprint(settings)
app.register_blueprint(checkout)
app.register_blueprint(admin_order)
app.register_blueprint(tracking)
app.register_blueprint(payment)
app.register_blueprint(api)
app.register_blueprint(admin_smtp)
# Route for homepage
@app.route('/')
def index():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template("about.html")
@app.route('/preview')
def preview():
    puppy_id = request.args.get("id")
    if not puppy_id or not puppy_id.isdigit():
        return "Invalid ID", 400

    db = get_connection(True)
    try:
        db.execute("SELECT * FROM puppy WHERE id = %s", (puppy_id,))
        puppy = db.fetchone()
        db.execute("SELECT * FROM review")
        reviews=db.fetchall()
        
        if not puppy:
            return "Puppy not found", 404
    finally:
        db.close()
    
    return render_template("preview.html", puppy=puppy,reviews=reviews,randomnumber=secrets.token_hex(6))
    

@app.route('/promise')
def promise():
    return render_template('promise.html')
@app.route('/available_puppies')
def ava_pup():
    cursor=get_connection(True)
    try:
        cursor.execute("SELECT id,name,images,age FROM puppy ")
        puppies=cursor.fetchall() or {}
    finally:
        cursor.close()
    return render_template("available.html",puppies=puppies)

@app.context_processor
def inject_settings():
    db = get_connection(True)
    try:
        db.execute("SELECT logo, email, phonenumber,call_number,ig_link, site_name,facebook_link FROM settings LIMIT 1")
        settings = db.fetchone() or {}
    finally:
        db.close()
    return dict(site=settings)
@app.route('/proxy-image')
def proxy_image():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Spoof headers to act like a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": url,  # Use the same image URL as referer to pass hotlink checks
        }

        # Use stream=True to control reading content
        resp = requests.get(url, headers=headers, stream=True, timeout=5)

        if resp.status_code != 200 or 'image' not in resp.headers.get('Content-Type', ''):
            print( jsonify({
                "error": "Invalid image or inaccessible",
                "status": resp.status_code,
                "content_type": resp.headers.get('Content-Type', ''),
            }))

        # Remove content-disposition if present
        
        return Response(resp.content, mimetype=resp.headers['Content-Type'])

    except Exception as e:
        return jsonify({"error": "Failed to fetch image", "details": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True)

