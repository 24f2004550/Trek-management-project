from extensions import db
from datetime import date,time


class User(db.Model):
    __tablename__='user'
    user_id =db.Column(db.Integer,primary_key=True,autoincrement=True)
    user_name=db.Column(db.String)
    password=db.Column(db.String,nullable=False)
    name =db.Column(db.String,nullable=False)
    phonenumber =db.Column(db.String(10),unique=True)
    email =db.Column(db.String,nullable=False,unique=True)
    status =db.Column(db.String,default="waiting") #blacklist,waiting,approved
    gender =db.Column(db.String)
    emergency_number =db.Column(db.String(10))
    role=db.Column(db.String,nullable=False)
    experience=db.Column(db.String,default="NA")
    treks=db.relationship("Staff",back_populates="user")
    bookings=db.relationship("Booking",back_populates="user")

#this treks here i.e usser.trek give list of objects of staff class where usser is object of above User class

class Trek(db.Model):
    __tablename__='trek'
    trek_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    trek_name=db.Column(db.String,nullable=False)
    location=db.Column(db.String,nullable=False)
    difficulty=db.Column(db.String,nullable=False)
    description=db.Column(db.String)
    trek_book_start=db.Column(db.Date)
    trek_book_end=db.Column(db.Date)
    duration=db.Column(db.Integer) #in days
    cost=db.Column(db.Integer) #its cost per person in rupees
    report_before=db.Column(db.Integer) # report before trek in hrs for guidelines
    slots=db.relationship("Slots",back_populates="treks")

class Staff(db.Model):
    __tablename__='staff_assigned_totrek'
    association_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    aslot_id=db.Column(db.Integer,db.ForeignKey("slots.slot_id"))
    staff_id=db.Column(db.Integer,db.ForeignKey("user.user_id"))
    trek_slot=db.relationship("Slots",back_populates="slotstaff")
    user=db.relationship("User",back_populates="treks")

class Slots(db.Model):
    __tablename__="slots"
    slot_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    trek_id=db.Column(db.Integer,db.ForeignKey("trek.trek_id"))
    slot_date=db.Column(db.Date)
    slot_time=db.Column(db.Time) #assigning values ==>> trek.start_time = time(8, 30,45)  gives ==>> 08:30:45
    slot_limit=db.Column(db.Integer)
    status=db.Column(db.String) # completed,going,open
    treks=db.relationship("Trek",back_populates="slots")
    slotstaff=db.relationship("Staff",back_populates="trek_slot")
    bookings=db.relationship("Booking",back_populates="slot")

class Booking(db.Model):
    __tablename__="bookings"
    booking_id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("user.user_id"))
    slot_id=db.Column(db.Integer,db.ForeignKey("slots.slot_id"))
    booking_date=db.Column(db.Date)
    booking_time=db.Column(db.Time)
    status=db.Column(db.String) #booked,cancelled,completed
    user=db.relationship("User",back_populates="bookings")
    slot=db.relationship("Slots",back_populates="bookings")
    reviews=db.relationship("Review",back_populates="booking")

class Review(db.Model):
    __tablename__="reviews"
    review_id=db.Column(db.Integer,primary_key=True)
    booking_id=db.Column(db.Integer,db.ForeignKey("bookings.booking_id"))
    review_date=db.Column(db.Date)
    review_time=db.Column(db.Time)
    review_description=db.Column(db.String)
    booking=db.relationship("Booking",back_populates="reviews")