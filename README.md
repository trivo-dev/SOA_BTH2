# Bài thực hành 2 — Django, Router, Middleware và JWT

## Chạy trên Windows (PowerShell)

Yêu cầu Python 3.10 trở lên.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_demo_user
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Tài khoản thực hành: **admin / 123456**. Lệnh tạo tài khoản không ghi đè tài khoản đã tồn tại.
Không cần kích hoạt môi trường ảo.

## Các endpoint

| Phương thức | URL | Chức năng |
|---|---|---|
| POST | http://localhost:8000/ | Đăng nhập, cấp JWT |
| GET | http://localhost:8000/auth | Xác thực JWT và trả claims |
| GET | http://localhost:8000/hello | Trả {"message":"Hello World"} qua middleware |

URL không có dấu / ở cuối, ngoại trừ URL gốc.

Body đăng nhập (JSON):

```json
{"userName":"admin","password":"MTIzNDU2"}
```

`MTIzNDU2` là Base64 của `123456`. Tạo Base64 tại client PowerShell:

```powershell
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("123456"))
```

Kết quả đăng nhập có `token`, `tokenType: Bearer`, `expiresIn: 1800`.
Gửi header cho hai API bảo vệ:

```text
Authorization: Bearer <token>
```

## Thử bằng Postman

Import file `BTH2.postman_collection.json`. Chạy lần lượt:
1. **Login**: lưu token tự động vào biến collection; test giải mã header và payload, ghi chúng vào Postman Console.
2. **Auth**: trả người dùng và claims sau khi server kiểm tra chữ ký.
3. **Hello World**: trả thông điệp sau khi middleware cho phép.
4. **Missing token**: phải nhận 401.

JWT gồm ba phần ngăn bằng dấu chấm: header.payload.signature. Header dùng HS256;
payload gồm sub (IdUser dạng chuỗi), iat (thời điểm cấp), exp (hết hạn), jti (mã token).
Giải mã trong Postman chỉ dùng xem cấu trúc, không chứng minh chữ ký hợp lệ.
Đăng nhập lần nữa rồi sử dụng token cũ sẽ nhận 401. Token hết hạn hoặc sửa chữ ký cũng nhận 401.
Sai tài khoản/mật khẩu: 401; JSON/Base64 sai: 400; Content-Type sai: 415; phương thức sai: 405
(với API bảo vệ cần token hợp lệ trước khi kiểm tra phương thức).

## Cấu trúc và luồng xử lý

- `config/urls.py` chuyển định tuyến đến `accounts/urls.py`.
- `accounts/views.py`: nhận JSON, giải mã Base64, kiểm tra hash mật khẩu và cấp JWT.
- `accounts/tokens.py`: tạo JWT và kiểm tra chữ ký HS256, các claims bắt buộc, hạn sử dụng.
- `accounts/middleware.py`: kiểm tra Bearer token, đối chiếu token đang lưu và gắn người dùng vào request.
- `accounts/models.py`: bảng User trong SQLite.

Luồng đăng nhập: client → router → login → kiểm tra mật khẩu → lưu token → trả JWT.
Luồng xác thực: client gửi Bearer → router xác định view → middleware kiểm tra → auth/hello.

Bảng User theo đề:

| Cột | Kiểu khai báo Django / SQL tương ứng |
|---|---|
| IdUser | AutoField / INTEGER PRIMARY KEY |
| UserName | CharField / VARCHAR(255), unique |
| Password | CharField / VARCHAR(255), lưu hash PBKDF2 của Django |
| Token | CharField / VARCHAR(255), token hiện hành |

SQLite không tự cưỡng chế độ dài VARCHAR; ứng dụng kiểm tra token <=255 ký tự khi cấp.
JWT chỉ chứa claims ngắn để phù hợp cột Token. Mỗi tài khoản có một token hiện hành.

Base64 là mã hóa biểu diễn, không bảo mật mật khẩu. Bài này chọn Base64 theo yêu cầu,
không dùng MD5 để lưu mật khẩu. Dùng HTTPS khi triển khai thực tế.
Khóa ký lấy từ DJANGO_SECRET_KEY; nếu chưa đặt sẽ sinh ngẫu nhiên một lần vào
`.local-secret` (đã được bỏ qua trong Git). Không chia sẻ file này hoặc cơ sở dữ liệu.
Đây là bài thực hành local, chưa có giới hạn lần đăng nhập hoặc quản lý refresh token.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

Kiểm tra đăng nhập, lưu token, xác thực, Hello World, dữ liệu lỗi, sai mật khẩu,
thiếu token, token hết hạn, sai khóa/thuật toán, thiếu claims và token bị thay thế.

Tài liệu: https://docs.djangoproject.com/en/5.2/topics/http/middleware/
và https://pyjwt.readthedocs.io/en/stable/usage.html
