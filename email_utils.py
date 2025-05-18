from flask import render_template
from flask_mail import Mail, Message
from email_validator import validate_email, EmailNotValidError

def send_custom_email(app, subject, recipients, template=None, context={}, body=None, smtp_config={}):
    """
    Sends an email using provided SMTP config and Flask app instance.
    """
    # Validate recipient emails
    for email in recipients:
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address: {str(e)}")

    # Configure Flask app with SMTP settings
    app.config.update({
        "MAIL_SERVER": smtp_config.get("MAIL_SERVER", "smtp.example.com"),
        "MAIL_PORT": smtp_config.get("MAIL_PORT", 587),
        "MAIL_USERNAME": smtp_config.get("MAIL_USERNAME"),
        "MAIL_PASSWORD": smtp_config.get("MAIL_PASSWORD"),
        "MAIL_USE_TLS": smtp_config.get("MAIL_USE_TLS", True),
        "MAIL_USE_SSL": smtp_config.get("MAIL_USE_SSL", False),
        "MAIL_DEFAULT_SENDER": smtp_config.get("MAIL_DEFAULT_SENDER", smtp_config.get("MAIL_USERNAME")),
    })

    mail = Mail(app)
   
    with app.app_context():
        html = render_template(template, **context) if template else None
        msg = Message(subject=subject, recipients=recipients, body=body or "No message body", html=html)
        mail.send(msg)