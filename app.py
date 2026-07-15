from flask import Flask
import os
from models import User,Trek,Staff,Slots,Booking,Review
from extensions import db,login_manager
from datetime import timedelta
from werkzeug.security import generate_password_hash

current_dir=os.path.abspath(os.path.dirname(__file__))

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(current_dir, "database.sqlite3.db")
db.init_app(app)
app.app_context().push()

from controllers  import bp
app.register_blueprint(bp)

app.config['SECRET_KEY']="HDJIDBSGJNENDNDUNRJ"
#app.config['REMEMBER-COOKIE_DURATION']=timedelta(days=15)
login_manager.init_app(app)

db.create_all()

if User.query.filter(User.role=="admin").first() is None:
    new_user=User(name="Maanya Khanna",password=generate_password_hash("12345678"),status="active",email="maanyakhanna2020@gmail.com",phonenumber="8642013579",emergency_number="9753124680",role="admin")
    db.session.add(new_user)
    db.session.commit()

if __name__=="__main__":
    app.run(debug=True)