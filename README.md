# Hệ thống Quản lý Bài tập & Giải đố EHC

Một ứng dụng Web được xây dựng bằng Flask (Python) và cơ sở dữ liệu MySQL, phục vụ cho việc quản lý lớp học. Hệ thống cung cấp nền tảng để Giáo viên giao bài tập, Sinh viên nộp bài, đồng thời tích hợp một trò chơi giải đố (CTF Challenge) mang phong cách An toàn thông tin.

## Tính năng chính

Hệ thống phân quyền rõ ràng thành 2 vai trò: Giáo viên (Teacher) và Sinh viên (Student).

* **Xác thực người dùng:** Đăng ký, đăng nhập và phân quyền tự động. Mật khẩu được băm (hash) bảo mật bằng Bcrypt.
* **Quản lý bài tập:** Giáo viên có thể tạo bài tập mới kèm file đề bài; Sinh viên tải file đề bài về máy.
* **Nộp bài:** Sinh viên nộp bài bằng cách tải file lên hệ thống; Giáo viên xem và tải về toàn bộ bài nộp của sinh viên.
* **Trò chơi giải đố (CTF Challenge):** Giáo viên upload một file đáp án (định dạng .txt) và đưa ra gợi ý. Sinh viên phải đoán đúng tên file để hệ thống hiển thị nội dung bí mật. Cơ chế này không lưu đáp án vào Database nhằm rèn luyện tư duy chống Local File Inclusion.

## Công nghệ sử dụng

* **Backend:** Python 3.x, Flask
* **Database:** MySQL, SQLAlchemy (ORM)
* **Frontend:** HTML5, CSS3, Jinja2 Templates
* **Public URL:** Ngrok

## Hướng dẫn Cài đặt & Chạy dự án (Localhost)

Làm theo các bước sau để khởi chạy hệ thống trên máy tính cá nhân.

### 1. Chuẩn bị môi trường
Đảm bảo máy tính đã cài đặt Python và MySQL Server. Mở Terminal và cài đặt các thư viện cần thiết:

```bash
pip install flask flask-sqlalchemy flask-bcrypt flask-login pymysql
