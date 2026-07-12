from flask import Flask,redirect,request,render_template,url_for,flash,session,Blueprint
from sqlalchemy import text,or_,and_,func
from flask_login import LoginManager,login_user,login_required,current_user,logout_user
from werkzeug.security import generate_password_hash,check_password_hash
from models import User,Trek,Slots,Booking,Staff
from extensions import login_manager,db
from datetime import date,timedelta,time,datetime
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
        if login_userr.status == "blacklisted":
            return render_template("pending_approval.html",email=User.query.filter(User.role=="admin").first().email)
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
            sizes.append(size)
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
    return render_template("user_details.html",users=User.query.filter(User.role=="user").all())

@bp.route("/treks")
def treks():
    treks=Trek.query.all()
    counts={}
    for trek in treks:
        counts[trek.trek_id]=(sum(1 for slot in trek.slots if slot.status=="open"))
    return render_template("trek_details.html",treks=treks,open_slots_count=counts)

@bp.route("/staff")
def staff():
    return render_template("staff_details.html",staff=User.query.filter(User.role=="staff").all())

@bp.route("/approve/<int:id>")
def approve_staff(id):
    if(current_user.role=="admin"):
        user=User.query.filter(User.user_id==id).first()
        user.status="approved"
        db.session.commit()
        flash(f"User {user.user_id} successfully approved.","success")
        return redirect("/staff")
    else:
        return redirect("/")

@bp.route("/blacklist/<int:id>")
def blacklist(id):
    if(current_user.role=="admin"):
        user=User.query.filter(User.user_id==id).first()
        user.status="blacklisted"
        if user.treks:
            for a in user.treks:
                remove_staf_from_slot(a.staff_id,a.aslot_id)
        db.session.commit()
        flash(f"User {user.user_id} is blacklisted.","error")
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
        flash(f"User {user.user_id} successfully restored and shifted to waiting.","info")
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
        flash(f"{role} successfully deleted.","info")
        if(role=="staff"):
            return redirect("/staff")
        else:
            return redirect("/users")
    else:
        return redirect("/")

@bp.route("/profile/<int:id>")
def profile(id):
    user=User.query.filter(User.user_id==id).first()
    return render_template("profile.html",user=user)

@bp.route("/edit/profile/<int:id>",methods=["GET","POST"])
def edit_profile(id):
    user=User.query.filter(User.user_id==id).first()
    if request.method == "POST":
        u=User.query.filter(User.user_name==request.form["user_name"]).first()
        if u:
            if u.user_id != user.user_id:
                flash("Username already taken.","error")
                return render_template("edit_profile.html",user=user)
        if(request.form["phone"]==request.form["emergency"]):
            flash("Emergency phone number must be different","error")
            return render_template("edit_profile.html",user=user)
        user.user_name=request.form["user_name"]
        user.name=request.form["name"]
        user.email=request.form["email"]
        user.phonenumber=request.form["phone"]
        user.emergency_number=request.form["emergency"]
        if request.form["gender"] != "":
            user.gender=request.form["gender"]
        db.session.commit()
        flash("Profile updated successfully","success")
        return redirect(url_for("main.profile",id=user.user_id))
    else:
        return render_template("edit_profile.html",user=user)
    
@bp.route("/change/password/user/<int:id>",methods=["GET","POST"])
def change_password(id):
    user=User.query.filter(User.user_id==id).first()
    if request.method == "POST":
        if(current_user.role!="admin"):
            if not check_password_hash(user.password,request.form["old_password"]):
                flash("Enter valid Current Password","error")
                return render_template("change_password.html",user=user)
        if(request.form["new_password"] != request.form["confirm_password"]):
            flash("Confirm password must be same as New Password","error")
            return render_template("change_password.html",user=user)
        if(len(request.form["new_password"]) < 8):
            flash("New Password Length must be 8 or more","error")
            return render_template("change_password.html",user=user)
        user.password=generate_password_hash(request.form["new_password"])
        flash("Password Updated","success")
        db.session.commit()
        return redirect(url_for("main.profile",id=user.user_id))
    else:
        return render_template("change_password.html",user=user)

def bookings(limit):
    bookings=Booking.query.order_by(Booking.booking_date.desc(),Booking.booking_time.desc()).limit(limit).all()
    return bookings

def hot_treks():
    datee=date.today() - timedelta(days=7)
    bookings=db.session.query(Trek.trek_name,func.count(Booking.booking_id)).join(Slots,Trek.trek_id==Slots.trek_id).join(Booking,Booking.slot_id==Slots.slot_id).filter(Booking.booking_date>=datee).group_by(Trek.trek_name).all()
    return bookings


def create_slots(count,id):
    trek_id=id
    for i in range(count):
        new_slot=Slots(trek_id=trek_id)
        db.session.add(new_slot)
    flash("Trek's slot created Successfully","success")
    db.session.commit()

@bp.route("/create/trek",methods=["GET","POST"])
def create_trek():
    if request.method == "POST":
        if Trek.query.filter(Trek.trek_name==(request.form["name"])).first():
            flash("Trek Name already exists","error")
            return render_template("new_trek.html")
        if (int(request.form["duration"]))<=0:
            flash("Duration must be greater than zero","error")
            return render_template("new_trek.html")
        trek_name=request.form["name"]
        location=request.form["location"]
        difficulty=request.form["difficulty"]
        description=request.form["description"]
        duration=request.form["duration"]
        cost=request.form["cost"]
        report_before=request.form["report_before"]
        trek_book_start=date.fromisoformat(request.form["booking_start"])
        trek_book_end=date.fromisoformat(request.form["booking_close"])
        new_trek=Trek(trek_name=trek_name,location=location,difficulty=difficulty,description=description,duration=duration,cost=cost,report_before=report_before,trek_book_start=trek_book_start,trek_book_end=trek_book_end)
        db.session.add(new_trek)
        db.session.commit()
        flash("Trek created Successfully","success")
        id=new_trek.trek_id
        create_slots(int(request.form["slots"]),id)
        return redirect(url_for("main.trek",id=id))
    else:
        return render_template("new_trek.html")
  
@bp.route("/edit/trek/<int:id>",methods=["GET","POST"])
def edit_trek(id):
    trek=Trek.query.filter(Trek.trek_id==id).first()
    count=(sum(1 for slot in trek.slots if (slot.status not in ["completed","going"])))
    if request.method == "POST":
        trekk=Trek.query.filter(Trek.trek_name==(request.form["name"])).first()
        if trekk:
            if(trek.trek_id != trekk.trek_id):
                flash("Trek Name already exists","error")
                return render_template("edit_trek.html",trek=trek,count=count)
        trek.trek_name=request.form["name"]
        trek.location=request.form["location"]
        trek.difficulty=request.form["difficulty"]
        trek.description=request.form["description"]
        trek.duration=request.form["duration"]
        trek.cost=request.form["cost"]
        trek.report_before=request.form["report_before"]
        trek.trek_book_start=date.fromisoformat(request.form["booking_start"])
        trek.trek_book_end=date.fromisoformat(request.form["booking_close"])
        db.session.commit()
        flash("Trek edited successfully","success")
        create_slots(int(request.form["slots"])-count,id)
        return redirect(url_for("main.trek",id=id))
    else:
        return render_template("edit_trek.html",trek=trek,count=count)
    
@bp.route("/trek/<int:id>")
def trek(id):
        trek=Trek.query.filter(Trek.trek_id==id).first()
        update_statuss(id)
        db.session.commit()
        return render_template("trek.html",trek=trek)

@bp.route("/update/slot/<int:id>",methods=["GET","POST"])
def update_slot(id):
    slot=Slots.query.filter(Slots.slot_id==id).first()
    if(request.method=="POST"):
        if(int(request.form["slot_limit"])<=0):
            flash("Slot Limit must be greater than 0","error")
            return redirect(url_for("main.trek",id=slot.trek_id))
        if current_user.role=="admin":
            if(date.fromisoformat(request.form["slot_date"]) < date.today()):
                flash("Slot date cant be past","error")
                return redirect(url_for("main.trek",id=slot.trek_id))
            if(date.fromisoformat(request.form["slot_date"])==date.today() and  time.fromisoformat(request.form["slot_time"])<= datetime.now().time()):
                flash("Slot time must be in future","error")
                return redirect(url_for("main.trek",id=slot.trek_id))
            s=Slots.query.filter(and_(Slots.slot_date == date.fromisoformat(request.form["slot_date"]),Slots.slot_time == time.fromisoformat(request.form["slot_time"]),Slots.trek_id==slot.trek_id,Slots.slot_id!=slot.slot_id)).first()
            if s:
                flash("Slot already exists","error")
                return redirect(url_for("main.trek",id=slot.trek_id))
            if(date.fromisoformat(request.form["slot_date"]) < slot.treks.trek_book_start):
                flash("Choose date after trek booking starts","error")
                return redirect(url_for("main.trek",id=slot.trek_id))
            if(request.form["slot_status"] in ["open","cancelled","completed","going","opening soon"]):
                slot.status=request.form["slot_status"]
            slot.slot_date=date.fromisoformat(request.form["slot_date"])
            slot.slot_time=time.fromisoformat(request.form["slot_time"])
        else:
            if(request.form["slot_status"]!=slot.status):
                if(request.form["slot_status"] in ["completed","going"]):
                    slot.status=request.form["slot_status"]
                else:
                    flash("You can only update status to completed or going","error")
                    return render_template("update_slot.html",slot=slot)
        slot.slot_limit=int(request.form["slot_limit"])
        db.session.commit()
        update_statuss(slot.treks.trek_id)
        flash("Slot updated","success")
        if current_user.role == "admin":
            return redirect(url_for("main.trek",id=slot.trek_id))
        else:
            staff=Staff.query.join(Slots).filter(Slots.slot_id==id).first()
            return redirect(url_for("main.staff_dashboard",id=staff.staff_id))
    else:
        return render_template("update_slot.html",slot=slot)

def update_statuss(id):
    trek=Trek.query.filter(Trek.trek_id==id).first()
    for s in trek.slots:
        if s.status != "cancelled" and s.slot_date != None and s.slot_time !=None:
            if date.today() < trek.trek_book_start:
                s.status="opening soon"
            elif date.today() >= trek.trek_book_start and date.today() < s.slot_date:
                s.status="open"
            elif date.today() > (s.slot_date + timedelta(days=trek.duration)) :
                s.status="completed"
            elif (date.today() == (s.slot_date + timedelta(days=trek.duration))) and (datetime.now().time()>=s.slot_time):
                s.status="completed"
            elif (date.today() == (s.slot_date + timedelta(days=trek.duration))) and (datetime.now().time()<s.slot_time):
                s.status="going"
            elif date.today() < (s.slot_date + timedelta(days=trek.duration)):
                s.status="going"
            else:
                s.status=None
            db.session.commit()
        if s.slot_date == None or s.slot_time ==None:
            s.status=None
            db.session.commit()


@bp.route("/delete/trek/<int:id>")
def delete_trek(id):
    trek=Trek.query.filter(Trek.trek_id==id).first()
    db.session.delete(trek)
    db.session.commit()
    flash("Trek successfully deleted","info")
    return redirect(url_for("main.treks"))

@bp.route("/delete/slot/<int:id>")
def delete_slot(id):
    slot=Slots.query.filter(Slots.slot_id==id).first()
    idd=slot.trek_id
    db.session.delete(slot)
    db.session.commit()
    flash("Trek slot successfully deleted","info")
    return redirect(url_for("main.trek",id=idd))

@bp.route("/logout")
def logout():
    logout_user()
    flash("You have been successfully logged out.","success")
    return redirect(url_for("main.login"))

@bp.route("/slot/<int:id>")
def slot_info(id):
        return render_template("slot_details.html",slot=Slots.query.filter(Slots.slot_id==id).first())

def remove_staf_from_slot(staff_id,slot_id):
    staff=Staff.query.filter(and_(Staff.aslot_id==slot_id,Staff.staff_id==staff_id)).first()
    db.session.delete(staff)
    db.session.commit()
    flash("Staff removed from trek slot successfully.","success")

@bp.route("/remove/staff/<int:staff_id>/slot/<int:slot_id>",methods=["GET","POST"])
def remove_staff_from_slot(staff_id,slot_id):
    remove_staf_from_slot(staff_id,slot_id)
    return render_template("slot_details.html",slot=Slots.query.filter(Slots.slot_id==id).first())

def add_staff_to_slot(staff_id,slot_id):
    staff=Staff(staff_id=staff_id,aslot_id=slot_id)
    db.session.add(staff)

@bp.route("/assign/staff/toslot/<int:id>",methods=["GET","POST"])
def assign_staff_to_slot(id):
    slot=Slots.query.filter(Slots.slot_id==id).first()
    if request.method=="POST":
        if(request.form.getlist("staff")==[]):
            flash("No staff selected","error")
            return redirect(url_for("main.slot_info",id=slot.slot_id))
        staff_list=request.form.getlist("staff")
        for x in staff_list:
            add_staff_to_slot(int(x),slot.slot_id)
        db.session.commit()
        return redirect(url_for("main.slot_info",id=slot.slot_id))
    else:
        staff=[]
        if slot.slot_date:
            date1=slot.slot_date + timedelta(days=slot.treks.duration)
        else:
            date1=None
        for u in User.query.filter(User.role=="staff").all():
            if not u.treks:
                staff.append(u)
            else:
                eligible=False
                remove_slots=[]
                for x in u.treks:
                    if (x.trek_slot.status =="completed" or x.trek_slot.status =="opening soon"):
                       remove_slots.append(x.trek_slot.slot_id)
                       eligible=True
                    if x.trek_slot.status == "open":
                        if date1:
                            if x.trek_slot.slot_date > date1:
                                eligible=True
                            else:
                                eligible=False
                                break
                        else:
                            eligible=True
                for slot_id in remove_slots:
                    remove_staf_from_slot(u.user_id,slot_id)
                if eligible:
                    staff.append(u)
                     
        return render_template("assign_staff.html",slot=slot,staff=staff)
    

@bp.route("/user/<int:id>")
def user_dashboard(id):
    return render_template("user_dashboard.html",id=id)

@bp.route("/staff/<int:id>")
def staff_dashboard(id):
    assigned_treks=Staff.query.join(Slots).filter(and_(Staff.staff_id==id,(Slots.status not in ["completed","going"]))).all()
    completed_treks=Staff.query.join(Slots).filter(and_(Staff.staff_id==id,Slots.status=="completed")).all()
    return render_template("staff_dashboard.html",assigned_treks=assigned_treks,completed_treks=completed_treks)

@bp.route("/staff/<int:id>/assigned/treks")
def assigned_treks(id):
    treks=Staff.query.join(Slots).filter(Staff.staff_id==id).all()
    assigned_treks=Staff.query.join(Slots).filter(and_(Staff.staff_id==id,(Slots.status not in ["completed","going"]))).all()
    completed_treks=Staff.query.join(Slots).filter(and_(Staff.staff_id==id,Slots.status=="completed")).all()
    return render_template("staff_treks.html",treks=treks,x=1,assigned_treks=assigned_treks,completed_treks=completed_treks)

@bp.route("/staff/<int:id>/completed/treks")
def completed_treks(id):
    treks=Staff.query.join(Slots).filter(Staff.staff_id==id).all()
    assigned_treks=Staff.query.join(Slots).filter(and_(Staff.staff_id==id,(Slots.status not in ["completed","going"]))).all()
    completed_treks=Staff.query.join(Slots).filter(and_(Staff.staff_id==id,Slots.status=="completed")).all()
    return render_template("staff_treks.html",treks=treks,x=0,assigned_treks=assigned_treks,completed_treks=completed_treks)

@bp.route("/uppdate/slot/status/<int:id>")
def update_slot_status_to_completed(id):
    slot=Slots.query.filter(Slots.slot_id==id).first()
    if slot.slot_date!=None:
        if date.today() > slot.slot_date:
            slot.status="completed"
            db.session.commit()
        if (date.today() == slot.slot_date) and (datetime.now().time() > slot.slot_time):
            slot.status="completed"
            db.session.commit()
    return redirect(url_for("main.staff_dashboard",id=Staff.query.filter(Staff.aslot_id==id).first().staff_id))

@bp.route("/participants/<int:id>")
def participants(id):
    l=Booking.query.filter(Booking.slot_id==id).all()
    participants=[]
    for y in l:
        participants.append(User.query.filter(User.user_id==y.user_id).first())
    return render_template("trek_participants.html",users=participants,trek=Trek.query.filter(Trek.trek_id==Slots.query.filter(Slots.slot_id==id).first().trek_id).first(),slot=id)