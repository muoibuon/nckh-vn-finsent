# PHỤ LỤC v0.3 — SIẾT TRỤC TÍCH_CỰC ↔ TRUNG_TÍNH

**Đề tài NCKH 2026 (VJU)** — Bổ sung cho Hướng dẫn gán nhãn v0.2
**Phiên bản:** 0.3 — cập nhật sau vòng gán 210 tin (κ = 0,330; Krippendorff α = 0,325)
**Ngày:** 15/09/2026
**Đọc kèm:** file v0.2 (mọi quy tắc v0.2 vẫn giữ nguyên hiệu lực)

---

## 0. v0.3 sửa gì và VÌ SAO

Sau khi hai người gán độc lập 210 tin, κ chỉ đạt **0,330** — gần bằng vòng thử cũ (0,369),
tức guideline v0.2 **đã đúng nhưng chưa được áp dụng đều tay**. Chẩn đoán từ ma trận nhầm lẫn:

> **54/66 tin bất đồng (82%) dồn vào đúng một trục: `tich_cuc` ↔ `trung_tinh`.**
> Trục `tieu_cuc` gần như không lệch (2 người thống nhất rất tốt về tin xấu; ô
> tieu_cuc↔tich_cuc = **0 lệch**).

Phân bố lớp cho thấy **một người gán `tich_cuc` rộng hơn người kia ~10 điểm %**
(31,0% so với 21,4%). Nghĩa là hai người đang đặt **ngưỡng "đủ tốt để gọi là tích cực"**
ở hai chỗ khác nhau.

**v0.3 không thêm quy tắc mới lạ** — nó chỉ biến 3 mục sẵn có của v0.2 (mục 3, mục 6, mục 7)
thành **một quy trình bắt buộc phải chạy trước khi được phép bấm `tich_cuc`**, kèm 12 ví dụ
hiệu chuẩn lấy từ chính 54 tin vừa gán lệch.

---

## 1. CỔNG KIỂM TRA TÍCH CỰC *(quy tắc trung tâm của v0.3)*

> **Trước khi bấm `tich_cuc`, phải vượt qua CẢ BA cổng dưới đây.
> Trượt bất kỳ cổng nào ⇒ `trung_tinh`.**

**Cổng 1 — Có thông tin tài chính MỚI không?** *(mục 3 v0.2)*
Phải nói được thành lời: *"Tin cho biết [con số / sự kiện tài chính cụ thể]."*
- Không có con số / sự kiện ràng buộc ⇒ **trượt** ⇒ `trung_tinh`.

**Cổng 2 — Thông tin đó có phải về BẢN THÂN DOANH NGHIỆP không, hay chỉ về GIÁ / TÀI SẢN cá nhân?** *(mục 6 v0.2, nhóm `GIA`)*
- Nếu tin nói cổ phiếu **đã tăng/giảm bao nhiêu %**, vốn hoá lập kỷ lục, hoặc tài sản
  của chủ tịch/tỷ phú tăng ⇒ đó là **hệ quả của giá**, không phải nguyên nhân tài chính mới
  ⇒ **trượt** ⇒ `trung_tinh` + mã `GIA`.

**Cổng 3 — Thông tin đó đã CHẮC CHẮN chưa, hay mới chỉ là tham vọng/kế hoạch mơ hồ?** *(mục 6 + mục 7 v0.2)*
- Phát biểu, tầm nhìn, "đặt mục tiêu trở thành...", MOU, ý tưởng chưa có vốn/tiến độ
  ⇒ **trượt** ⇒ `trung_tinh`.
- Chỉ khi kế hoạch **đã có số liệu cụ thể** (vốn đầu tư, tiến độ, giá trị hợp đồng đã ký)
  mới được qua cổng.

Chỉ tin **qua cả ba cổng** mới được gán `tich_cuc`.

---

## 2. Bốn nhóm lỗi cụ thể phát hiện ở vòng 210 tin

Đây là 4 nhóm chiếm gần hết 54 tin lệch. Ghi nhớ 4 nhóm này là đủ diệt phần lớn bất đồng.

### Nhóm A — Tin biến động giá / tài sản cá nhân → `trung_tinh` + `GIA`
Trượt **Cổng 2**. Đây là nhóm lệch nhiều nhất.

| Tiêu đề (rút gọn) | Nhãn đúng | Vì sao |
|---|---|---|
| [VIC] Vingroup lập kỷ lục mới, tỷ phú Vượng đứng trước ngưỡng cửa lịch sử | ⚪ `GIA` | nói vốn hoá/tài sản đã tăng, không có KQKD mới |
| [MSN] Cổ phiếu MSN tăng kịch trần, tài sản tỷ phú Nguyễn Đăng Quang chạm... | ⚪ `GIA` | biến động giá + tài sản cá nhân |
| [HPG] Cổ phiếu Hòa Phát lên đỉnh 3 năm, tài sản Trần Đình Long tăng vọt | ⚪ `GIA` | biến động giá + tài sản cá nhân |
| [TCB] Vốn hóa Techcombank tăng vọt lên cao nhất 20 tháng | ⚪ `GIA` | vốn hoá tăng là hệ quả của giá |
| [SHB] Một cổ phiếu bất ngờ khớp lệnh hơn trăm triệu đơn vị | ⚪ `GIA` | thanh khoản/giá, không có thông tin DN |

### Nhóm B — Phát biểu / tham vọng / PR không số liệu → `trung_tinh`
Trượt **Cổng 3** (hoặc Cổng 1).

| Tiêu đề (rút gọn) | Nhãn đúng | Vì sao |
|---|---|---|
| [FPT] Chủ tịch Trương Gia Bình đặt mục tiêu tạo mô hình AI nhỏ gọn nhất | ⚪ | tham vọng, không lộ trình/số liệu (≈ ví dụ #13 v0.2) |
| [HDB] Tỷ phú Thảo: "HDBank muốn được khách hàng lựa chọn vì chất..." | ⚪ `PR` | phát biểu quảng bá, không có số |
| [VHM] Lợi nhuận kỷ lục, Vinhomes trả thu nhập lãnh đạo bao nhiêu | ⚪ `KHO` | có "lợi nhuận kỷ lục" nhưng tiêu đề lái sang lương lãnh đạo — thông tin chính không phải KQKD mới; nếu nội dung nêu rõ số lãi cụ thể thì mới cân nhắc 🟢 |

### Nhóm C — Cổ tức tiền mặt / mua cổ phiếu quỹ → `tich_cuc` (ĐỪNG bỏ sót!)
Đây là nhóm lệch **ngược chiều**: người gán `trung_tinh` mới là người SAI.
Theo mục 7 v0.2, các tin này **có dòng tiền thực về cổ đông** ⇒ `tich_cuc`.

| Tiêu đề (rút gọn) | Nhãn đúng | Vì sao |
|---|---|---|
| [MWG] Thế Giới Di Động dự chia cổ tức 10%, mua lại cổ phiếu quỹ, ESOP | 🟢 | cổ tức tiền mặt + mua CP quỹ (= ví dụ #10 v0.2) |
| [MWG] Chuẩn bị mua cổ phiếu quỹ sau khi Bách Hóa Xanh có lãi | 🟢 | mua CP quỹ = giảm lượng CP lưu hành |
| [FPT] FPT hoàn thành tăng vốn điều lệ, cổ đông nước ngoài... | 🟢 hoặc ⚪ `KHO` | nếu là phát hành cho đối tác chiến lược giá cao ⇒ 🟢; nếu chỉ là thủ tục tăng vốn ⇒ ⚪ |

### Nhóm D — Giao dịch cổ đông lớn / khối ngoại → theo mục 7.1 v0.2
| Tiêu đề (rút gọn) | Nhãn đúng | Vì sao |
|---|---|---|
| [MBB] Quỹ ngoại hé lộ lý do chi 700 tỷ mua thêm chục triệu CP MBB | 🟢 | mua vào khối lượng lớn = tín hiệu tích cực (mục 7.1) |
| [VIB] Khối ngoại bán ròng hơn 148 triệu CP, gần 5% vốn tại một ngân hàng | 🔴 hoặc ⚪ `KHO` | bán ròng lớn — cân nhắc tieu_cuc; nếu chỉ là chuyển nhượng thoả thuận đã biết ⇒ ⚪ |

---

## 3. Quy ước chốt cho các tin ranh giới hay gặp

Những trường hợp v0.2 chưa nói rõ, nay chốt để 2 người không lệch:

| Tình huống | Nhãn chốt | Lý do |
|---|---|---|
| Vốn hoá / tài sản cá nhân lập kỷ lục | `trung_tinh` + `GIA` | hệ quả của giá |
| "Cổ phiếu vượt đỉnh / lên đỉnh N năm" | `trung_tinh` + `GIA` | mô tả giá, không phải nhân quả DN |
| Chỉ tiêu an toàn vốn (CAR), hệ số kỹ thuật tốt | `trung_tinh` | không tác động trực tiếp dòng tiền ngắn hạn 1–5 phiên, trừ khi tin nhấn mạnh hệ quả lợi nhuận |
| "Được vinh danh / lọt bảng xếp hạng quốc tế" | `trung_tinh` + `PR` | giải thưởng không tạo dòng tiền |
| Câu hỏi tu từ / suy đoán ("SK đã tìm được đối tác?") | `trung_tinh` | chưa xác nhận, mới là suy đoán |
| Cổ tức TIỀN MẶT | `tich_cuc` | dòng tiền thực về cổ đông |
| Mua lại cổ phiếu quỹ | `tich_cuc` | giảm CP lưu hành |
| Cổ đông lớn/khối ngoại MUA khối lượng lớn | `tich_cuc` | tín hiệu nội bộ (mục 7.1) |
| Cổ đông lớn/khối ngoại BÁN ròng khối lượng lớn | `tieu_cuc` | tín hiệu nội bộ (mục 7.1) |

---

## 4. Checklist v0.3 — dán cạnh màn hình khi gán lại

Trước khi bấm **`tich_cuc`**, tự hỏi đủ 3 câu:

1. **Có con số / sự kiện tài chính mới cụ thể không?** (không → trung_tính)
2. **Đây là thông tin về DOANH NGHIỆP hay chỉ là GIÁ/TÀI SẢN đã biến động?** (chỉ là giá → trung_tính + `GIA`)
3. **Thông tin đã CHẮC CHẮN chưa, hay mới là tham vọng/MOU/kế hoạch mơ hồ?** (mơ hồ → trung_tính)

Trước khi bấm **`trung_tinh`** cho tin có vẻ tốt, kiểm tra ngược:
4. **Có phải cổ tức tiền mặt / mua CP quỹ / cổ đông lớn mua vào không?** (nếu có → phải là `tich_cuc`, đừng bỏ sót)

---

## 5. Quy trình gán lại (v0.3)

1. **Cả 2 người đọc kỹ mục 1–4 của phụ lục này** (10 phút).
2. Gán lại **đúng 210 tin cũ** (không phải bộ mới) — để đo κ trên cùng tập, thấy được cải thiện.
3. Chạy lại:
   ```bash
   python3 -m src.annotation.iaa \
     --file1 data/gold/nhan_duyen_da_gan.csv \
     --file2 data/gold/file_nguon_tien_trinh.csv \
     --label-col1 nhan --label-col2 nhan_chu --join-key url
   ```
4. **κ ≥ 0,6** → chuyển sang gán mở rộng tới 300 tin.
5. **κ vẫn < 0,6** → mở `bat_dong.csv`, soi nhóm lệch còn lại, cập nhật v0.4.

**Mục tiêu thực tế:** với 4 nhóm lỗi trên chiếm 82% bất đồng, nếu 2 người áp dụng đúng
Nhóm A + C (chỉ 2 nhóm này đã ~40 tin), κ có thể nhảy từ 0,33 lên vùng 0,55–0,65 ngay.

---

## 6. Lịch sử phiên bản

| Bản | Ngày | Thay đổi |
|---|---|---|
| 0.1 | 11/09/2026 | Bản draft đầu tiên |
| 0.2 | 13/09/2026 | Thêm phép kiểm tra thông tin tài chính mới (mục 3), tiền vào/ra (3.1), nhóm tin trung tính (mục 6), PR có số vs rỗng (6.1), giao dịch nội bộ (7.1), 16 ví dụ hiệu chuẩn |
| 0.3 | 15/09/2026 | Sau 210 tin (κ=0,330). Thêm CỔNG KIỂM TRA TÍCH CỰC (mục 1), 4 nhóm lỗi thực tế + 12 ví dụ từ tin lệch thật (mục 2), quy ước chốt ranh giới (mục 3), checklist gán lại (mục 4) |
