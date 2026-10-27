from __future__ import annotations

from datetime import date
from pathlib import Path

from flask import Flask, abort, render_template, request


BASE_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.config.from_mapping(SITE_NAME="LibraryMS")

BOOKS = [
    {"id": 1, "title": "Lập trình Python căn bản", "author": "Nguyễn Văn A", "category": "Lập trình", "year": 2024, "available": True, "description": "Nhập môn Python qua các ví dụ thực hành và bài tập nhỏ."},
    {"id": 2, "title": "Flask Web Development", "author": "Miguel Grinberg", "category": "Web", "year": 2023, "available": True, "description": "Xây dựng ứng dụng web Flask theo hướng thực tế."},
    {"id": 3, "title": "Cơ sở dữ liệu hiện đại", "author": "Trần Minh Đức", "category": "Cơ sở dữ liệu", "year": 2022, "available": False, "description": "Các khái niệm cốt lõi về mô hình hóa và truy vấn dữ liệu."},
    {"id": 4, "title": "Thiết kế giao diện Bootstrap", "author": "Lê Thu Hà", "category": "Web", "year": 2025, "available": True, "description": "Thiết kế giao diện responsive với Bootstrap 5."},
    {"id": 5, "title": "Clean Code", "author": "Robert C. Martin", "category": "Kỹ nghệ phần mềm", "year": 2021, "available": False, "description": "Những nguyên tắc giúp mã nguồn dễ đọc, kiểm thử và bảo trì."},
    {"id": 6, "title": "Nhập môn Git", "author": "Phạm Quốc Huy", "category": "Công cụ", "year": 2025, "available": True, "description": "Quản lý phiên bản và cộng tác hiệu quả với Git."},
]


@app.context_processor
def inject_globals():
    return {
        "site_name": app.config["SITE_NAME"],
        "current_year": date.today().year,
        "categories": sorted({book["category"] for book in BOOKS}),
    }


@app.route("/")
def home():
    recent_books = sorted(BOOKS, key=lambda book: book["year"], reverse=True)[:3]
    return render_template(
        "home.html",
        total_books=len(BOOKS),
        available_books=sum(book["available"] for book in BOOKS),
        recent_books=recent_books,
    )


@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template("about.html", name=request.form.get("name", "") if request.method == "POST" else "")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/books")
def book_list():
    selected_category = request.args.get("category", "").strip()
    books = [book for book in BOOKS if not selected_category or book["category"].casefold() == selected_category.casefold()]
    return render_template("books/list.html", books=books, selected_category=selected_category)


@app.route("/books/<int:book_id>")
def book_detail(book_id):
    book = next((item for item in BOOKS if item["id"] == book_id), None)
    if book is None:
        abort(404, description=f"Không có sách với mã = {book_id}.")
    return render_template("books/detail.html", book=book)


@app.route("/api/books")
def api_books():
    return {"books": BOOKS, "total": len(BOOKS)}


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html", error=error), 404


if __name__ == "__main__":
    app.run(debug=True, port=5001)
