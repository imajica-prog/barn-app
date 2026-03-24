from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Horse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horse_id = db.Column(db.Integer)
    service = db.Column(db.String(100))
    date = db.Column(db.DateTime)

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horse_id = db.Column(db.Integer)
    note = db.Column(db.String(200))
    date = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def dashboard():
    today = datetime.utcnow()
    soon = today + timedelta(days=7)
    upcoming = Appointment.query.filter(Appointment.date >= today, Appointment.date <= soon).all()
    return render_template('dashboard.html', upcoming=upcoming)

@app.route('/horses')
def horses():
    horses = Horse.query.all()
    return render_template('horses.html', horses=horses)

@app.route('/horse/<int:id>')
def horse_detail(id):
    horse = Horse.query.get_or_404(id)
    health = HealthRecord.query.filter_by(horse_id=id).all()
    appointments = Appointment.query.filter_by(horse_id=id).all()
    return render_template('horse_detail.html', horse=horse, health=health, appointments=appointments)

@app.route('/add_horse', methods=['GET', 'POST'])
def add_horse():
    if request.method == 'POST':
        horse = Horse(name=request.form['name'], breed=request.form['breed'], age=request.form['age'])
        db.session.add(horse)
        db.session.commit()
        return redirect('/horses')
    return render_template('add_horse.html')

@app.route('/add_health/<int:horse_id>', methods=['POST'])
def add_health(horse_id):
    record = HealthRecord(horse_id=horse_id, note=request.form['note'])
    db.session.add(record)
    db.session.commit()
    return redirect(f'/horse/{horse_id}')

@app.route('/add_appointment/<int:horse_id>', methods=['POST'])
def add_appointment(horse_id):
    date = datetime.strptime(request.form['date'], "%Y-%m-%d")
    appt = Appointment(horse_id=horse_id, service=request.form['service'], date=date)
    db.session.add(appt)
    db.session.commit()
    return redirect(f'/horse/{horse_id}')

if __name__ == '__main__':
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
    date = db.Column(db.DateTime, default=datetime.utcnow) with app.app_context():
        db.create_all()
    app.run(debug=True)
