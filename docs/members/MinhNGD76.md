# MinhNGD76 — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit): sửa 4 lỗi luật gather, mỗi lỗi một commit kèm test hồi quy.
  - P1-4 `faint.lost` theo LIFO: [ce6251e](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/ce6251e)
  - P1-5 ngất thì bỏ toàn bộ giỏ, kho rỗng: [6e6e88b](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/6e6e88b)
  - P1-6 `choke.hp` ghi Máu sau khi trừ: [4dc9c6e](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/4dc9c6e)
  - P2-2 Cá Sấu chạm, số món rơi = floor(số đang mang × loss_ratio): [7b31b94](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/7b31b94), khôi phục sau merge + đổi test sang kho v1.2: [6d7f748](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/6d7f748)
- Tôi đã review (kèm link): diff AI viết cho cả 4 lỗi trên (link commit ở trên), đọc từng dòng và chạy lại toàn bộ test trước khi commit.
- AI sai ở đâu và tôi phát hiện thế nào: test Cá Sấu có sẵn dùng giỏ 4 món (chẵn) nên làm tròn và `floor` ra cùng kết quả, lỗi P2-2 lọt qua; chỉ lộ khi viết test giỏ lẻ 3 món. Ở P1-6, file phân công không nói `choke.hp` khi Máu còn 1 (event ghi 0 rồi mới `faint`); AI tự chọn ghi 0 theo "hp sau trừ", cần PO xác nhận.
- Điều tôi học được: test xanh chưa chắc luật đúng, phải viết test hồi quy đỏ trước rồi mới sửa; chỗ spec mơ hồ thì ghi lại và hỏi PO thay vì để AI tự chọn; sau merge phải kiểm lại luật vì fix của mình có thể bị ghi đè.
