from flask import Blueprint,render_template,request,session,redirect,url_for,flash,jsonify,current_app
from db.connection import get_connection
from werkzeug.utils import secure_filename
from datetime  import datetime,timedelta,timezone
from werkzeug.utils import secure_filename
import json
from email_utils import send_custom_email


checkout=Blueprint("checkout",__name__)
checkout_flow = ['details',"delivery","essentials","payment"]
@checkout.before_request
def enforce_session_expiration():
    if 'checkouts' in session:
        expired = []
        now = datetime.now(timezone.utc)
        checkouts = session['checkouts']

        # Remove expired or completed
        for order_id, data in checkouts.items():
            try:
                created = datetime.fromisoformat(data['start_time'])
                if now > created + timedelta(hours=24) or data.get('complete'):
                    expired.append(order_id)
            except:
                expired.append(order_id)

        for oid in expired:
            checkouts.pop(oid, None)

        # Limit to 5 sessions, remove oldest
        if len(checkouts) > 5:
            sorted_sessions = sorted(checkouts.items(), key=lambda x: x[1]['start_time'])
            for oid, _ in sorted_sessions[:len(checkouts)-5]:
                checkouts.pop(oid)

        session.modified = True
@checkout.route("/checkout/<step>/order/<order_id>/<rand>")
def  render_checkout_main(step,order_id,rand):
    session['step']=step
    if step not in checkout_flow:
        return "invalid",404

    return render_template("checkout.html")
@checkout.route("/checkout/step/<step>/order/<order_id>/<rand>")
def proctected_checkout(step,order_id,rand):
    print("requested step:", step)
    print('ORDER_ID',order_id)
    print("session checkouts:",session.get('checkouts'))
    print(order_id)
    if step not in checkout_flow:
        return "Invalid step", 404
    is_ajax=request.headers.get("X-Requested-width"=="XMLHttpRequest")
    step_index = checkout_flow.index(step)
    session.setdefault('checkouts', {})
    checkout_sessions = session['checkouts']
    checkout = checkout_sessions.get(order_id)

    if not checkout:
        if step != 'details':
            # Graceful restart
            flash("Your session has expired. Starting over.")
            return redirect(url_for('checkout.render_checkout_main', step='details', order_id=order_id, rand=rand))
        checkout_sessions[order_id] = {
            'rand': rand,
            'step_index': 0,
            'start_time': datetime.now(timezone.utc).isoformat()
        }
        session.modified = True
    else:
        if checkout['rand'] != rand:
            return "Session mismatch or expired", 403
        if datetime.fromisoformat(checkout['start_time']) + timedelta(hours=24) < datetime.now(timezone.utc):
            del checkout_sessions[order_id]
            session.modified = True
            flash("Your session expired. Please restart.")
            return redirect(url_for('checkout.render_checkout_main', step='details', order_id=order_id, rand=rand))
        
        current_index = checkout['step_index']
        
        if step_index > current_index:
            if is_ajax:
                return "NOT allowed skip steps"
            print("IN PROTECTED CHECKOUT")
           
            return redirect(url_for('checkout.proctected_checkout', step=checkout_flow[current_index], order_id=order_id, rand=rand))

        checkout['step_index'] = max(current_index, step_index)
        
        session.modified = True

    # Include saved form data (e.g. contact)
    contact = session.get('contact_info', {}).get(order_id, {})
   
    db=get_connection(True)
    db.execute("SELECT * FROM puppy WHERE id =%s",(order_id,))
    puppy=db.fetchone()
    db.close()
    session['step']=step
    if step=="payment":
        contact_info=session.get('contact_info',{}).get(order_id,{})
        delivery_info=session.get('essentials_info',{}).get(order_id,{})
        essentials=session.get('essentials_selected',{}).get(order_id,{})
        db = get_connection(True)

        # Insert order if not exists
        db.execute("""
        INSERT INTO orders (
            puppy_id, customer_name, customer_email, customer_phone, customer_address,
            payment_status, delivery_info, essentials
        )
        SELECT %s, %s, %s, %s, %s, %s, %s, %s
        WHERE NOT EXISTS (
            SELECT 1 FROM orders WHERE puppy_id = %s
        )
    """, (
        order_id,
        contact_info.get('name'),
        contact_info.get('email'),
        contact_info.get('phone'),
        contact_info.get('address'),
        'pending',
        json.dumps(delivery_info),
        json.dumps(essentials),
        order_id
    ))

        db.close()
        return render_template("payment.html",order_id=order_id,contact=contact_info,rand=rand,delivery=delivery_info,essentials=essentials,puppy=puppy)
    return render_template(f'{step}.html', order_id=order_id, rand=rand, contact=contact,puppy=puppy)

@checkout.route('/contact_details', methods=['POST'])
def save_contact_details():
    name = request.form.get('fullname')
    phone = request.form.get('phonenumber')
    email = request.form.get('email')
    add2 = request.form.get('add2') if request.form.get('add2') != '' else ""
    address = f"{request.form.get('add1')} {add2} {request.form.get('add3')} {request.form.get('add4')} {request.form.get('add5')}"
    order_id = request.args.get('order_id')

    session.setdefault('contact_info', {})
    session['contact_info'][order_id] = {
        'name': name,
        'phone': phone,
        'email': email,
        'address': address
    }

    # ✅ Safely reinitialize session checkouts if missing
    session.setdefault('checkouts', {})
    if order_id not in session['checkouts']:
        # Rebuild basic session if missing (fallback)
        session['checkouts'][order_id] = {
            'rand': session.get('rand', 'fallback'),
            'step_index': 1,
            'start_time': datetime.now(timezone.utc).isoformat()
        }
    else:
        session['checkouts'][order_id]['step_index'] = 1  # Advance to delivery
    
    session.modified = True

    return {'status': 'ok'}, 200
@checkout.route('/delivery', methods=['POST'])
def save_delivery():
    data = request.get_json()
    order_id = str(request.args.get('order_id'))
    delivery_type = data.get('delivery_type')
    delivery_cost = data.get('delivery_cost')
    if 'checkouts' not in session:
        session['checkouts']={}
    if order_id not in session['checkouts']:
        print("ERROR: order_id not foundin session")
        return {'error': 'invalid session'},403
    # Save delivery info
    session.setdefault('essentials_info', {})
    session['essentials_info'][order_id] = {
        'delivery_type': delivery_type,
        'delivery_cost': delivery_cost
    }
    print("SESSION CHECKOUT AFTER DELIVERY SAVE",session.get("checkouts"))

    # ✅ Update step_index safely without wiping session
    session['checkouts'][order_id]['step_index'] = 2
    session.modified = True
    print('updated step_index to 2:',session['checkouts'][order_id])
    session.modified = True
    return {'status': 'ok'}, 200

@checkout.route('/essentials', methods=['POST'])
def save_essentials():
    data = request.get_json()
    order_id = str(request.args.get('order_id'))
    supplies = data.get('supplies', [])

    # Save selected supplies in session
    session.setdefault('essentials_selected', {})
    session['essentials_selected'][order_id] = supplies

    # Advance step to payment
    if 'checkouts' in session and order_id in session['checkouts']:
        session['checkouts'][order_id]['step_index'] = 3
        session.modified = True
    else:
        # Fallback for missing session
        session.setdefault('checkouts', {})
        session['checkouts'][order_id] = {
            'rand': 'unknown',
            'step_index': 3,
            'start_time': datetime.now(timezone.utc).isoformat()
        }

    return jsonify({'status': 'ok'})



@checkout.route("/place_adoption", methods=["POST","GET"])

def place_adoption():
    if request.method=="POST":
        order_id=request.form.get('orderid')
        db = get_connection(True)
        try:
            # Fetch contact, delivery, essentials, and puppy info from session
            contact_info = session.get('contact_info', {}).get(order_id, {})
            delivery_info = session.get('essentials_info', {}).get(order_id, {})
            essentials = session.get('essentials_selected', {}).get(order_id, {})
            db.execute("SELECT * FROM puppy WHERE id = %s", (order_id,))
            puppy = db.fetchone()
            

            # Calculate total
            total = puppy.get('price', 0) + delivery_info.get('delivery_cost', 0)
            if essentials:
                total += sum(item.get('price', 0) for item in essentials)

            # Fetch SMTP settings
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

            # Fetch contact details from settings table
            db.execute("SELECT email, facebook_link, ig_link FROM settings LIMIT 1")
            settings = db.fetchone()
            if not settings:
                return jsonify({'success': False, 'message': 'No contact settings configured.'}), 400

            # Prepare email context
            context = {
                'contact': contact_info,
                'puppy': puppy,
                'delivery': delivery_info,
                'essentials': essentials,
                'total': total,
                
            }

            # Send email to customer and admin
            recipients = [contact_info.get('email'), settings['email']]
            try:
                send_custom_email(
                    app=current_app,
                    subject="Puppy Adoption Request Confirmation",
                    recipients=recipients,
                    template="templates.html",
                    context=context,
                    smtp_config=smtp_config
                )
               
            except Exception as e:
                
                return  render_template("thank_you.html",puppy=puppy,order=contact_info)
            # Update order status to 'confirmed' (optional, depending on your workflow)
            db.execute("UPDATE orders SET payment_status = %s WHERE id = %s", ('confirmed', order_id))

            return  render_template("thank_you.html",puppy=puppy,order=contact_info)

        except Exception as e:
            
            return  render_template("thank_you.html",puppy=puppy,order=contact_info)
        finally:
            db.close()