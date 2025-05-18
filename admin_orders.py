from flask import Blueprint, jsonify, request,render_template
from utils import login_required
from db.connection import get_connection
import logging
import random
import string,json
from email_utils import send_custom_email

admin_order = Blueprint('admin_order', __name__)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    filename='admin.log',
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)
@admin_order.route('/admin/orders', methods=['GET'])
@login_required
def serve_admin_orders():
    try:
        db = get_connection()
        db.execute("""
            SELECT o.id, o.puppy_id, o.customer_name, o.customer_email, o.customer_phone, 
                   o.customer_address, o.tracking_number, o.status, o.created_at, p.name AS puppy_name
            FROM orders o
            JOIN puppy p ON o.puppy_id = p.id
            ORDER BY o.created_at DESC
        """)
        orders = db.fetchall()
        db.close()
        return render_template('admin/admin_orders.html', orders=orders)
    except Exception as e:
        logger.error(f"Error loading orders page: {e}")
        return render_template('admin/admin_orders.html', orders=[])
    
@admin_order.route('/admin/update_status', methods=['POST'])
@login_required
def update_status():
    try:
        order_id = request.form.get('order_id')
        status = request.form.get('status')

        if not order_id or not status:
            logger.error(f"Missing order_id or status: order_id={order_id}, status={status}")
            return jsonify({'success': False, 'message': 'Order ID and status are required'}), 400

        db = get_connection(True)
        db.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
        
        db.close()
        logger.info(f"Updated status to {status} for order {order_id}")
        return jsonify({'success': True, 'message': 'Status updated successfully'})

    except Exception as e:
        logger.error(f"Error updating status for order {order_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

def send_payment_confirmation_email(order_id):
    from app import app
    db = get_connection(True)
    db.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order=db.fetchone()
    if not order:
        logger.error(f"Order {order_id} not found.")
        return

    db.execute("SELECT * FROM puppy WHERE id = %s", (order['puppy_id'],))
    puppy=db.fetchone()
    if not puppy:
        logger.error(f"Puppy {order['puppy_id']} not found.")
        return

    try:
    
        contact = {
            "id":puppy['id'],
            "puppy_id":order_id,
            "customer_name":order['customer_name'],
            "email":order['customer_email'],
            "customer_phone":order["customer_phone"],
            "customer_address": order['customer_address'],
            "status":order['status']
        }
        delivery = json.loads(order['delivery_info'])
        essentials = json.loads(order['essentials']) if order['essentials'] else []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON for order {order_id}: {e}")
        return

    total = puppy.get('price', 0) + delivery.get('delivery_cost', 0)
    if essentials:
        total += sum(item.get('price', 0) for item in essentials)
    db.execute("SELECT smtp_server, smtp_port, email, username, password FROM smtp_settings LIMIT 1")
    smtp_settings = db.fetchone()
    if not smtp_settings:
        
        return jsonify({'success': False, 'message': 'No SMTP settings configured.'}), 400

    smtp_config = {
        'MAIL_SERVER': smtp_settings['smtp_server'],
        'MAIL_PORT': int(smtp_settings['smtp_port']),
        'MAIL_USERNAME': smtp_settings['username'],
        'MAIL_PASSWORD': smtp_settings['password'],
        'MAIL_DEFAULT_SENDER': smtp_settings['email'],
        'MAIL_USE_TLS': True if int(smtp_settings['smtp_port']) == 587 else False,
        'MAIL_USE_SSL': True if int(smtp_settings['smtp_port']) == 465 else False
    }
    send_custom_email(
        app=app,
        subject="Your Puppy Adoption is Confirmed!",
        recipients=[contact['email']],
        template="tem2.html",
        context={
            "contact": contact,
            "puppy": puppy,
            "delivery": delivery,
            "essentials": essentials,
            "total": total,
            "tracking_number": order['tracking_number'],
            "url_root": request.url_root,
            
        },
        smtp_config=smtp_config
        
    )
    logger.info(f"Confirmation email sent for order {order_id}.")
    db.close()
@admin_order.route('/admin/generate_tracking', methods=['POST'])
@login_required
def generate_tracking():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        if not order_id:
            logger.error("No order_id provided for tracking number generation")
            return jsonify({'success': False, 'message': 'Order ID is required'}), 400

        tracking_number = f'TRK-{order_id}' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        db = get_connection(True)
        db.execute("UPDATE orders SET tracking_number = %s WHERE id = %s", (tracking_number, order_id))
       
        db.close()

        send_payment_confirmation_email(order_id)
        logger.info(f"Generated tracking number {tracking_number} for order {order_id}")
        return jsonify({'success': True, 'tracking_number': tracking_number})

    except Exception as e:
        logger.error(f"Error generating tracking number for order {order_id}: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
@admin_order.route('/admin/delete_orders', methods=['POST'])
def delete_orders():
    data = request.get_json()
    order_ids = data.get('order_ids', [])

    if not order_ids:
        return jsonify(success=False, message="No orders selected")

    try:
        db = get_connection()
        # Prepare placeholders for SQL IN clause
        placeholders = ",".join(["%s"] * len(order_ids))
        sql = f"DELETE FROM orders WHERE id IN ({placeholders})"
        
        # Execute query (for SQLite, %s replaced by ? in your class)
        db.execute(sql, order_ids)
        db.close()
        
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))
