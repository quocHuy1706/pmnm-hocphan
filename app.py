from __future__ import annotations

import csv
import io
from datetime import date

from flask import Flask, abort, make_response, redirect, render_template, request, url_for


app = Flask(__name__)
app.config.from_mapping(
    CHUONG4_URL="http://127.0.0.1:5001",
    CHUONG5_URL="http://127.0.0.1:5002",
)


STUDENTS = {
    "23T1020001": {"name": "Nguyễn Văn An", "lop": "K47A", "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.07}},
    "23T1020002": {"name": "Trần Thị Bình", "lop": "K47A", "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0}},
    "23T1020003": {"name": "Lê Hoàng Cường", "lop": "K47B", "scores": {"PMMNM": 9.5, "CSDL": 9.0}},
    "23T1020004": {"name": "Phạm Minh Dũng", "lop": "K47B", "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0}},
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A", "scores": {}},
    "23T1020006": {"name": "Võ Quốc Khánh", "lop": "K47C", "scores": {"PMMNM": 7.5, "MMT": 8.0}},
}


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


@app.context_processor
def inject_globals():
    return {
        "current_year": date.today().year,
        "chapter4_url": app.config["CHUONG4_URL"],
        "chapter5_url": app.config["CHUONG5_URL"],
    }


@app.route("/")
def home():
    return render_template(
        "dashboard.html",
        total=len(STUDENTS),
        num_classes=len({student["lop"] for student in STUDENTS.values()}),
    )


@app.route("/students")
def student_list():
    selected_class = request.args.get("lop", "").strip()
    students = [
        {"mssv": mssv, **student, "average": tinh_tb(student["scores"]), "classification": xep_loai(tinh_tb(student["scores"]))}
        for mssv, student in STUDENTS.items()
        if not selected_class or selected_class.lower() in student["lop"].lower()
    ]
    classes = sorted({student["lop"] for student in STUDENTS.values()})
    return render_template("students/list.html", students=students, classes=classes, selected_class=selected_class)


@app.route("/students/<mssv>")
def student_detail(mssv):
    student = STUDENTS.get(mssv)
    if student is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    average = tinh_tb(student["scores"])
    return render_template(
        "students/detail.html",
        mssv=mssv,
        student=student,
        average=average,
        classification=xep_loai(average),
    )


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
        results = [
            {"mssv": mssv, "name": student["name"]}
            for mssv, student in STUDENTS.items()
            if lowered in student["name"].casefold() or lowered in mssv.casefold()
        ]
    return render_template("students/search.html", query=query, results=results)


@app.route("/api/students")
def api_students():
    return STUDENTS


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", error=error), 404


if __name__ == "__main__":
    app.run(debug=True)
