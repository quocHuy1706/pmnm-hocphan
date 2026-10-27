from __future__ import annotations

import os
from functools import wraps
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm, CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp


BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.config.from_mapping(
    SECRET_KEY=os.environ.get("SECRET_KEY") or os.urandom(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    WTF_CSRF_TIME_LIMIT=None,
)
csrf = CSRFProtect(app)

USERS: dict[str, dict[str, str]] = {}


class RegisterForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired(), Length(min=3, max=32)])
    email = StringField("Email", validators=[DataRequired(), Regexp(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", message="Email không hợp lệ.")])
    password = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=8, message="Mật khẩu cần ít nhất 8 ký tự.")])
    confirm_password = PasswordField("Nhập lại mật khẩu", validators=[DataRequired(), EqualTo("password", message="Mật khẩu nhập lại không khớp.")])
    submit = SubmitField("Đăng ký")


class LoginForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired()])
    password = PasswordField("Mật khẩu", validators=[DataRequired()])
    remember = BooleanField("Ghi nhớ đăng nhập")
    submit = SubmitField("Đăng nhập")


def current_user():
    username = session.get("username")
    return USERS.get(username) if username else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            flash("Vui lòng đăng nhập để tiếp tục.", "warning")
            return redirect(url_for("login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user() is not None:
        return redirect(url_for("profile"))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        if username in USERS:
            form.username.errors.append("Tên đăng nhập đã tồn tại.")
        elif any(user["email"] == email for user in USERS.values()):
            form.email.errors.append("Email đã được sử dụng.")
        else:
            USERS[username] = {"username": username, "email": email, "password_hash": generate_password_hash(form.password.data)}
            session.clear()
            session["username"] = username
            flash("Đăng ký thành công.", "success")
            return redirect(url_for("profile"))
    return render_template("auth/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user() is not None:
        return redirect(url_for("profile"))
    form = LoginForm()
    if form.validate_on_submit():
        user = USERS.get(form.username.data.strip())
        if user and check_password_hash(user["password_hash"], form.password.data):
            session.clear()
            session["username"] = user["username"]
            session.permanent = form.remember.data
            flash("Đăng nhập thành công.", "success")
            next_url = request.args.get("next")
            parsed_next = urlsplit(next_url or "")
            if next_url and parsed_next.path and not parsed_next.netloc and not parsed_next.scheme:
                return redirect(next_url)
            return redirect(url_for("profile"))
        flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")
    return render_template("auth/login.html", form=form)


@app.route("/profile")
@login_required
def profile():
    return render_template("auth/profile.html")


@app.post("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("home"))


def parse_number(value: str) -> float:
    return float(value.strip().replace(",", "."))


@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    if request.method == "POST":
        try:
            a = parse_number(request.form["a"])
            b = parse_number(request.form["b"])
        except (KeyError, ValueError):
            return render_template("calculator.html", ketqua="Vui lòng nhập số hợp lệ")
        operation = request.form.get("operation")
        if operation == "cong":
            result = a + b
        elif operation == "tru":
            result = a - b
        elif operation == "nhan":
            result = a * b
        elif operation == "chia":
            if b == 0:
                return render_template("calculator.html", ketqua="Không thể chia cho 0")
            result = a / b
        else:
            return render_template("calculator.html", ketqua="Phép tính không hợp lệ")
        return render_template("calculator.html", ketqua=round(result, 4))
    return render_template("calculator.html", ketqua=None)


@app.route("/diemhocphan", methods=["GET", "POST"])
def diemhocphan():
    if request.method == "POST":
        try:
            scores = [parse_number(request.form[name]) for name in ("a", "b", "c")]
        except (KeyError, ValueError):
            return render_template("diemhocphan.html", kq="Vui lòng nhập giá trị hợp lệ")
        if not all(0 <= score <= 10 for score in scores):
            return render_template("diemhocphan.html", kq="Điểm phải nằm trong khoảng 0 đến 10")
        average = round(sum(scores) / 3, 2)
        grade = "A" if average >= 8.5 else "B" if average >= 7.0 else "C" if average >= 5.5 else "D" if average >= 4.0 else "F"
        return render_template("diemhocphan.html", kq=grade, dtb=average)
    return render_template("diemhocphan.html")


@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    if request.method == "GET":
        return render_template("bmi.html")
    height_raw, weight_raw = request.form.get("chieucao", ""), request.form.get("cannang", "")
    height_error = weight_error = None
    try:
        height = parse_number(height_raw)
        if not 50 <= height <= 250:
            height_error = "Giá trị phải từ 50 đến 250."
            if 0 < height < 3:
                height_error += " (nhập mét thay vì cm)"
    except ValueError:
        height, height_error = None, "Vui lòng nhập một số."
    try:
        weight = parse_number(weight_raw)
        if not 10 <= weight <= 300:
            weight_error = "Giá trị phải từ 10 đến 300."
    except ValueError:
        weight, weight_error = None, "Vui lòng nhập một số."
    if height_error or weight_error:
        return render_template("bmi.html", loi_cao=height_error, loi_nang=weight_error, chieucao=height_raw, cannang=weight_raw)
    bmi_value = round(weight / ((height / 100) ** 2), 1)
    if bmi_value < 18.5:
        category, color = "Thiếu cân", "warning"
    elif bmi_value < 23:
        category, color = "Bình thường", "success"
    elif bmi_value < 25:
        category, color = "Thừa cân", "warning"
    else:
        category, color = "Béo phì", "danger"
    return render_template("bmi.html", bmi=bmi_value, phanloai=category, mau=color, can_min=round(18.5 * (height / 100) ** 2, 1), can_max=round(22.9 * (height / 100) ** 2, 1), chieucao=height_raw, cannang=weight_raw)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
