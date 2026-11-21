# Kế hoạch Phase 3 (7 phút đầu)

- **Mục tiêu:** contract v1.2: kho cá thể có độ tươi qua file và trong day; giữ chỗ theo id; giá theo tươi; HUD độ tươi; tag `phase-3` trước 2:30.
- **Phân tích tác động, quyết định schema, thứ tự tích hợp:** [`docs/adr/0001-kho-ca-the-v12.md`](../adr/0001-kho-ca-the-v12.md).
- **Trước khi đổi schema:** gộp các PR sửa lỗi gather đang mở (#5, #6) vào `Draft` để không ai phải gỡ xung đột trên `gather.py`.
- **Phút 20:** smoke bàn giao kho (`docs/proof/phase-3/handover.txt`), standup.
- **Rủi ro:** test cũ dùng kho đếm → chuyển hết qua helper `items()` trong cùng commit đổi schema; sai số ở ngưỡng 30 → độ tươi tính bằng phân số.
