from flask import Blueprint, render_template, g, abort,request,redirect,url_for
from datetime import datetime, timedelta
from db.connection import get_connection

tracking = Blueprint('tracking', __name__)

@tracking.route('/track/<tracking_number>')
def track_order(tracking_number):
    cursor = get_connection(True)
   
    cursor.execute("""
        SELECT o.*, p.name as puppy_name, p.gender, p.age, p.price
        FROM orders o
        JOIN puppy p ON o.puppy_id = p.id
        WHERE o.tracking_number = %s
    """, (tracking_number,))
    
    order = cursor.fetchone()
    cursor.close()

    if not order:
        return render_template("tracking_not_found.html")

    # Setup timeline stages
    created_at = order['created_at']
    if isinstance(created_at,str):
        created_at=datetime.fromisoformat(created_at)
    status = order['status']
    steps = [
        ("Order Placed", 0),
        ("In Production", 1),
        ("Ocean Transit", 3),
        ("Shipping Final Mile", 5),
        ("Delivered", 7)
    ]
    current_index = next((i for i, (s, _) in enumerate(steps) if s == status), 0)

    timeline = []
    for i, (label, offset) in enumerate(steps):
        date = created_at + timedelta(days=offset)
        timeline.append({
            "label": label,
            "date": date.strftime("%b %d, %Y"),
            "status": "done" if i <= current_index else "pending"
        })

    estimated_start = created_at + timedelta(days=7)
    estimated_end = created_at + timedelta(days=9)
    estimated_range = f"{estimated_start.strftime('%b %d')} - {estimated_end.strftime('%b %d')}"

    return render_template("tracking.html", order=order, timeline=timeline, estimated_range=estimated_range)


@tracking.route('/track')
def track_redirect():
    tracking_number = request.args.get("q")
    if not tracking_number:
        return render_template("tracking_not_found.html")
    return redirect(url_for('tracking.track_order', tracking_number=tracking_number))