# Ma trận truy vết Phase 4 (contract v1.3, phát hành v1.0.0)

> Kết quả dưới đây chạy thật trên commit `f94ef1c` (nhánh `Draft`). Bench/QA **chạy lại trên commit gắn tag
> `phase-4` / `v1.0.0`** và cập nhật cột "Kết quả" nếu khác. Bằng chứng: [`docs/proof/phase-4/`](../proof/phase-4/).

| AC | Cách kiểm chứng | Bằng chứng | Kết quả (f94ef1c) |
|---|---|---|---|
| AC-P4-01 contract_version 1.3, khai `bench_cmd`, `soak_cmd` ở gốc manifest; gameplay / kho / JSONL theo v1.2 | `tests/test_phase4_release.py::Manifest`, regression P1–P3 | unittest.txt | Đạt |
| AC-P4-02 `bench_cmd --seed 42 --duration 30 --out bench.json` chạy cảnh chuẩn, ghi đủ 5 trường | chạy lệnh; `BenchMetrics` (công thức avg / 1% low) | bench.json, bench.txt | Đạt: avg 144.0 FPS, 1% low 139.59 FPS, 4320 khung / 30.0 s, load 600 ms (Windows 10, Chrome headless) |
| AC-P4-03 Mốc báo cáo: avg ≥ 60, 1% low ≥ 30, load ≤ 10 s | bench.txt | bench.txt | Đạt cả ba mốc |
| AC-P4-04 `soak_cmd --seed 7 --days 10 --out soak.json`: days_completed = days, crashes = 0, lặp lại được | chạy 2 lần; `Soak` | soak.json, soak.txt | Đạt: 10/10 Ngày, 0 crash, 2 lần giống nhau (bỏ duration_s), ~5 s |
| AC-P4-05 Clone sạch chạy bản có giao diện trong ≤ 3 lệnh | clone → `cd` → `python3 -m chonoi.live --mode day` → GET / và /state | clean-clone.txt | Đạt (trang có canvas, màn menu); 128 test xanh trong bản clone |
| AC-P4-06 Cảnh báo thủy quái gần: biểu tượng + chữ | chơi thử | hc-gather.png | Đạt (🐊 "Thủy quái gần!" + viền màn hình) |
| AC-P4-07 Cảnh báo oxy sắp hết: biểu tượng + chữ | chơi thử | hc-gather.png | Đạt (⚠ "Oxy sắp hết, nổi lên!", 🫁 "HẾT HƠI!") |
| AC-P4-08 Cảnh báo khách sắp giận: biểu tượng + chữ | chơi thử | hc-quan.png | Đạt ("! SẮP GIẬN" cạnh khách + banner 😠) |
| AC-P4-09 Chế độ tương phản cao, chơi thử cả ba cảnh báo ở chế độ này | phím H / Cài đặt, `?hc=1` | hc-gather.png, hc-quan.png | Đạt |
| AC-P4-10 CHANGELOG theo phase, release notes, bản đóng gói, CREDITS, LICENSE | đọc file; `python3 tools/package.py v1.0.0` | CHANGELOG.md, docs/release-notes-v1.0.0.md | Đạt ở commit; bản zip tạo lúc phát hành |
| AC-P4-11 Tag `phase-4` và Release `v1.0.0` cùng trỏ commit trên `main` trước 3:00 | `git rev-parse phase-4 v1.0.0`, trang Release | | (Release/Integrator điền) |
| AC-P4-12 Regression P1–P3 còn hiệu lực đạt | toàn bộ test | unittest.txt | Đạt: 128 OK (1 skip: bench thật, chạy riêng bằng CHONOI_RUN_BENCH=1 → đạt) |
| AC-P4-13 Mở rộng leaderboard: khai extensions, cặp cờ, ghi một mục / lượt chuẩn, sắp + hòa, export | `Leaderboard` | summary-leaderboard.png | Đạt |
| AC-P4-14 Mở rộng phụ đề SFX: phụ đề hiện đúng lúc khi tắt âm thanh | chơi thử `?sound=0` | captions.png | Đạt ("[tiếng cá quẫy]" lúc bắt cá) |
| AC-P4-15 Retro rà hành động P2, phản tư cá nhân đủ người | đọc `docs/retro.md`, `docs/members/` | | (điều phối retro điền) |

## Đánh giá ngắn
- Đạt: lệnh v1.3, bench, soak, clone sạch, cảnh báo + tương phản cao, 2 mở rộng, regression.
- Cần trước khi phát hành: merge các bản sửa còn lại, chạy lại toàn bộ test + bench + soak trên commit gắn tag, cập nhật bảng trên.
