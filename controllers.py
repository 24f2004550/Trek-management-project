from flask import Flask,redirect,request,render_template,url_for,flash,session,Blueprint
from sqlalchemy import text,or_,and_,func
from flask_login import LoginManager,login_user,login_required,current_user,logout_user
from werkzeug.security import generate_password_hash,check_password_hash
from models import User,Trek,Slots,Booking
from extensions import login_manager,db
from datetime import date,timedelta
import matplotlib.pyplot as plt
import os

bp=Blueprint("main",__name__)


@login_manager.user_loader
def user(user_id):
    return User.query.get(int(user_id))

@bp.route("/",methods=["GET","POST"])
def login():
    if(request.method == "POST"):
        login_userr=User.query.filter(or_(User.email==request.form["user"],User.user_name==request.form["user"])).first()
        if login_userr == None:
            flash("Enter Valid Username/email",'error')
            return redirect("/")
        if not check_password_hash(login_userr.password,request.form["password"]):
            flash("Enter correct password",'error')
            return redirect("/")
        if login_userr.role  != request.form["role"]:
            flash("Enter correct role",'error')
            return redirect("/")
        flash("Login Successful","success")
        login_user(login_userr)
        if(login_userr.role == "staff"):
            if(login_userr.status == "approved"):
                return redirect(url_for("main.staff_dashboard",id=login_userr.user_id))
            else:
                return render_template("pending_approval.html")
        elif(login_userr.role == "user"):
            return redirect(url_for("main.user_dashboard",id=login_userr.user_id))
        else:
            return redirect("/admin")
    else:
        return render_template("login.html")


@bp.route("/register/<role>",methods=["GET","POST"])
def register_user(role):
    if (request.method == "POST"):
        current_user1=User.query.filter(User.email==request.form["email"]).first()
        current_user2=User.query.filter(or_(User.phonenumber==request.form["phone"],User.emergency_number==request.form["phone"])).first()
        if current_user1 != None:
            flash("User already exists","warning")
        elif(request.form["password"] != request.form["confirm_password"]):
            flash("Confirm password must be same as Password","error")
        elif(len(request.form["password"]) < 8):
            flash("Password Length must be 8 or more","error")
        elif current_user2 != None:
            flash("Phone number already exists","warning")
        else:
            name=request.form["name"]
            password=generate_password_hash(request.form["password"])
            email=request.form["email"]
            phonenumber=request.form["phone"]
            emergency_number=request.form["emergency"]
            if(role=="user"):
                new_user=User(name=name,password=password,status="approved",email=email,phonenumber=phonenumber,emergency_number=emergency_number,role=role)
            else:
                new_user=User(experience=request.form["experience"],name=name,role=role,email=email,phonenumber=phonenumber,emergency_number=emergency_number,password=password)
            flash("Registration Successful","success")
            db.session.add(new_user)
            db.session.commit()
            return redirect("/")
        return render_template("register.html",role=role)
    else:
        return render_template("register.html",role=role)
    
@bp.route("/admin")
def admin_dashboard():
    labels=[]
    sizes=[]
    if(hot_treks()!=[]):
        for label,size in hot_treks():
            labels.append(label)
            sizes.append(sizes)
        plt.figure(figsize=(4,4))
        plt.pie(sizes,labels=None,startangle=90,autopct="%1.1f%%",wedgeprops={"edgecolor":"black"})
        plt.legend(labels,loc="lower center")
        plt.savefig("static/hot_trek_pie.png")
        plt.close()
    if(labels==[] or sizes==[]):
        return render_template("admin_dashboard.html",bookings=bookings(10),pie=False,Users=User.query.filter(User.role=="user").count(),Treks=Trek.query.count(),Staff=User.query.filter(User.role=="staff").count(),Bookings=Booking.query.count())
    return render_template("admin_dashboard.html",bookings=bookings(10),pie=True,Users=User.query.filter(User.role=="user").count(),Treks=Trek.query.count(),Staff=User.query.filter(User.role=="staff").count(),Bookings=Booking.query.count())

@bp.route("/users")
def users():
    return "Users"

@bp.route("/treks")
def treks():
    return "treks"

@bp.route("/staff")
def staff():
    return render_template("staff_details.html",staff=User.query.filter(User.role=="Staff").all())

@bp.route("/approve/<int:id>")
def approve_staff(id):
    if(current_user.role=="admin"):
        user=User.query.filter(User.user_id==id).first()
        user.status="approved"
        db.session.commit()
        return redirect("/staff")
    else:
        return redirect("/")

@bp.route("/blacklist/<int:id>")
def blacklist(id):
    if(current_user.role=="admin"):
        user=User.query.filter(User.user_id==id).first()
        user.status="blacklisted"
        db.session.commit()
        if(user.role=="staff"):
            return redirect("/staff")
        else:
            return redirect("/users")
    else:
        return redirect("/")
    
@bp.route("/restore/<int:id>")
def restore(id):
    if(current_user.role=="admin"):
        user=User.query.filter(User.user_id==id).first()
        user.status="waiting"
        db.session.commit()
        if(user.role=="staff"):
            return redirect("/staff")
        else:
            return redirect("/users")
    else:
        return redirect("/")
    
@bp.route("/delete/<int:id>")
def delete(id):
    if(current_user.role=="admin"):
        user=User.query.filter(User.user_id==id).first()
        role=user.role
        db.session.delete(user)
        db.session.commit()
        if(role=="staff"):
            return redirect("/staff")
        else:
            return redirect("/users")
    else:
        return redirect("/")

@bp.route("/profile")
def profile():
    return "admin profile"


def bookings(limit):
    bookings=Booking.query.order_by(Booking.booking_date.desc(),Booking.booking_time.desc()).limit(limit).all()
    return bookings

def hot_treks():
    datee=date.today() - timedelta(days=7)
    bookings=db.session.query(Trek.trek_name,func.count(Booking.booking_id)).join(Slots,Trek.trek_id==Slots.trek_id).join(Booking,Booking.slot_id==Slots.slot_id).filter(Booking.booking_date>=datee).group_by(Trek.trek_name).all()
    return bookings

@bp.route("/logout")
def logout():
    logout_user()
    flash("You have been successfully logged out.","success")
    return redirect(url_for("main.login"))

@bp.route("/user/<int:id>")
def user_dashboard(id):
    return render_template("user_dashboard.html",id=id)

@bp.route("/staff/<int:id>")
def staff_dashboard(id):
    return render_template("staff_dashboard.html",id=id)