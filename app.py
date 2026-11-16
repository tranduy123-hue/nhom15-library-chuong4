"""Local teaching application. Run: python app.py --port 8765."""
import argparse
import hmac
import secrets
import sqlite3
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from string import Template
from urllib.parse import parse_qs, urlsplit

from library import BookService, SqliteBookRepository, FineCalculator, ValidationError, DuplicateISBNError

ROOT = Path(__file__).resolve().parent


def create_server(database='library.sqlite3', host='127.0.0.1', port=8765):
    token = secrets.token_urlsafe(32)
    repo = SqliteBookRepository(database)
    repo.initialize()
    repo.close()

    class Handler(BaseHTTPRequestHandler):
        def respond(self, body, status=200, content_type='text/html; charset=utf-8'):
            encoded = body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(encoded)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(encoded)

        def render(self, status=200, error='', values=None, fine='', days=''):
            values = values or {}
            repository = SqliteBookRepository(database)
            try:
                books = BookService(repository).list_books()
            finally:
                repository.close()
            rows = ''.join('<tr><td>'+str(book.id)+'</td><th scope="row">'+escape(book.title)+'</th><td>'+escape(book.author)+'</td><td class="isbn">'+escape(book.isbn)+'</td></tr>' for book in books)
            empty = '<p class="empty">Chưa có sách trong danh mục. Thêm cuốn sách đầu tiên bằng biểu mẫu bên cạnh.</p>' if not books else ''
            notice = '<p class="notice" role="status">Đã thêm sách vào danh mục.</p>' if parse_qs(urlsplit(self.path).query).get('added') == ['1'] else ''
            errors = '<p class="error" role="alert">'+escape(error)+'</p>' if error else ''
            html = Template((ROOT/'web'/'index.html').read_text(encoding='utf-8')).substitute(
                token=token, rows=rows, empty=empty, count=len(books), notice=notice, errors=errors,
                title=escape(values.get('title',''), quote=True), author=escape(values.get('author',''), quote=True),
                isbn=escape(values.get('isbn',''), quote=True), fine=escape(fine), days=escape(days,quote=True))
            self.respond(html, status)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/':
                self.render()
            elif path == '/style.css':
                self.respond((ROOT/'web'/'style.css').read_text(encoding='utf-8'), content_type='text/css; charset=utf-8')
            elif path == '/favicon.ico':
                self.respond('', 204)
            else:
                self.respond('Không tìm thấy trang.', 404, 'text/plain; charset=utf-8')

        def do_POST(self):
            if urlsplit(self.path).path not in ('/books', '/fines'):
                self.respond('Không tìm thấy trang.', 404)
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                self.respond('Dữ liệu không hợp lệ.', 400)
                return
            if not 0 < length <= 8192:
                self.respond('Biểu mẫu quá lớn hoặc trống.', 413)
                return
            if self.headers.get_content_type() != 'application/x-www-form-urlencoded':
                self.respond('Định dạng biểu mẫu không hợp lệ.', 415)
                return
            try:
                fields = {k: v[0] for k,v in parse_qs(self.rfile.read(length).decode('utf-8'), keep_blank_values=True, max_num_fields=10).items()}
            except (ValueError, UnicodeDecodeError):
                self.respond('Không đọc được biểu mẫu.', 400)
                return
            if not hmac.compare_digest(fields.get('token', '').encode('utf-8'), token.encode('ascii')):
                self.respond('Phiên biểu mẫu đã hết hạn. Tải lại trang để tiếp tục.', 403)
                return
            if urlsplit(self.path).path == '/fines':
                try:
                    days = int(fields.get('days',''))
                    if abs(days) > 1000000:
                        raise ValueError('out of range')
                    amount = FineCalculator().calculate(days)
                except ValueError:
                    self.render(422, error='Số ngày phải là số nguyên từ -1.000.000 đến 1.000.000.', days=fields.get('days',''))
                    return
                self.render(fine=format(amount, ',').replace(',', '.')+' đ', days=str(days))
                return
            repository = SqliteBookRepository(database)
            try:
                BookService(repository).add_book(fields.get('title',''), fields.get('author',''), fields.get('isbn',''))
            except (ValidationError, DuplicateISBNError) as exc:
                self.render(422, error=str(exc), values=fields)
                return
            except sqlite3.OperationalError:
                self.render(503, error='Danh mục đang bận. Vui lòng thử lại.', values=fields)
                return
            finally:
                repository.close()
            self.send_response(303)
            self.send_header('Location', '/?added=1')
            self.send_header('Content-Length', '0')
            self.end_headers()

    return HTTPServer((host, port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Library Sprint 1 local demo')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--database', default='library.sqlite3')
    args = parser.parse_args()
    server = create_server(args.database, port=args.port)
    print(f'Open http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
