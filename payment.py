from flask import Blueprint,render_template,request,session,redirect,url_for,flash,jsonify
from db.connection import get_connection
from werkzeug.utils import secure_filename
import random,string,os,time
import threading


payment=Blueprint("payment",__name__)

def generate_tracking(puppy_id):
    suffix=''.join(random.choices(string.ascii_uppercase + string.digits,k=4))
    return f"TGR-{str(puppy_id).zfill(4)}-{suffix}"

@payment.route("/payment", methods=["POST"])
def save_payment_method():
    data = request.get_json()
    order_id = data.get("order_id")
    method = data.get("payment_method")
    extra_data = data.get("details", {})

    # Fetch puppy_id from orders
    
    cur = get_connection(True)
    cur.execute("SELECT puppy_id FROM orders WHERE id = %s", (order_id,))
    row = cur.fetchone()
    if not row:
        return {"status": "error", "message": "Order not found"}, 404

    puppy_id = row["puppy_id"]
    tracking_number = generate_tracking(puppy_id)

    cur.execute("""
        UPDATE orders
        SET payment_method=%s, tracking_number=%s, status='Order Placed'
        WHERE id=%s
    """, (method, tracking_number, order_id))
    cur.close()

    return {"status": "ok", "tracking": tracking_number}, 200


@payment.route("/upload_receipt", methods=["POST"])
def upload_receipt():
    receipt = request.files.get("receipt")
    order_id = request.form.get("order_id")
    
    if receipt and order_id:
        filename = secure_filename(receipt.filename)
        receipt_path = os.path.join("static/receipts", filename)
        receipt.save(receipt_path)

        # Save file + mark order as pending review
        db = get_connection(True)
        db.execute("UPDATE orders SET receipt_path = %s, status = 'pending_review' WHERE id = %s", (filename, order_id))
        
        db.close()

        tracking = generate_tracking(order_id)
        return jsonify({"status": "pending", "tracking": tracking})
    return jsonify({"status": "error"}), 400

@payment.route("/paymentapi")
def payment_api():
    amount=request.args.get('amount')
    special_key=request.args.get('specialkey')
    order_id=request.args.get('order_id')

    threading.Thread(target=simulate_payment_success,args=(order_id,),daemon=True).start()
    return render_template("fake.html",amount=amount,special_key=special_key,order_id=order_id)
def simulate_payment_success(order_id):
    time.sleep(60)
    db=get_connection(True)
    db.execute("UPDATE orders SET payment_status='paid' WHERE id =%s",(order_id,))
    db.close()