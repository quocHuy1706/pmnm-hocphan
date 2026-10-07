from flask import Flask, abort, make_response, redirect, request, url_for
from markupsafe import escape

app = Flask(__name__)

STUDENTS = {
    "23T1020001": {"name": "Nguyễn Văn An", "lop": "K47A",
                   "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.07}},
    "23T1020002": {"name": "Trần Thị Bình", "lop": "K47A",
                   "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0}},
    "23T1020003": {"name": "Lê Hoàng Cường", "lop": "K47B",
                   "scores": {"PMMNM": 9.5, "CSDL": 9.0}},
    "23T1020004": {"name": "Phạm Minh Düng", "lop": "K47B",
                   "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0}},
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A",
                   "scores": {}},
    "23T1020006": {"name": "Võ Quốc Khánh", "lop": "K47C",
                   "scores": {"PMMNM": 7.5, "MMT": 8.0}},
}


def trang(tieu_de, noi_dung):
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{tieu_de}</title>
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand navbar-dark bg-primary mb-4">
        <div class="container">
            <a class="navbar-brand" href="{url_for('home')}">Quản lý sinh viên</a>
            <div class="navbar-nav">
                <a class="nav-link" href="{url_for('home')}">Trang chủ</a>
                <a class="nav-link" href="{url_for('student_list')}">Sinh viên</a>
            </div>
        </div>
    </nav>
    <div class="container pb-5">
        {noi_dung}
    </div>
</body>
</html>"""


def tinh_tb(scores):
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


def xep_loai(tb):
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


def badge(xl):
    """Nhãn màu cho xếp loại."""
    mau = {"Xuất sắc": "success", "Giỏi": "primary", "Khá": "info",
           "Trung bình": "warning", "Yếu": "danger"}.get(xl, "secondary")
    return f'<span class="badge text-bg-{mau}">{xl}</span>'


@app.route("/")
def home():
    total = len(STUDENTS)
    num_classes = len({sv["lop"] for sv in STUDENTS.values()})
    noi_dung = f"""
        <h1 class="mb-4">Hệ thống quản lý sinh viên</h1>
        <div class="row g-3 mb-4">
            <div class="col-md-6">
                <div class="card text-center shadow-sm">
                    <div class="card-body">
                        <div class="text-muted">Tổng số sinh viên</div>
                        <div class="display-4 fw-bold text-primary">{total}</div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card text-center shadow-sm">
                    <div class="card-body">
                        <div class="text-muted">Số lớp</div>
                        <div class="display-4 fw-bold text-success">{num_classes}</div>
                    </div>
                </div>
            </div>
        </div>
        <a class="btn btn-primary" href="{url_for('student_list')}">Danh sách sinh viên</a>
        <a class="btn btn-outline-secondary" href="{url_for('api_students')}">API sinh viên</a>
    """
    return trang("Trang chủ", noi_dung)


@app.route("/students")
def student_list():
    lop = request.args.get("lop", "")
    classes = sorted({sv["lop"] for sv in STUDENTS.values()})

    tat_ca_active = "active" if lop == "" else ""
    thanh_loc = (
        f'<a class="btn btn-outline-primary {tat_ca_active}" '
        f'href="{url_for("student_list")}">Tất cả</a>'
    )
    for l in classes:
        active = "active" if lop.lower() == l.lower() else ""
        thanh_loc += (
            f'<a class="btn btn-outline-primary {active}" '
            f'href="{url_for("student_list", lop=l)}">{l}</a>'
        )

    noi_dung = f"""
        <h1 class="mb-4">Danh sách sinh viên</h1>
        <div class="row g-3 mb-3 align-items-center">
            <div class="col-lg-6">
                <div class="btn-group" role="group">{thanh_loc}</div>
            </div>
            <div class="col-lg-6">
                <form class="input-group" action="{url_for('search')}" method="get">
                    <input type="text" class="form-control" name="q"
                           placeholder="Tìm theo tên hoặc MSSV">
                    <button class="btn btn-primary" type="submit">Tìm</button>
                </form>
            </div>
        </div>
        <p>
            <a class="btn btn-success btn-sm" href="{url_for('export_all')}">
                Tải danh sách tất cả sinh viên (CSV)
            </a>
        </p>
    """

    rows = ""
    for mssv, sv in STUDENTS.items():
        if lop and lop.lower() not in sv["lop"].lower():
            continue
        tb = tinh_tb(sv["scores"])
        tb_text = "-" if tb is None else tb
        link = url_for("student_detail", mssv=mssv)
        rows += (
            f'<tr><td><a href="{link}">{mssv}</a></td>'
            f'<td>{sv["name"]}</td><td>{sv["lop"]}</td>'
            f"<td>{tb_text}</td><td>{badge(xep_loai(tb))}</td></tr>"
        )

    if rows == "":
        noi_dung += '<div class="alert alert-warning">Không có sinh viên phù hợp</div>'
    else:
        noi_dung += (
            '<div class="card shadow-sm"><div class="table-responsive">'
            '<table class="table table-striped table-hover align-middle mb-0">'
            '<thead class="table-primary"><tr><th>MSSV</th><th>Họ tên</th>'
            "<th>Lớp</th><th>Điểm TB</th><th>Xếp loại</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div></div>"
        )
    return trang("Danh sách sinh viên", noi_dung)


@app.route("/students/<mssv>")
def student_detail(mssv):
    sv = STUDENTS.get(mssv)
    if sv is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")

    tb = tinh_tb(sv["scores"])
    tb_text = "-" if tb is None else tb
    link_lop = url_for("student_list", lop=sv["lop"])
    link_csv = url_for("export_csv", mssv=mssv)
    link_ngan = url_for("sv_redirect", mssv=mssv)

    if not sv["scores"]:
        bang_diem = '<div class="alert alert-secondary mb-0">Chưa có điểm</div>'
    else:
        dong = ""
        for mon, diem in sv["scores"].items():
            dong += f"<tr><td>{mon}</td><td>{diem}</td></tr>"
        bang_diem = (
            '<table class="table table-striped mb-0">'
            "<thead><tr><th>Học phần</th><th>Điểm</th></tr></thead>"
            f"<tbody>{dong}</tbody></table>"
        )

    noi_dung = f"""
        <h1 class="mb-4">{sv['name']}</h1>
        <div class="row g-3">
            <div class="col-md-5">
                <div class="card shadow-sm">
                    <div class="card-header fw-bold">Thông tin</div>
                    <ul class="list-group list-group-flush">
                        <li class="list-group-item"><b>MSSV:</b> {mssv}</li>
                        <li class="list-group-item"><b>Lớp:</b>
                            <a href="{link_lop}">{sv['lop']}</a></li>
                        <li class="list-group-item"><b>Điểm TB:</b> {tb_text}</li>
                        <li class="list-group-item"><b>Xếp loại:</b> {badge(xep_loai(tb))}</li>
                        <li class="list-group-item"><b>Link rút gọn:</b>
                            <a href="{link_ngan}">{link_ngan}</a></li>
                    </ul>
                </div>
            </div>
            <div class="col-md-7">
                <div class="card shadow-sm">
                    <div class="card-header fw-bold">Bảng điểm</div>
                    <div class="card-body p-0">{bang_diem}</div>
                </div>
            </div>
        </div>
        <div class="mt-3">
            <a class="btn btn-success" href="{link_csv}">Tải bảng điểm (CSV)</a>
            <a class="btn btn-outline-secondary" href="{url_for('student_list')}">Về danh sách</a>
        </div>
    """
    return trang(sv["name"], noi_dung)


@app.route("/sv/<mssv>")
def sv_redirect(mssv):
    return redirect(url_for("student_detail", mssv=mssv), code=301)


@app.route("/students/<mssv>/export")
def export_csv(mssv):
    sv = STUDENTS.get(mssv)
    if sv is None:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")

    noi_dung = "hoc_phan,diem\n"
    for mon, diem in sv["scores"].items():
        noi_dung += f"{mon},{diem}\n"

    resp = make_response(noi_dung)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = f"attachment; filename=diem_{mssv}.csv"
    return resp


@app.route("/students/export")
def export_all():
    noi_dung = "\ufeffmssv,ho_ten,lop,diem_tb,xep_loai\n"
    for mssv, sv in STUDENTS.items():
        tb = tinh_tb(sv["scores"])
        tb_text = "-" if tb is None else tb
        noi_dung += f"{mssv},{sv['name']},{sv['lop']},{tb_text},{xep_loai(tb)}\n"

    resp = make_response(noi_dung)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=danh_sach_sinh_vien.csv"
    return resp


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    q_an_toan = escape(q)

    noi_dung = f"""
        <h1 class="mb-4">Tìm kiếm sinh viên</h1>
        <form class="input-group mb-3" action="{url_for('search')}" method="get">
            <input type="text" class="form-control" name="q" value="{q_an_toan}"
                   placeholder="Tìm theo tên hoặc MSSV">
            <button class="btn btn-primary" type="submit">Tìm</button>
        </form>
    """

    if q != "":
        ket_qua = []
        for mssv, sv in STUDENTS.items():
            if q.lower() in sv["name"].lower() or q.lower() in mssv.lower():
                ket_qua.append((mssv, sv["name"]))

        noi_dung += (
            f'<div class="alert alert-info">Tìm thấy {len(ket_qua)} '
            f"kết quả cho “{q_an_toan}”</div>"
        )
        if ket_qua:
            noi_dung += '<div class="list-group shadow-sm">'
            for mssv, name in ket_qua:
                link = url_for("student_detail", mssv=mssv)
                noi_dung += (
                    f'<a class="list-group-item list-group-item-action" href="{link}">'
                    f"{name} <span class='text-muted'>({mssv})</span></a>"
                )
            noi_dung += "</div>"

    noi_dung += (
        f'<a class="btn btn-outline-secondary mt-3" '
        f'href="{url_for("student_list")}">Về danh sách</a>'
    )
    return trang("Tìm kiếm", noi_dung)


@app.route("/api/students")
def api_students():
    return STUDENTS


if __name__ == "__main__":
    app.run(debug=True)
