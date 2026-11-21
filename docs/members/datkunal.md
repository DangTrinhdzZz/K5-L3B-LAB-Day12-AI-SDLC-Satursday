# datkunal — Vũ Tuấn Đạt — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm.** Làm cặp với Tanh0406 trên cùng máy ở bản vá v1.0.1, mỗi lỗi một test đỏ trước khi sửa: Shop cho mua khi
  tiền đúng bằng giá (`<=` → `<`, `test_buy_with_exact_money`,
  [8ca2893](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/8ca2893)); giữ chỗ lấy cá thể
  chưa ươn tươi nhất, hòa theo id (`test_reserve_picks_freshest_item`,
  [b4a24f4](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/b4a24f4)).
- **Tôi đã kiểm chứng.** Chạy lại v1.0.2 trên máy Windows thứ hai: 139 test OK, soak 10/10 Ngày 0 crash, day tất định
  ([9e1b84d](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/9e1b84d)); viết hướng dẫn
  chạy test trên Windows ([50737ee](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/50737ee)).
  Quay video demo của nhóm.
- **AI sai ở đâu và tôi phát hiện thế nào?** 142 test hỏng với mã 9009: `python3` chỉ là lối tắt Microsoft Store.
  Claude Code tạo `python3.cmd` nhưng vẫn 9009, vì `subprocess.run([...])` không chạy `.cmd`; chép `python.exe` thành
  `python3.exe` thì 139 test xanh.
- **Điều tôi học được.** Test đỏ hàng loạt thì đọc mã thoát trước khi nghi luật; lỗi biên chỉ lộ khi test đúng giá trị biên.
