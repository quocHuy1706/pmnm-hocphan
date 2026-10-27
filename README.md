# pmnm-hocphan

Repository bài thực hành Flask cho các chương 3–5. Các app dùng Bootstrap 5 và có thể chạy độc lập.

## Chạy nhanh

Tạo môi trường ảo rồi cài thư viện:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

App dashboard + chương 3:

```powershell
flask --app app run --debug
```

Mở `http://127.0.0.1:5000`. Dashboard liên kết tới hai app độc lập ở cổng 5001 và 5002.

LibraryMS v0.2 (chương 4):

```powershell
cd chuong4-template
flask --app app run --debug --port 5001
```

Forms, xác thực và các bài tính (chương 5):

```powershell
cd chuong5-form
$env:SECRET_KEY = "thay-bang-chuoi-bi-mat-dai"
flask --app app run --debug --port 5002
```

## Nội dung đã triển khai

- App gốc có dashboard Bootstrap công khai và chuyển toàn bộ chương 3 sang Jinja templates, giữ các URL `/students`, `/search`, CSV, redirect `/sv/<mssv>` và `/api/students`; không còn HTML ghép trong `app.py` hay dùng `escape()`.
- `chuong4-template` là LibraryMS v0.2 độc lập: `base.html`, macro `book_card`/`status_badge`, context processor thể loại, lọc responsive, chi tiết sách, 404 có mô tả và `/api/books`.
- `chuong5-form` dùng Flask-WTF với CSRF toàn cục, đăng ký/đăng nhập/hồ sơ/đăng xuất, mật khẩu băm bằng Werkzeug và dictionary trong bộ nhớ. Các form calculator/BMI/điểm học phần cũ được giữ lại và bổ sung CSRF.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

Test kiểm tra dashboard, chức năng chương 3, lọc/API/404 của LibraryMS và luồng xác thực cùng CSRF.

## Git

Đã tạo commit cục bộ và tag `v0.2` theo yêu cầu bài tập. Chưa push lên GitHub.
