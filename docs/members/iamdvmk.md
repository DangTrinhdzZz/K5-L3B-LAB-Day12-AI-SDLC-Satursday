# iamdvmk — phản tư cá nhân (≤ 200 từ)

- Tôi đã làm (kèm link commit):
  - Phase 1, lát 1 (oxy, ngạt) — PR #4 (https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/pull/4):
    - Reset đếm ngạt khi nổi lên mặt nước: https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/34e45f4
    - Đếm ngạt cả bước vừa chạm oxy 0, ngạt lần đầu ở t+59: https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/29cd54a
    - `dive`/`surface` dùng cùng biên d ≤ surface_depth với `at_surface`: https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/e495d5f
  - Phase 2, P2-1 — cá chạm mép x đảo thành phần hướng x: https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday/commit/0a2ad19
- Tôi đã review (kèm link): chưa có.
- AI sai ở đâu và tôi phát hiện thế nào: AI viết test "nổi lên đúng bước đáng lẽ ngạt" với d = 0.55 nhưng quên vận tốc còn đang ramp, bước đầu chỉ đi ~0.01 m nên chưa lên mặt nước. Tôi đọc snapshot từng tick thì thấy fixture sai chứ không phải luật sai.
- Điều tôi học được: tái hiện lỗi bằng test đỏ trước rồi mới sửa giúp chắc sửa đúng chỗ.