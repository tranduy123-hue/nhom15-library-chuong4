"""Role C (proposed): HTTP form validation and integration; AAA style."""
import http.client
import re
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode
from app import create_server


class WebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = create_server(str(Path(self.tmp.name)/'catalog.sqlite3'), port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup)
        status, html, _ = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.token = re.search('name="token" value="([^"]+)"', html).group(1)

    def cleanup(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.tmp.cleanup()

    def request(self, method, path, fields=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        body = urlencode(fields) if fields is not None else None
        headers = {'Content-Type': 'application/x-www-form-urlencoded'} if fields is not None else {}
        try:
            connection.request(method, path, body, headers)
            response = connection.getresponse()
            return response.status, response.read().decode('utf-8'), dict(response.getheaders())
        finally:
            connection.close()

    def book_fields(self, **updates):
        fields = dict(token=self.token, title='Clean Code', author='Robert C. Martin', isbn='9780132350884')
        fields.update(updates)
        return fields

    def test_add_book_redirects_and_persists_escaped_html(self):
        # Arrange
        fields = self.book_fields(title='<script>alert(1)</script>')
        # Act
        status, _, headers = self.request('POST', '/books', fields)
        _, html, _ = self.request('GET', '/')
        # Assert
        self.assertEqual(status, 303)
        self.assertEqual(headers['Location'], '/?added=1')
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)
        self.assertIn('9780132350884', html)

    def test_duplicate_isbn_preserves_form_values(self):
        # Arrange
        self.request('POST', '/books', self.book_fields())
        # Act
        status, html, _ = self.request('POST', '/books', self.book_fields(isbn='978-0-13-235088-4'))
        # Assert
        self.assertEqual(status, 422)
        self.assertIn('value="Clean Code"', html)
        self.assertIn('value="Robert C. Martin"', html)
        self.assertIn('value="978-0-13-235088-4"', html)
        self.assertIn('1 sách đã lưu', html)
        self.assertIn('role="alert"', html)

    def test_empty_title_is_rejected_by_server(self):
        # Arrange
        fields = self.book_fields(title='  ')
        # Act
        status, _, _ = self.request('POST', '/books', fields)
        # Assert
        self.assertEqual(status, 422)

    def test_fine_form_required_cases(self):
        # Arrange
        cases = [(0,'0 đ'), (5,'25.000 đ'), (10,'50.000 đ'), (11,'66.000 đ')]
        for days, expected in cases:
            with self.subTest(days=days):
                # Act
                status, html, _ = self.request('POST','/fines',dict(token=self.token, days=str(days)))
                # Assert
                self.assertEqual(status, 200)
                self.assertIn(expected, html)

    def test_invalid_fine_rejected(self):
        # Arrange
        fields = dict(token=self.token, days='1.5')
        # Act
        status, _, _ = self.request('POST', '/fines', fields)
        # Assert
        self.assertEqual(status, 422)

    def test_missing_csrf_token_rejected(self):
        # Arrange
        fields = self.book_fields(token='')
        # Act
        status, _, _ = self.request('POST', '/books', fields)
        # Assert
        self.assertEqual(status, 403)

    def test_non_ascii_csrf_token_returns_403_and_server_remains_usable(self):
        # Arrange
        fields = self.book_fields(token='é')
        # Act
        status, _, _ = self.request('POST', '/books', fields)
        get_status, _, _ = self.request('GET', '/')
        # Assert
        self.assertEqual(status, 403)
        self.assertEqual(get_status, 200)

    def test_static_routes_do_not_expose_source(self):
        # Arrange
        paths = ['/../app.py','/app.py','/library.sqlite3','/.git/config']
        for path in paths:
            with self.subTest(path=path):
                # Act
                status, _, _ = self.request('GET', path)
                # Assert
                self.assertEqual(status, 404)

    def test_favicon_endpoint_returns_204(self):
        # 1. Arrange: server đang chạy
        # 2. Act: gửi request GET /favicon.ico
        status, content, _ = self.request('GET', '/favicon.ico')
        # 3. Assert: trả về 204 No Content và nội dung rỗng
        self.assertEqual(status, 204)
        self.assertEqual(content, '')

    def test_static_stylesheet_serves_css_content_type(self):
        # 1. Arrange: server đang chạy
        # 2. Act: gửi request GET /style.css
        status, content, headers = self.request('GET', '/style.css')
        # 3. Assert: trả về 200, header Content-Type text/css và nội dung css
        self.assertEqual(status, 200)
        self.assertIn('text/css', headers.get('Content-Type', ''))
        self.assertIn('body', content)

    def test_post_book_with_whitespace_title_returns_422_with_error_message(self):
        # 1. Arrange: form có title là khoảng trắng
        fields = self.book_fields(title='    ')
        # 2. Act: gửi request POST /books
        status, html, _ = self.request('POST', '/books', fields)
        # 3. Assert: status 422 và form hiển thị thông báo lỗi
        self.assertEqual(status, 422)
        self.assertIn('Title must be a nonempty string', html)

    def test_security_headers_present_in_response(self):
        # 1. Arrange: server đang chạy
        # 2. Act: gửi request GET /
        status, _, headers = self.request('GET', '/')
        # 3. Assert: kiểm tra các header bảo mật quan trọng
        self.assertEqual(status, 200)
        self.assertIn('Content-Security-Policy', headers)
        self.assertEqual(headers.get('X-Content-Type-Options'), 'nosniff')





if __name__ == '__main__':
    unittest.main()
