@app.route("/edit_health/<int:record_id>", methods=["GET", "POST"])
@login_required
def edit_health(record_id):
    record = HealthRecord.query.get_or_404(record_id)
    if request.method == "POST":
        record.note = request.form.get("note", "").strip()
        date_text = request.form.get("date", "").strip()
        if date_text:
            record.date = datetime.strptime(date_text, "%Y-%m-%d")
        db.session.commit()
        return redirect(f"/horse/{record.horse_id}")
    return render_template("edit_health.html", record=record)

@app.route("/edit_appointment/<int:appt_id>", methods=["GET", "POST"])
@login_required
def edit_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if request.method == "POST":
        appt.service = request.form.get("service", "").strip()
        date_text = request.form.get("date", "").strip()
        if date_text:
            appt.date = datetime.strptime(date_text, "%Y-%m-%d")
        db.session.commit()
        return redirect(f"/horse/{appt.horse_id}")
    return render_template("edit_appointment.html", appt=appt)

@app.route("/edit_record/<int:record_id>", methods=["GET", "POST"])
@login_required
def edit_record(record_id):
    record = Record.query.get_or_404(record_id)
    if request.method == "POST":
        record.type = request.form.get("type")
        record.title = request.form.get("title", "").strip()
        record.details = request.form.get("details", "").strip()
        date_text = request.form.get("date", "").strip()
        next_due_text = request.form.get("next_due", "").strip()
        if date_text:
            record.date = datetime.strptime(date_text, "%Y-%m-%d")
        record.next_due = datetime.strptime(next_due_text, "%Y-%m-%d") if next_due_text else None
        db.session.commit()
        return redirect(f"/horse/{record.horse_id}")
    return render_template("edit_record.html", record=record)

@app.route("/edit_feed/<int:profile_id>", methods=["GET", "POST"])
@login_required
def edit_feed(profile_id):
    profile = FeedProfile.query.get_or_404(profile_id)
    if request.method == "POST":
        profile.hay_type = request.form.get("hay_type", "").strip()
        profile.hay_amount = request.form.get("hay_amount", "").strip()
        profile.grain_type = request.form.get("grain_type", "").strip()
        profile.grain_amount = request.form.get("grain_amount", "").strip()
        profile.supplements = request.form.get("supplements", "").strip()
        profile.notes = request.form.get("notes", "").strip()
        cost_text = request.form.get("cost_per_month", "").strip()
        profile.cost_per_month = float(cost_text) if cost_text else None
        db.session.commit()
        return redirect(f"/feed/{profile.horse_id}")
    return render_template("edit_feed.html", profile=profile)

@app.route("/edit_tack/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_tack(item_id):
    item = Tack.query.get_or_404(item_id)
    if request.method == "POST":
        item.category = request.form.get("category", "").strip()
        item.brand = request.form.get("brand", "").strip()
        item.description = request.form.get("description", "").strip()
        item.notes = request.form.get("notes", "").strip()
        db.session.commit()
        return redirect(f"/tack/{item.horse_id}")
    return render_template("edit_tack.html", item=item)
