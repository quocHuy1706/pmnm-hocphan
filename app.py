from __future__ import annotations

import csv
import io
import os
from datetime import date
from functools import wraps
from urllib.parse import urlsplit

from flask import Flask, abort, flash, make_response, redirect, render_template, request, session, url_for
from flask_wtf import FlaskForm, CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp


app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY=os.environ.get("SECRET_KEY") or os.urandom(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
    WTF_CSRF_TIME_LIMIT=None,
    SITE_NAME="PMMNM · Bài tập Flask",
)
csrf = CSRFProtect(app)


STUDENTS = {
    "23T1020001": {"name": "Nguyễn Văn An", "lop": "K47A", "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.07}},
    "23T1020002": {"name": "Trần Thị Bình", "lop": "K47A", "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0}},
    "23T1020003": {"name": "Lê Hoàng Cường", "lop": "K47B", "scores": {"PMMNM": 9.5, "CSDL": 9.0}},
    "23T1020004": {"name": "Phạm Minh Dũng", "lop": "K47B", "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0}},
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A", "scores": {}},
    "23T1020006": {"name": "Võ Quốc Khánh", "lop": "K47C", "scores": {"PMMNM": 7.5, "MMT": 8.0}},
}

BOOKS = [
    {"id": 1, "title": "Lập trình Python căn bản", "author": "Nguyễn Văn A", "category": "Lập trình", "year": 2024, "available": True, "description": "Nhập môn Python qua các ví dụ thực hành và bài tập nhỏ."},
    {"id": 2, "title": "Flask Web Development", "author": "Miguel Grinberg", "category": "Web", "year": 2023, "available": True, "description": "Xây dựng ứng dụng web Flask theo hướng thực tế."},
    {"id": 3, "title": "Cơ sở dữ liệu hiện đại", "author": "Trần Minh Đức", "category": "Cơ sở dữ liệu", "year": 2022, "available": False, "description": "Các khái niệm cốt lõi về mô hình hóa và truy vấn dữ liệu."},
    {"id": 4, "title": "Thiết kế giao diện Bootstrap", "author": "Lê Thu Hà", "category": "Web", "year": 2025, "available": True, "description": "Thiết kế giao diện responsive với Bootstrap 5."},
    {"id": 5, "title": "Clean Code", "author": "Robert C. Martin", "category": "Kỹ nghệ phần mềm", "year": 2021, "available": False, "description": "Những nguyên tắc giúp mã nguồn dễ đọc, kiểm thử và bảo trì."},
    {"id": 6, "title": "Nhập môn Git", "author": "Phạm Quốc Huy", "category": "Công cụ", "year": 2025, "available": True, "description": "Quản lý phiên bản và cộng tác hiệu quả với Git."},
]

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


def tinh_tb(scores: dict[str, float]) -> float | None:
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


def xep_loai(tb: float | None) -> str:
    if tb is None:
        return "-"
    if tb >= 9:
        return "Xuất sắc"
    if tb >= 8:
        return "Giỏi"
    if tb >= 6.5:
        return "Khá"
    if tb >= 5:
        return "Trung bình"
    return "Yếu"


def parse_number(value: str) -> float:
    return float(value.strip().replace(",", "."))


@app.context_processor
def inject_globals():
    return {
        "current_year": date.today().year,
        "site_name": app.config["SITE_NAME"],
        "current_user": current_user(),
        "categories": sorted({book["category"] for book in BOOKS}),
    }


@app.route("/")
def home():
    return render_template(
        "dashboard.html",
        total=len(STUDENTS),
        num_classes=len({student["lop"] for student in STUDENTS.values()}),
    )


# Chương 3: danh sách sinh viên, tìm kiếm, CSV và API.
@app.route("/students")
def student_list():
    selected_class = request.args.get("lop", "").strip()
    students = [
        {"mssv": mssv, **student, "average": tinh_tb(student["scores"]), "classification": xep_loai(tinh_tb(student["scores"]))}
        for mssv, student in STUDENTS.items()
        if not selected_class or selected_class.casefold() in student["lop"].casefold()
    ]
    classes = sorted({student["lop"] for student in STUDENTS.values()})
    return render_template("students/list.html", students=students, classes=classes, selected_class=selected_class)


@app.route("/students/<mssv>")
def student_detail(mssv):
    student = STUDENTS.get(mssv)
    if student is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    average = tinh_tb(student["scores"])
    return render_template("students/detail.html", mssv=mssv, student=student, average=average, classification=xep_loai(average))


@app.route("/sv/<mssv>")
def sv_redirect(mssv):
    return redirect(url_for("student_detail", mssv=mssv), code=301)


@app.route("/students/<mssv>/export")
def export_csv(mssv):
    student = STUDENTS.get(mssv)
    if student is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["hoc_phan", "diem"])
    writer.writerows(student["scores"].items())
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=diem_{mssv}.csv"
    return response


@app.route("/students/export")
def export_all():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["mssv", "ho_ten", "lop", "diem_tb", "xep_loai"])
    for mssv, student in STUDENTS.items():
        average = tinh_tb(student["scores"])
        writer.writerow([mssv, student["name"], student["lop"], average if average is not None else "-", xep_loai(average)])
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=danh_sach_sinh_vien.csv"
    return response


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    results = []
    if query:
        lowered = query.casefold()
        results = [{"mssv": mssv, "name": student["name"]} for mssv, student in STUDENTS.items() if lowered in student["name"].casefold() or lowered in mssv.casefold()]
    return render_template("students/search.html", query=query, results=results)


@app.route("/api/students")
def api_students():
    return STUDENTS


# Chương 4: LibraryMS v0.2 trong cùng app, dưới /library.
@app.route("/library")
def library_home():
    recent_books = sorted(BOOKS, key=lambda book: book["year"], reverse=True)[:3]
    return render_template("library/home.html", total_books=len(BOOKS), available_books=sum(book["available"] for book in BOOKS), recent_books=recent_books)


@app.route("/library/books")
@app.route("/books")
def book_list():
    selected_category = request.args.get("category", "").strip()
    books = [book for book in BOOKS if not selected_category or book["category"].casefold() == selected_category.casefold()]
    return render_template("library/books/list.html", books=books, selected_category=selected_category)


@app.route("/library/books/<int:book_id>")
@app.route("/books/<int:book_id>")
def book_detail(book_id):
    book = next((item for item in BOOKS if item["id"] == book_id), None)
    if book is None:
        abort(404, description=f"Không có sách với mã = {book_id}.")
    return render_template("library/books/detail.html", book=book)


@app.route("/api/books")
def api_books():
    return {"books": BOOKS, "total": len(BOOKS)}


@app.route("/library/about", methods=["GET", "POST"])
@app.route("/about", methods=["GET", "POST"])
def about():
    name = request.form.get("name", "") if request.method == "POST" else ""
    return render_template("library/about.html", name=name)


@app.route("/library/contact")
@app.route("/contact")
def contact():
    return render_template("library/contact.html")


# Chương 5: forms, xác thực và các bài tính trong cùng app.
@app.route("/forms")
def forms_home():
    return render_template("forms/home.html")


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
    return render_template("forms/auth/register.html", form=form)


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
    return render_template("forms/auth/login.html", form=form)


@app.route("/profile")
@login_required
def profile():
    return render_template("forms/auth/profile.html")


@app.post("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("home"))


@app.route("/forms/calculator", methods=["GET", "POST"])
@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    if request.method == "POST":
        try:
            a = parse_number(request.form["a"])
            b = parse_number(request.form["b"])
        except (KeyError, ValueError):
            return render_template("forms/calculator.html", ketqua="Vui lòng nhập số hợp lệ")
        operation = request.form.get("operation")
        if operation == "cong":
            result = a + b
        elif operation == "tru":
            result = a - b
        elif operation == "nhan":
            result = a * b
        elif operation == "chia":
            if b == 0:
                return render_template("forms/calculator.html", ketqua="Không thể chia cho 0")
            result = a / b
        else:
            return render_template("forms/calculator.html", ketqua="Phép tính không hợp lệ")
        return render_template("forms/calculator.html", ketqua=round(result, 4))
    return render_template("forms/calculator.html", ketqua=None)


@app.route("/forms/diemhocphan", methods=["GET", "POST"])
@app.route("/diemhocphan", methods=["GET", "POST"])
def diemhocphan():
    if request.method == "POST":
        try:
            scores = [parse_number(request.form[name]) for name in ("a", "b", "c")]
        except (KeyError, ValueError):
            return render_template("forms/diemhocphan.html", kq="Vui lòng nhập giá trị hợp lệ")
        if not all(0 <= score <= 10 for score in scores):
            return render_template("forms/diemhocphan.html", kq="Điểm phải nằm trong khoảng 0 đến 10")
        average = round(sum(scores) / 3, 2)
        grade = "A" if average >= 8.5 else "B" if average >= 7.0 else "C" if average >= 5.5 else "D" if average >= 4.0 else "F"
        return render_template("forms/diemhocphan.html", kq=grade, dtb=average)
    return render_template("forms/diemhocphan.html")


@app.route("/forms/bmi", methods=["GET", "POST"])
@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    if request.method == "GET":
        return render_template("forms/bmi.html")
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
        return render_template("forms/bmi.html", loi_cao=height_error, loi_nang=weight_error, chieucao=height_raw, cannang=weight_raw)
    bmi_value = round(weight / ((height / 100) ** 2), 1)
    if bmi_value < 18.5:
        category, color = "Thiếu cân", "warning"
    elif bmi_value < 23:
        category, color = "Bình thường", "success"
    elif bmi_value < 25:
        category, color = "Thừa cân", "warning"
    else:
        category, color = "Béo phì", "danger"
    return render_template("forms/bmi.html", bmi=bmi_value, phanloai=category, mau=color, can_min=round(18.5 * (height / 100) ** 2, 1), can_max=round(22.9 * (height / 100) ** 2, 1), chieucao=height_raw, cannang=weight_raw)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", error=error), 404


if __name__ == "__main__":
    app.run(debug=True)
