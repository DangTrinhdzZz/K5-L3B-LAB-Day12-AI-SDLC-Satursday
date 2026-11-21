# BSFactor — Nguyễn Nam Khánh

- **Tôi đã làm.** Phase 1, tôi sửa ba lỗi hái nút: tính cả đúng mép bán kính, đổi thời gian mọc lại từ giây sang tick và chỉ cho hái khi ở mặt nước. Phase 2, tôi sửa P2-3 để Cá Sấu phát hiện người chơi ở đúng ngưỡng độ sâu khi trong tầm. Mỗi lỗi có một test hồi quy. [Phase 1](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/pull/3) · [Phase 2](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/e505d7c)
- **Tôi đã kiểm chứng.** Cả bốn test đều tái hiện lỗi trước khi sửa. Bộ test đạt 60/60 khi gộp ba bản sửa Phase 1 và 93/93 sau bản sửa Phase 2.
- **AI sai ở đâu và tôi phát hiện thế nào?** Codex dùng danh sách nguyên liệu Phase 1 để kiểm tra bàn giao kho Phase 2. Kiểm tra thất bại vì fixture Phase 2 có thêm cá kèo và kèo nèo. Đối chiếu với fixture Phase 2 cho kết quả đúng.
- **Điều tôi học được.** Test đúng giá trị biên và kiểm tra tick cụ thể để phát hiện sai lệch trong luật.
