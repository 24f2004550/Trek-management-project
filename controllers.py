from flask import Flask,redirect,request,render_template,url_for,flash,session,Blueprint
from sqlalchemy import text,or_,and_
from flask_login import UserMixin,LoginManager,login_user,login_required,current_user,logout_user
from werkzeug.security import generate_password_hash,check_password_hash
from models import User,Trek,Slots
from extensions import login_manager,db
import os

bp=Blueprint("main",__name__)

@login_manager.user_loader
def user(user_id):
    return User.query.get(int(user_id))

@bp.route("/",methods=["GET","POST"])
def login():
    if(request.method == "POST"):
        current_user=(db.session.execute(text("SELECT * from user where email=:e or user_name=:e"),{"e":request.form["user"]})).fetchone()
        if current_user == None:
            flash("Enter Valid Username/email",'error')
            return redirect("/")
        if not check_password_hash(current_user.password,request.form["password"]):
            flash("Enter correct password",'error')
            return redirect("/")
        if current_user.role  != request.form["role"]:
            flash("Enter correct role",'error')
            return redirect("/")
        flash("Login Successful","success")
        if(current_user.role == "staff"):
            if(current_user.status == "approved"):
                return redirect(url_for("main.staff_dashboard",id=current_user.user_id))
            else:
                return render_template("pending_approval.html")
        elif(current_user.role == "user"):
            return redirect(url_for("main.user_dashboard",id=current_user.user_id))
        else:
            return redirect("/admin")
    else:
        return render_template("login.html")


@bp.route("/register/<role>",methods=["GET","POST"])
def register_user(role):
    if (request.method == "POST"):
        current_user1=(db.session.execute(text("SELECT * from user where email=:e"),{"e":request.form["email"]})).fetchone()
        current_user2=(db.session.execute(text("SELECT * from user where phonenumber=:p or emergency_number=:e"),{"p":request.form["phone"],"e":request.form["emergency"]})).fetchone()
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
    return render_template("admin_dashboard.html")

@bp.route("/user/<int:id>")
def user_dashboard(id):
    return render_template("user_dashboard.html",id=id)

@bp.route("/staff/<int:id>")
def staff_dashboard(id):
    return render_template("staff_dashboard.html",id=id)