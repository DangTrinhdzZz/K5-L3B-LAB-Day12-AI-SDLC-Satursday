# FPT-Trungocsdiogee — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Phase 1, bắt cá (`_catch()`):
    [hold_full không đặt hồi chiêu](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/e7fc4a77c78f16e1a58c6276f9db62d758d2bab5),
    [chỉ xét đàn gần nhất, thiếu chỗ không thử đàn khác](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/cb946d73e9b119cd277061c43cdaaef0fe4a16ed),
    [hold_full dùng khóa fish_id](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/eef69523db5305940547105da5e29b602edac083),
    [bổ sung test](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/a985d94fa6fd78995340a4157bc2fc45f9feaff5).
  - Phase 2, pause (`Session.step()`):
    [bước resumed chạy gameplay ngay](https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/a80c45a504a4866b73f096c8f28ceef792205a2d),
    test `test_day_mode.Pause.test_resumed_step_runs_gameplay`.
- Tôi đã review (kèm link):
- AI sai ở đâu và tôi phát hiện thế nào: không thấy AI sai luật; mỗi lỗi đều chạy lệnh tái hiện và thấy test đỏ trước khi sửa. Lần đầu commit Phase 2 hỏng vì AI truyền message sai cú pháp PowerShell, đọc lỗi git rồi commit lại bằng file message.
- Điều tôi học được: sửa luật phải bám đúng câu trong PRD/Ticket (ví dụ "chạy gameplay ngay trong bước đó") và khóa lại bằng test hộp đen, vì lỗi lệch một tick rất khó thấy khi chơi thử.
