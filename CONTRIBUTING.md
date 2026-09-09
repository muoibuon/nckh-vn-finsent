# Quy tắc đóng góp

## 1. Git workflow

- **KHÔNG** push thẳng lên `main`. Mọi thay đổi phải qua Pull Request có review.
- Đặt tên nhánh: `<tên>/<mô-tả-ngắn>`. Ví dụ: `duyen/scraper-cafef`, `an/event-study-capm`, `dat/prompt-qwen`.
- Commit message ngắn, tiếng Anh, dạng imperative:
  - ✅ `add cafef scraper with timestamp parsing`
  - ❌ `sửa scraper`
- Mỗi PR chỉ giải quyết **1 việc**. PR dài quá 500 dòng thay đổi phải tách nhỏ.

## 2. Định nghĩa "hoàn thành" (Definition of Done)

Một task chỉ được đóng khi:
1. Code có **seed cố định** (`--seed 42` mặc định) — cùng input → cùng output.
2. **Tái lập bằng script**, không phải "chạy từng cell notebook".
3. Có **test** (nếu là code core) hoặc **notebook demo** (nếu là exploration).
4. **Docstring** rõ ràng cho hàm public.
5. Đã chạy `make lint` và `make format` sạch.
6. PR có ít nhất **1 review** từ thành viên khác.

## 3. Cấu trúc code

- Mỗi module `src/<name>/` phải có `__init__.py` và `README.md` mô tả module.
- Config nằm ở `configs/`, không hardcode magic numbers trong code.
- Không commit dữ liệu thô (>10MB) — dùng `.gitignore`.
- Notebooks chỉ dùng cho **demo/exploration**, KHÔNG chứa logic quan trọng — logic vào `src/`.

## 4. Secrets

- **TUYỆT ĐỐI KHÔNG** commit API key, mật khẩu, token.
- Dùng file `.env` (đã trong `.gitignore`), tham khảo `.env.example`.
- Nếu lỡ commit key, thông báo NGAY cho chủ nhiệm và rotate key.

## 5. Style

- Python: PEP 8, formatted bằng `black` (line length 100).
- Docstring: Google style.
- Type hints cho hàm public.

## 6. Quy trình review

Người review kiểm tra:
- [ ] Code chạy được (`make test` pass).
- [ ] Logic đúng, đọc hiểu được.
- [ ] Không có magic number, hardcoded path.
- [ ] Không leak dữ liệu test vào train (data leakage).
- [ ] Không có `print()` debug còn sót lại.

## 7. Họp tuần

- Thời gian: **Chủ nhật 20:00** (linh hoạt).
- Chủ trì: chủ nhiệm đề tài (Đạt).
- Nội dung: tiến độ tuần, blocker, kế hoạch tuần sau.
- Cập nhật trạng thái trên sheet "Theo dõi tiến độ".
