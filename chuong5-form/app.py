from flask import Flask, render_template, request

app = Flask(__name__)


def parse_number(value):
    """Chuyển chuỗi nhập vào thành số thực, chấp nhận dấu phẩy thập phân."""
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
            ketqua = a + b
        elif operation == "tru":
            ketqua = a - b
        elif operation == "nhan":
            ketqua = a * b
        elif operation == "chia":
            if b == 0:
                return render_template("calculator.html", ketqua="Không thể chia cho 0")
            ketqua = a / b
        else:
            return render_template("calculator.html", ketqua="Phép tính không hợp lệ")

        return render_template("calculator.html", ketqua=round(ketqua, 4))
    return render_template("calculator.html")


@app.route("/diemhocphan", methods=["GET", "POST"])
def diemhocphan():
    if request.method == "POST":
        try:
            a = parse_number(request.form["a"])
            b = parse_number(request.form["b"])
            c = parse_number(request.form["c"])
        except (KeyError, ValueError):
            return render_template("diemhocphan.html", kq="Vui lòng nhập giá trị hợp lệ")

        if not all(0 <= x <= 10 for x in (a, b, c)):
            return render_template("diemhocphan.html", kq="Điểm phải nằm trong khoảng 0 đến 10")

        total = round((a + b + c) / 3, 2)

        if total >= 8.5:
            kq = "A"
        elif total >= 7.0:
            kq = "B"
        elif total >= 5.5:
            kq = "C"
        elif total >= 4.0:
            kq = "D"
        else:
            kq = "F"

        return render_template("diemhocphan.html", kq=kq, dtb=total)
    return render_template("diemhocphan.html")


@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    if request.method == "GET":
        return render_template("bmi.html")

    chieucao_raw = request.form.get("chieucao", "")
    cannang_raw = request.form.get("cannang", "")
    loi_cao = loi_nang = None
    chieucao = cannang = None

    try:
        chieucao = parse_number(chieucao_raw)
        if not (50 <= chieucao <= 250):
            loi_cao = "Giá trị phải từ 50 đến 250."
            if 0 < chieucao < 3:
                loi_cao += " (nhập mét thay vì cm)"
    except ValueError:
        loi_cao = "Vui lòng nhập một số."

    try:
        cannang = parse_number(cannang_raw)
        if not (10 <= cannang <= 300):
            loi_nang = "Giá trị phải từ 10 đến 300."
    except ValueError:
        loi_nang = "Vui lòng nhập một số."

    if loi_cao or loi_nang:
        return render_template("bmi.html", loi_cao=loi_cao, loi_nang=loi_nang,
                               chieucao=chieucao_raw, cannang=cannang_raw)

    h = chieucao / 100
    bmi_value = round(cannang / (h * h), 1)

    if bmi_value < 18.5:
        phanloai, mau = "Thiếu cân", "warning"
    elif bmi_value < 23:
        phanloai, mau = "Bình thường", "success"
    elif bmi_value < 25:
        phanloai, mau = "Thừa cân", "warning"
    else:
        phanloai, mau = "Béo phì", "danger"

    can_min = round(18.5 * h * h, 1)
    can_max = round(22.9 * h * h, 1)

    return render_template("bmi.html", bmi=bmi_value, phanloai=phanloai, mau=mau,
                           can_min=can_min, can_max=can_max,
                           chieucao=chieucao_raw, cannang=cannang_raw)


if __name__ == "__main__":
    # debug=True chỉ dùng khi phát triển; không bật khi triển khai thật.
    app.run(debug=True)
