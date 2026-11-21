# DangTrinhdzZz — phản tư cá nhân

- Tôi đã làm: [P1 #13](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/667b652), [P1 #14](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/554a763), [P1 #15](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/c869a04), [P2-4](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/0368168): sửa luật khách, kiên nhẫn, uy tín và giới hạn món theo kế hoạch Ngày; viết regression test.
- Tôi đã review: kiểm tra staged diff, RED → GREEN cho từng lỗi, rà ảnh hưởng khi tích hợp Phase 3/4, giữ code đồng đội và chạy full suite 134 tests, 1 skipped; [merge](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/ffbef78).
- AI sai ở đâu: Codex từng bị chặn `.git/index.lock`; fixture kho đếm v1.1 bị từ chối khi chuyển sang item-list v1.2; full suite còn phát hiện lỗi rơi nguyên liệu, sau đó chờ bản sửa đúng từ Draft.
- Điều tôi học được: giữ assertion khi đổi schema, luôn kiểm tra RED → GREEN và chạy lại toàn bộ test sau merge; không commit khi gate chưa đạt.
