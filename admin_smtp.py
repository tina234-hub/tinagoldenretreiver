from flask import Blueprint, render_template, flash, jsonify, request
from db.connection import get_connection
from utils import login_required
from email_utils import send_custom_email

admin_smtp = Blueprint("admin_smtp", __name__)

@admin_smtp.route('/admin/smtp', methods=['GET', 'POST'])
@login_required
def admin_smtp1():
    settings = None
    cursor = get_connection(True)
    try:
        cursor.execute("SELECT id, smtp_server, smtp_port, email, username, password FROM smtp_settings LIMIT 1")
        result = cursor.fetchone()
        if result:
            settings = {
                'id': result['id'],
                'smtp_server': result['smtp_server'],
                'smtp_port': result['smtp_port'],
                'email': result['email'],
                'username': result['username'],
                'password': result['password']
            }
    except Exception as e:
        flash(f'Error fetching SMTP settings: {str(e)}', 'error')
    finally:
        cursor.close()

    if request.method == 'POST':
        try:
            smtp_server = request.form['smtp_server']
            smtp_port = request.form['smtp_port']
            email = request.form['email']
            username = request.form['username']
            password = request.form['password']

            if not all([smtp_server, smtp_port, email, username, password]):
                return jsonify({'success': False, 'message': 'All fields are required.'}), 400

            smtp_port = int(smtp_port)
        except KeyError as e:
            return jsonify({'success': False, 'message': f'Missing field: {str(e)}'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Port must be a valid number.'}), 400

        try:
            cursor = get_connection(True)
            cursor.execute("SELECT id FROM smtp_settings LIMIT 1")
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """
                    UPDATE smtp_settings 
                    SET smtp_server = %s, smtp_port = %s, email = %s, username = %s, password = %s
                    WHERE id = %s
                    """,
                    (smtp_server, smtp_port, email, username, password, existing['id'])
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO smtp_settings (smtp_server, smtp_port, email, username, password)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (smtp_server, smtp_port, email, username, password)
                )
           
            cursor.close()
            return jsonify({'success': True, 'message': 'SMTP settings updated successfully!'})
        except Exception as e:
            cursor.close()
            return jsonify({'success': False, 'message': f'Error updating settings: {str(e)}'}), 500

    return render_template('admin/smtp.html', settings=settings)

@admin_smtp.route('/admin/smtp/test', methods=['POST'])
@login_required
def test_smtp():
    from app import app  # Import here to avoid circular import
    cursor = get_connection(True)
    try:
        cursor.execute("SELECT * FROM smtp_settings LIMIT 1")
        smtp_row = cursor.fetchone()

        if not smtp_row:
            return jsonify({'success': False, 'message': 'No SMTP settings configured'}), 400

        smtp_config = {
            "MAIL_SERVER": smtp_row['smtp_server'],
            "MAIL_PORT": smtp_row['smtp_port'],
            "MAIL_USERNAME": smtp_row['username'],
            "MAIL_PASSWORD": smtp_row['password'],
            "MAIL_USE_TLS": smtp_row['smtp_port'] == 587,
            "MAIL_USE_SSL": smtp_row['smtp_port'] == 465,
            "MAIL_DEFAULT_SENDER": smtp_row['email']
        }

        cursor.execute("SELECT email FROM settings LIMIT 1")
        recipient_email = cursor.fetchone().get("email")

        if not recipient_email:
            return jsonify({'success': False, 'message': 'No recipient email configured in settings'}), 400

        send_custom_email(
            app=app,
            subject="SMTP Test Email",
            recipients=[recipient_email],
            body="This is a test email to confirm SMTP is working.",
            smtp_config=smtp_config
        )

        return jsonify({'success': True, 'message': f'Test email sent to {recipient_email}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()