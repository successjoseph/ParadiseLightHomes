from flask import Flask, render_template, request, redirect, url_for, flash, session
import json

app = Flask(__name__)
app.secret_key = "supersecret"

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name")
    email = request.form.get("email")
    message = request.form.get("message")
    # TODO: save to DB or send email
    flash("Thanks for reaching out! We'll get back to you soon.", "success")
    return redirect(url_for("index") + "#contact")

@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email")
    # TODO: save subscriber to DB or mailing list
    flash("You're now subscribed to our newsletter!", "success")
    return redirect(url_for("index") + "#footer")


@app.route("/verifier", methods=["GET", "POST"])
def verifier():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        with open("static/data/verifier.json") as f:
            data = json.load(f)

        roles = ["techies", "admins", "editors"]
        for role in roles:
            for user in data.get(role, []):
                if user.get("email") == email and user.get("password") == password:
                    # Save login + role
                    session["user"] = user.get("user")
                    session["role"] = role
                    return redirect(url_for("settings"))

        flash("Invalid email or password")
        return redirect(url_for("verifier"))

    return render_template("verifier.html")


@app.route("/settings", methods=["GET", "POST"])
def settings():
    role = session.get("role")
    if not role:
        flash("You must log in first.")
        return redirect(url_for("verifier"))

    # Load data
    with open("static/data/verifier.json") as f:
        verifier_data = json.load(f)

    with open("static/data/posts.json") as f:
        posts_data = json.load(f)

    return render_template(
        "settings.html",
        role=role,
        user=session.get("user"),
        verifier_data=verifier_data,
        posts_data=posts_data
    )

@app.route("/manage/users/<section>")
def manage_users(section):
    role = session.get("role")
    if not role:
        return redirect(url_for("verifier"))

    # only admins can manage everyone
    if role == "admins" or (role == section):
        with open("static/data/verifier.json") as f:
            data = json.load(f)
        users = data.get(section, [])
        return render_template("manage_users.html", users=users, section=section)
    else:
        flash("Not authorized")
        return redirect(url_for("settings"))

@app.route("/manage/posts")
def manage_posts():
    role = session.get("role")
    if not role:
        return redirect(url_for("verifier"))

    if role in ["admins", "editors"]:
        with open("static/data/posts.json") as f:
            data = json.load(f)
        return render_template("manage_posts.html", posts=data.get("projects", []) + data.get("blog", []))
    else:
        flash("Not authorized")
        return redirect(url_for("settings"))

@app.route("/logout")
def logout():
    session.clear()  # wipe all stored user/session data
    flash("You have been logged out.", "info")
    return redirect(url_for("verifier"))



if __name__ == "__main__":
    app.run(debug=True)
