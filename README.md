# pmnm-hocphan

Một Flask app duy nhất cho các bài thực hành chương 3–5. Mọi chức năng chạy từ `app.py` ở thư mục gốc; các chương được phân biệt bằng đường dẫn.

## Chạy

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app run --debug
```

Mở `http://127.0.0.1:5000` để xem dashboard.

## Các đường dẫn chính

- `/` — dashboard chung.
- `/students`, `/search`, `/api/students` — chương 3: danh sách, lọc, tìm kiếm, CSV, chi tiết và API.
- `/library`, `/library/books`, `/api/books` — chương 4: LibraryMS v0.2; `/books` vẫn được giữ làm alias ngắn.
- `/forms` — dashboard chương 5; `/register`, `/login`, `/profile`, `/logout` — xác thực dùng chung.
- `/calculator`, `/diemhocphan`, `/bmi` — các bài form chương 5; mỗi POST đều có CSRF.

Chương 4 vẫn giữ các đường dẫn cũ `/about` và `/contact`.

## Cấu hình bảo mật

Đặt `SECRET_KEY` khi chạy lâu dài hoặc triển khai thật:

```powershell
$env:SECRET_KEY = "thay-bang-chuoi-bi-mat-dai"
flask --app app run
```

Mật khẩu được băm bằng Werkzeug; người dùng được lưu trong dictionary bộ nhớ nên sẽ mất khi khởi động lại app.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

## Git

Đã tạo commit cục bộ và tag `v0.2`; chưa push lên GitHub.
