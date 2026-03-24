Found it! This is the problem — barn_app/app.py is a mess with the FeedProfile class stuck inside if __name__ == '__main__': and other issues. And since there's also a barn_app/Procfile, Render may be running this one.
The cleanest fix is to replace the entire contents of barn_app/app.py with the same clean version we fixed earlier. Go to barn_app/app.py, select all, delete, and paste this:
pythonfrom flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)

database_url = os.getenv("DATABASE_URL", "sqlite:///database.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Horse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horse_id = db.Column(db.Integer, nullable=False)
    service = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horse_id = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horse_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50))
    title = db.Column(db.String(100))
    details = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    next_due = db.Column(db.DateTime, nullable=True)

class FeedProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horse_id = db.Column(db.Integer, nullable=False)
    hay_type = db.Column(db.String(100))
    hay_amount = db.Column(db.String(100))
    grain_type = db.Column(db.String(100))
    grain_amount = db.Column(db.String(100))
    supplements = db.Column(db.String(300))
    notes = db.Column(db.String(300))
    cost_per_month = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)
class Tack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horse_id = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50))  # Saddle, Bridle, Blanket, Boots, Pad, Other
    brand = db.Column(db.String(100))
    description = db.Column(db.String(200))
    notes = db.Column(db.String(300))
with app.app_context():
    db.create_all()

@app.route("/")
def dashboard():
    today = datetime.utcnow()
    soon = today + timedelta(days=7)
    upcoming = Appointment.query.filter(
        Appointment.date >= today,
        Appointment.date <= soon
    ).order_by(Appointment.date.asc()).all()
    return render_template("dashboard.html", upcoming=upcoming)

@app.route("/horses")
def horses():
    horses = Horse.query.order_by(Horse.name.asc()).all()
    return render_template("horses.html", horses=horses)

@app.route("/horse/<int:id>")
def horse_detail(id):
    horse = Horse.query.get_or_404(id)
    health = HealthRecord.query.filter_by(horse_id=id).order_by(HealthRecord.date.desc()).all()
    appointments = Appointment.query.filter_by(horse_id=id).order_by(Appointment.date.desc()).all()
    records = Record.query.filter_by(horse_id=id).order_by(Record.date.desc()).all()
    return render_template(
        "horse_detail.html",
        horse=horse,
        health=health,
        appointments=appointments,
        records=records
    )

@app.route("/add_horse", methods=["GET", "POST"])
def add_horse():
    if request.method == "POST":
        age_value = request.form.get("age", "").strip()
        horse = Horse(
            name=request.form["name"].strip(),
            breed=request.form.get("breed", "").strip(),
            age=int(age_value) if age_value else None
        )
        db.session.add(horse)
        db.session.commit()
        return redirect("/horses")
    return render_template("add_horse.html")

@app.route("/add_health/<int:horse_id>", methods=["POST"])
def add_health(horse_id):
    note = request.form.get("note", "").strip()
    if note:
        record = HealthRecord(horse_id=horse_id, note=note)
        db.session.add(record)
        db.session.commit()
    return redirect(f"/horse/{horse_id}")

@app.route("/add_appointment/<int:horse_id>", methods=["POST"])
def add_appointment(horse_id):
    service = request.form.get("service", "").strip()
    date_text = request.form.get("date", "").strip()
    if service and date_text:
        date = datetime.strptime(date_text, "%Y-%m-%d")
        appt = Appointment(horse_id=horse_id, service=service, date=date)
        db.session.add(appt)
        db.session.commit()
    return redirect(f"/horse/{horse_id}")

@app.route("/add_record/<int:horse_id>", methods=["POST"])
def add_record(horse_id):
    type = request.form.get("type")
    title = request.form.get("title")
    details = request.form.get("details")
    date_text = request.form.get("date")
    next_due_text = request.form.get("next_due")
    date = datetime.strptime(date_text, "%Y-%m-%d") if date_text else datetime.utcnow()
    next_due = datetime.strptime(next_due_text, "%Y-%m-%d") if next_due_text else None
    record = Record(
        horse_id=horse_id,
        type=type,
        title=title,
        details=details,
        date=date,
        next_due=next_due
    )
    db.session.add(record)
    db.session.commit()
    return redirect(f"/horse/{horse_id}")

@app.route("/feed/<int:horse_id>")
def feed(horse_id):
    horse = Horse.query.get_or_404(horse_id)
    profiles = FeedProfile.query.filter_by(horse_id=horse_id).order_by(FeedProfile.date.desc()).all()
    return render_template("feed.html", horse=horse, profiles=profiles)

@app.route("/add_feed/<int:horse_id>", methods=["POST"])
def add_feed(horse_id):
    cost_text = request.form.get("cost_per_month", "").strip()
    profile = FeedProfile(
        horse_id=horse_id,
        hay_type=request.form.get("hay_type", "").strip(),
        hay_amount=request.form.get("hay_amount", "").strip(),
        grain_type=request.form.get("grain_type", "").strip(),
        grain_amount=request.form.get("grain_amount", "").strip(),
        supplements=request.form.get("supplements", "").strip(),
        notes=request.form.get("notes", "").strip(),
        cost_per_month=float(cost_text) if cost_text else None,
        date=datetime.utcnow()
    )
    db.session.add(profile)
    db.session.commit()
    return redirect(f"/feed/{horse_id}")
@app.route("/tack/<int:horse_id>")
def tack(horse_id):
    horse = Horse.query.get_or_404(horse_id)
    items = Tack.query.filter_by(horse_id=horse_id).all()
    return render_template("tack.html", horse=horse, items=items)

@app.route("/add_tack/<int:horse_id>", methods=["POST"])
def add_tack(horse_id):
    item = Tack(
        horse_id=horse_id,
        category=request.form.get("category", "").strip(),
        brand=request.form.get("brand", "").strip(),
        description=request.form.get("description", "").strip(),
        notes=request.form.get("notes", "").strip()
    )
    db.session.add(item)
    db.session.commit()
    return redirect(f"/tack/{horse_id}")

@app.route("/delete_tack/<int:item_id>", methods=["POST"])
def delete_tack(item_id):
    item = Tack.query.get_or_404(item_id)
    horse_id = item.horse_id
    db.session.delete(item)
    db.session.commit()
    return redirect(f"/tack/{horse_id}")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
