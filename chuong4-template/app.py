from flask import Flask, render_template, request
from datetime import date

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about", methods=["GET", "POST"])
def about():
    name = ""
    if request.method == "POST":
        name = request.form.get("name", "")
    return render_template("about.html", name=name)


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.context_processor
def inject_globals():
    return {
        "site_name": "MiniBlog",
        "current_year": date.today().year,
    }


if __name__ == "__main__":
    app.run(debug=True)
