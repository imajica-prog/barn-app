from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import cross_origin
from datetime import datetime, timedelta
import os
import base64
import json
import urllib.request
import urllib.error

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

database_url = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_PF6oH8baDmlK@ep-restless-sea-am72oev5-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=30)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Waiver page origin allowed to POST to /submit_waiver.
# "*" works for testing; once the waiver page has a permanent URL,
# replace this with that exact URL (e.g. "https://imajica.net") to lock it down.
WAIVER_ALLOWED_ORIGIN = "*"

class User(UserMixin):
    id = 1
    def get_id(self):
        return "1"

@login_manager.user_loader
def load_user(user_id):
    if user_id == "1":
        return User()
    return None

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
    category = db.Column(db.String(50))
    brand = db.Column(db.String(100))
    description = db.Column(db.String(200))
    notes = db.Column(db.String(300))

class FarrierVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horse_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    farrier = db.Column(db.String(100))
    service_type = db.Column(db.String(100))
    cost = db.Column(db.Float)
    next_due = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.String(300))
with app.app_context():
    db.create_all()

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == os.getenv("APP_USERNAME", "admin") and password == os.getenv("APP_PASSWORD", "changeme"):
            user = User()
            login_user(user, remember=True)
            return redirect("/")
        error = "Invalid username or password"
    return render_template("login.html", error=error)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/")
@login_required
def dashboard():
    today = datetime.utcnow()
    soon = today + timedelta(days=7)
    upcoming = Appointment.query.filter(
        Appointment.date >= today,
        Appointment.date <= soon
    ).order_by(Appointment.date.asc()).all()
    return render_template("dashboard.html", upcoming=upcoming)

@app.route("/horses")
@login_required
def horses():
    horses = Horse.query.order_by(Horse.name.asc()).all()
    return render_template("horses.html", horses=horses)

@app.route("/horse/<int:id>")
@login_required
def horse_detail(id):
    horse = Horse.query.get_or_404(id)
    health = HealthRecord.query.filter_by(horse_id=id).order_by(HealthRecord.date.desc()).all()
    appointments = Appointment.query.filter_by(horse_id=id).order_by(Appointment.date.desc()).all()
    records = Record.query.filter_by(horse_id=id).order_by(Record.date.desc()).all()
    return render_template("horse_detail.html", horse=horse, health=health, appointments=appointments, records=records)

@app.route("/edit_horse/<int:id>", methods=["GET", "POST"])
@login_required
def edit_horse(id):
    horse = Horse.query.get_or_404(id)
    if request.method == "POST":
        horse.name = request.form.get("name", "").strip()
        horse.breed = request.form.get("breed", "").strip()
        age_value = request.form.get("age", "").strip()
        horse.age = int(age_value) if age_value else None
        db.session.commit()
        return redirect(f"/horse/{id}")
    return render_template("edit_horse.html", horse=horse)

@app.route("/add_horse", methods=["GET", "POST"])
@login_required
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
@login_required
def add_health(horse_id):
    note = request.form.get("note", "").strip()
    if note:
        record = HealthRecord(horse_id=horse_id, note=note)
        db.session.add(record)
        db.session.commit()
    return redirect(f"/horse/{horse_id}")

@app.route("/delete_health/<int:record_id>", methods=["POST"])
@login_required
def delete_health(record_id):
    record = HealthRecord.query.get_or_404(record_id)
    horse_id = record.horse_id
    db.session.delete(record)
    db.session.commit()
    return redirect(f"/horse/{horse_id}")

@app.route("/add_appointment/<int:horse_id>", methods=["POST"])
@login_required
def add_appointment(horse_id):
    service = request.form.get("service", "").strip()
    date_text = request.form.get("date", "").strip()
    if service and date_text:
        date = datetime.strptime(date_text, "%Y-%m-%d")
        appt = Appointment(horse_id=horse_id, service=service, date=date)
        db.session.add(appt)
        db.session.commit()
    return redirect(f"/horse/{horse_id}")

@app.route("/delete_appointment/<int:appt_id>", methods=["POST"])
@login_required
def delete_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    horse_id = appt.horse_id
    db.session.delete(appt)
    db.session.commit()
    return redirect(f"/horse/{horse_id}")

@app.route("/add_record/<int:horse_id>", methods=["POST"])
@login_required
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

@app.route("/delete_record/<int:record_id>", methods=["POST"])
@login_required
def delete_record(record_id):
    record = Record.query.get_or_404(record_id)
    horse_id = record.horse_id
    db.session.delete(record)
    db.session.commit()
    return redirect(f"/horse/{horse_id}")

@app.route("/feed/<int:horse_id>")
@login_required
def feed(horse_id):
    horse = Horse.query.get_or_404(horse_id)
    profiles = FeedProfile.query.filter_by(horse_id=horse_id).order_by(FeedProfile.date.desc()).all()
    return render_template("feed.html", horse=horse, profiles=profiles)

@app.route("/add_feed/<int:horse_id>", methods=["POST"])
@login_required
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

@app.route("/delete_feed/<int:profile_id>", methods=["POST"])
@login_required
def delete_feed(profile_id):
    profile = FeedProfile.query.get_or_404(profile_id)
    horse_id = profile.horse_id
    db.session.delete(profile)
    db.session.commit()
    return redirect(f"/feed/{horse_id}")

@app.route("/tack/<int:horse_id>")
@login_required
def tack(horse_id):
    horse = Horse.query.get_or_404(horse_id)
    items = Tack.query.filter_by(horse_id=horse_id).all()
    return render_template("tack.html", horse=horse, items=items)

@app.route("/add_tack/<int:horse_id>", methods=["POST"])
@login_required
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
@login_required
def delete_tack(item_id):
    item = Tack.query.get_or_404(item_id)
    horse_id = item.horse_id
    db.session.delete(item)
    db.session.commit()
    return redirect(f"/tack/{horse_id}")

@app.route("/farrier/<int:horse_id>")
@login_required
def farrier(horse_id):
    horse = Horse.query.get_or_404(horse_id)
    visits = FarrierVisit.query.filter_by(horse_id=horse_id).order_by(FarrierVisit.date.desc()).all()
    return render_template("farrier.html", horse=horse, visits=visits)

@app.route("/add_farrier/<int:horse_id>", methods=["POST"])
@login_required
def add_farrier(horse_id):
    date_text = request.form.get("date", "").strip()
    next_due_text = request.form.get("next_due", "").strip()
    cost_text = request.form.get("cost", "").strip()
    visit = FarrierVisit(
        horse_id=horse_id,
        date=datetime.strptime(date_text, "%Y-%m-%d") if date_text else datetime.utcnow(),
        farrier=request.form.get("farrier", "").strip(),
        service_type=request.form.get("service_type", "").strip(),
        cost=float(cost_text) if cost_text else None,
        next_due=datetime.strptime(next_due_text, "%Y-%m-%d") if next_due_text else None,
        notes=request.form.get("notes", "").strip()
    )
    db.session.add(visit)
    db.session.commit()
    return redirect(f"/farrier/{horse_id}")

@app.route("/delete_farrier/<int:visit_id>", methods=["POST"])
@login_required
def delete_farrier(visit_id):
    visit = FarrierVisit.query.get_or_404(visit_id)
    horse_id = visit.horse_id
    db.session.delete(visit)
    db.session.commit()
    return redirect(f"/farrier/{horse_id}")


# ---------------------------------------------------------------------------
# Waiver submission (public, unauthenticated — this is filled out by visitors,
# not staff, so it deliberately has no @login_required)
# ---------------------------------------------------------------------------

@app.route("/submit_waiver", methods=["POST"])
@cross_origin(origins=WAIVER_ALLOWED_ORIGIN)
def submit_waiver():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "No data received"}), 400

    required = ["fullName", "address", "phone", "email", "initials", "sigDate", "signature"]
    if any(field not in data or not data[field] for field in required):
        return jsonify({"error": "Missing required fields"}), 400

    resend_key = os.environ.get("RESEND_API_KEY")
    to_email = os.environ.get("WAIVER_TO_EMAIL", "info@imajica.net")

    if not resend_key:
        return jsonify({"error": "Email is not configured on the server"}), 500

    sig_data_url = data["signature"]
    try:
        sig_b64 = sig_data_url.split(",", 1)[1]
        base64.b64decode(sig_b64)  # validate it decodes
    except Exception:
        return jsonify({"error": "Invalid signature data"}), 400

    submitted_at = data.get("submittedAt", datetime.utcnow().isoformat())

    body_text = (
        "New signed release - Imajica, LLC\n\n"
        f"Name: {data['fullName']}\n"
        f"Address: {data['address']}\n"
        f"Phone: {data['phone']}\n"
        f"Email: {data['email']}\n"
        f"Initials: {data['initials']}\n"
        f"Date signed: {data['sigDate']}\n"
        f"Submitted: {submitted_at}\n\n"
        "Signature image is attached.\n"
    )

    safe_name = data["fullName"].replace(" ", "-").lower()

    payload = {
        "from": "Imajica Waivers <onboarding@resend.dev>",
        "to": [to_email],
        "subject": f"Signed release - {data['fullName']}",
        "text": body_text,
        "attachments": [
            {
                "filename": f"signature-{safe_name}.png",
                "content": sig_b64,
            }
        ],
    }

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resend_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        app.logger.error(f"Resend rejected the waiver email ({e.code}): {detail}")
        return jsonify({"error": "Failed to send email"}), 502
    except Exception as e:
        app.logger.error(f"Failed to send waiver email: {e}")
        return jsonify({"error": "Failed to send email"}), 502

    return jsonify({"status": "sent"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
