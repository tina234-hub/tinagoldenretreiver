from flask_mail import Mail
from flask import Flask
mail = Mail()

def create_app():
    app = Flask(__name__)
    # Do NOT configure MAIL_ settings statically here if you're loading them from DB
    mail.init_app(app)
    return app
