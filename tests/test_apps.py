from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("project_app", ROOT / "app.py")
app_module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(app_module)


def csrf_token(html: bytes) -> str:
    match = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', html)
    assert match, "CSRF token was not rendered"
    return match.group(1).decode()


class AppTests(unittest.TestCase):
    def test_repository_has_one_app_file(self):
        app_files = [path for path in ROOT.rglob("app.py") if ".venv" not in path.parts]
        self.assertEqual([ROOT / "app.py"], app_files)

    def test_student_routes_keep_original_features(self):
        client = app_module.app.test_client()
        self.assertEqual(client.get("/").status_code, 200)
        filtered = client.get("/students?lop=K47A")
        self.assertEqual(filtered.status_code, 200)
        self.assertIn("23T1020001".encode(), filtered.data)
        self.assertEqual(client.get("/search?q=An").status_code, 200)
        self.assertEqual(client.get("/sv/23T1020001").status_code, 301)
        self.assertTrue(client.get("/students/23T1020001/export").headers["Content-Type"].startswith("text/csv"))
        self.assertEqual(client.get("/api/students").json["23T1020001"]["name"], "Nguyễn Văn An")
        not_found = client.get("/students/not-found")
        self.assertEqual(not_found.status_code, 404)
        self.assertIn("Không có sinh viên".encode("utf-8"), not_found.data)

    def test_library_is_a_route_group_in_same_app(self):
        client = app_module.app.test_client()
        self.assertIn("Tổng số đầu sách".encode("utf-8"), client.get("/library").data)
        web_books = client.get("/library/books?category=Web").data
        self.assertIn(b"Flask Web Development", web_books)
        self.assertNotIn("Cơ sở dữ liệu hiện đại".encode("utf-8"), web_books)
        self.assertIn(b"Web", client.get("/books/2").data)
        self.assertEqual(client.get("/api/books").json["total"], 6)
        not_found = client.get("/library/books/999")
        self.assertEqual(not_found.status_code, 404)
        self.assertIn("Không có sách".encode("utf-8"), not_found.data)

    def test_forms_auth_and_csrf_are_shared(self):
        app_module.USERS.clear()
        app_module.app.config.update(TESTING=True)
        client = app_module.app.test_client()
        register_page = client.get("/register")
        self.assertEqual(register_page.status_code, 200)
        missing_csrf = client.post("/register", data={"username": "alice", "email": "alice@example.com", "password": "password123", "confirm_password": "password123"})
        self.assertEqual(missing_csrf.status_code, 400)
        token = csrf_token(register_page.data)
        response = client.post("/register", data={"username": "alice", "email": "alice@example.com", "password": "password123", "confirm_password": "password123", "csrf_token": token})
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(app_module.USERS["alice"]["password_hash"], "password123")
        self.assertEqual(client.get("/profile").status_code, 200)
        profile_token = csrf_token(client.get("/profile").data)
        self.assertEqual(client.post("/logout", data={"csrf_token": profile_token}).status_code, 302)
        login_page = client.get("/login")
        login_token = csrf_token(login_page.data)
        self.assertEqual(client.post("/login", data={"username": "alice", "password": "password123", "csrf_token": login_token}).status_code, 302)
        self.assertEqual(client.post("/calculator", data={"a": "2", "b": "3", "operation": "cong"}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
