# Nhóm 15 — Hệ thống Quản lý Thư viện

Bài thực hành Chương 4: Phát triển, Tích hợp và Đảm bảo chất lượng.

Trạng thái tích hợp: backend, form HTML và kiểm thử AAA/HTTP đã tích hợp.

- Jira: https://duygk45.atlassian.net/jira/software/projects/KAN/boards/1
- GitHub: https://github.com/tranduy123-hue/nhom15-library-chuong4

User Story: Là thủ thư, tôi muốn thêm sách mới vào hệ thống để quản lý tài sản thư viện.

## Chạy ứng dụng

Python 3.11 hoặc 3.12; chỉ dùng thư viện chuẩn, không cần pip install.

~~~sh
git clone https://github.com/tranduy123-hue/nhom15-library-chuong4.git
cd nhom15-library-chuong4
python app.py
~~~

Mở http://127.0.0.1:8765, dừng bằng Ctrl+C. Có thể dùng --port 8766 --database demo.sqlite3. SQLite được tạo tự động; dữ liệu không đưa vào Git. Ứng dụng thực hành local, chưa có đăng nhập để triển khai công khai.

## Phạm vi

Book gồm id, title, author, isbn. Tên và tác giả không rỗng, tối đa 255/150 ký tự. ISBN-10/13 được kiểm tra checksum, bỏ khoảng trắng/gạch nối và chuẩn hóa X; UNIQUE trong SQLite bảo vệ cả ghi đồng thời. ISBN-10/13 tương đương vẫn là hai chuỗi định danh riêng, không quy đổi chéo.

Form tiếng Việt thêm và hiển thị sách, giữ dữ liệu khi lỗi, escape HTML, kiểm tra CSRF. Nhập thử Clean Code / Robert C. Martin / 9780132350884. Nhập lại ISBN 978-0-13-235088-4 để kiểm tra báo trùng.

FineCalculator: <=0 ngày trả 0; 5.000đ/ngày; >10 ngày cộng 20% tổng tiền phạt bằng số nguyên.

## Kiểm thử AAA

~~~sh
python -B -W error::ResourceWarning -m unittest discover -s tests -v
~~~

42 test (toàn bộ đạt, 100% PASS):
- **10 tests Repository** (Hào đóng góp thêm 3 tests tại PR #3: danh sách rỗng, độ dài tối đa 255/150 ký tự, ID tự tăng).
- **12 tests Service/Validation** (Bảo đóng góp thêm 2 tests tại PR #4: chuẩn hóa ISBN gạch nối, từ chối tác giả khoảng trắng).
- **9 tests FineCalculator** (Bảo đóng góp thêm 2 tests tại PR #4: ca quá hạn 15 ngày 90.000đ và 30 ngày 180.000đ).
- **11 tests HTTP Web** (Thịnh đóng góp thêm 3 tests tại PR #5: route favicon 204, style.css 200 text/css, validation form rỗng 422).
Các ca đề yêu cầu: testNoFine(0)=0, testNormalFine(5)=25000, testHeavyFine(11)=66000. Có biên -1/10, persistence, concurrent duplicate, SQL injection, HTML escaping và token Unicode. CI GitHub Actions chạy trên Python 3.11 và 3.12 đều xanh 100%.

## Task độc lập trên Jira

| Task | Nội dung | Phụ trách | Trạng thái |
|---|---|---|---|
| [KAN-19](https://duygk45.atlassian.net/browse/KAN-19) | T1: Bảng Book | Hào | Done |
| [KAN-20](https://duygk45.atlassian.net/browse/KAN-20) | T2: Entity và Repository | Hào | Done |
| [KAN-21](https://duygk45.atlassian.net/browse/KAN-21) | T3: Service thêm sách | Duy | Done |
| [KAN-22](https://duygk45.atlassian.net/browse/KAN-22) | T4: Form và HTTP | Thịnh | Done |
| [KAN-23](https://duygk45.atlassian.net/browse/KAN-23) | T5: Unit Test AAA | Bảo | Done |
| [KAN-24](https://duygk45.atlassian.net/browse/KAN-24) | T6: Git và review | Duy, cả nhóm | Done |
| [KAN-25](https://duygk45.atlassian.net/browse/KAN-25) | UT1: Bổ sung test Repository | Hào | Done (PR #3) |
| [KAN-26](https://duygk45.atlassian.net/browse/KAN-26) | UT2: Bổ sung test Service & Fines | Bảo | Done (PR #4) |
| [KAN-27](https://duygk45.atlassian.net/browse/KAN-27) | UT3: Bổ sung test Form HTTP | Thịnh | Done (PR #5) |

## Thành viên và Phân công

- **Trần Duy** (`tranduy123-hue`): Trưởng nhóm, Service nghiệp vụ (T3), Git workflow, review & merge PR (T6).
- **Phan Văn Hào** (`phanvanhao1103-create`): Bảng Book (T1), SQLite BookRepository (T2), Unit test Repository (UT1 / PR #3).
- **Phan Thanh Thịnh** (`phanthanhthinhptt27-cmd`): Form nhập sách HTML (T4), Unit test Form & HTTP Web (UT3 / PR #5).
- **Lê Quân Bảo** (`lequanbaodepzai`): Unit test AAA FineCalculator (T5), Unit test mở rộng Service & Fines (UT2 / PR #4).

## Git workflow & Pull Requests

Nhóm áp dụng Git Feature Branch Workflow:
- Nhánh `main`: Mã nguồn tích hợp ổn định.
- Nhánh `feature/add-book-service` và `feature/add-book-ui`: Hai nhánh ban đầu thực hành xử lý conflict trên `README.md` (đã merge qua PR #1 và PR #2).
- Nhánh `feature/ut1-repository-tests`: Bổ sung test Repository của Hào (đã review & merge qua PR #3).
- Nhánh `feature/ut2-fines-service-tests`: Bổ sung test FineCalculator & Service của Bảo (đã review & merge qua PR #4).
- Nhánh `feature/ut3-web-tests`: Bổ sung test HTTP & Form của Thịnh (đã review & merge qua PR #5).
- Mọi Pull Request đều có mô tả chi tiết, phân công tác giả rõ ràng, có review nhận xét và merge vào `main`.
