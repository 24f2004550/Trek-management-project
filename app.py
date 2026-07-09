from flask import Flask
import os
from models import User,Trek,Staff,Slots,Booking,Review
from extensions import db,login_manager
from datetime import timedelta

current_dir=os.path.abspath(os.path.dirname(__file__))

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(current_dir, "database.sqlite3.db")
db.init_app(app)
app.app_context().push()

from controllers  import bp
app.register_blueprint(bp)

app.config['SECRET_KEY']="HDJIDBSGJNENDNDUNRJ"
app.config['REMEMBER-COOKIE_DURATION']=timedelta(days=15)
login_manager.init_app(app)

db.create_all()

if __name__=="__main__":
    app.run(debug=True)