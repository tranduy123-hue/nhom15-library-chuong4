# Bằng chứng Git workflow

Repo được khởi tạo mới, không sao chép .git hoặc commit từ repo cũ.

- Baseline main: 23a647a.
- Backend feature: acc96e0 và 797adb2.
- UI feature từ baseline: c337f11 và 39ebf63.
- Hai nhánh sửa cùng dòng README. Khi nhánh UI merge feature/add-book-service, Git báo CONFLICT (content): Merge conflict in README.md và exit 1.
- Bản marker thật trước xử lý nằm ở conflict-before.txt. Giải quyết bằng cách kết hợp backend, UI và kiểm thử; commit merge giữ hai parent.
- Các nhánh sẽ được giữ trên GitHub; PR do tài khoản chủ repo tạo và yêu cầu review thật từ nhóm.

Mã/test được AI hỗ trợ. Phân công Jira và reviewer request không phải chứng cứ thành viên đã tự viết test; nhiệm vụ tiếp nhận test đang theo dõi riêng.
