# Quán Ăn Chợ Nổi v1.0.0 — nhóm Satursday

Út Sen lặn bắt cá, hái bông trên sông Chín Khúc buổi sáng, tối mở quán trên nhà bè của Má Tư, cuối ngày mua nâng
cấp cho lần lặn sau. Trọn 5 Ngày theo kế hoạch của Má Tư, chạy trong trình duyệt, chỉ cần Python 3.

## Cách chạy (macOS / Linux, Python 3.10+, không cài thêm gì)

```bash
git clone https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday.git
cd K5-L3B-LAB-Day12-AI-SDLC-Satursday
python3 -m chonoi.live --mode day      # mở địa chỉ in ra (mặc định http://127.0.0.1:8000/)
```

Dùng bản đóng gói đính kèm Release: giải nén `quan-an-cho-noi-v1.0.0.zip`, `cd` vào thư mục vừa giải nén rồi chạy
lệnh thứ ba ở trên.

**Điều khiển:** WASD / mũi tên đi, bơi · E cập bến / hái / nấu / bưng / phục vụ · Space bắt cá · 1 / 2 mua nâng cấp,
Enter đóng Shop · Esc / P tạm dừng · H tương phản cao · M âm thanh · C phụ đề · R chơi lại.

## Điểm mới theo phase
- **Phase 1 (contract v1.0):** buổi sáng lặn và hái (oxy, ngạt, Máu, ngất, hái nút, bắt cá, giỏ), buổi tối mở quán
  (khách, giữ chỗ, bếp, bưng, phục vụ, boa, uy tín), file kho nối hai buổi, HUD.
- **Phase 2 (v1.1):** số liệu chuẩn, 6 nguyên liệu / 6 món, 2 bếp / 4 bàn, đàn cá bơi và sinh theo lịch,
  Cá Sấu Năm Chèo, vòng ngày D1–D5 với Shop và nâng cấp oxy / Máu, pause, menu, màn giới thiệu.
- **Phase 3 (v1.2, Mùa Nước Nổi):** kho cá thể có độ tươi; hàng ươn dưới 30; giữ chỗ cá thể tươi nhất;
  giá món theo độ tươi; HUD độ tươi. *Breaking change:* file kho đếm cũ không còn đọc được (xem CHANGELOG).
- **Phase 4 (v1.3):** `bench_cmd` (benchmark có render), `soak_cmd` (bot tất định nhiều Ngày), cảnh báo có chữ +
  biểu tượng (thủy quái gần, oxy sắp hết, khách sắp giận), chế độ tương phản cao.
- **Mở rộng:** bảng xếp hạng cục bộ (`leaderboard`), phụ đề hiệu ứng âm thanh.

## Lệnh cho người chấm
- Test: `PYTHONPATH=tests:. python3 -m unittest discover -s tests -v`
- Headless: `python3 -m chonoi.headless --mode gather|quan|day --seed 1 --ticks 600 --out out.jsonl [--days 1..5]`
- Benchmark: `python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json` (cần Chrome / Chromium / Edge;
  đặt `CHONOI_BROWSER=<đường dẫn>` nếu không tự tìm thấy)
- Soak: `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json`
- Bảng xếp hạng: `python3 -m chonoi.live --mode day --export-leaderboard out.json [--leaderboard store.json]`

## Giới hạn đã biết
- Benchmark cần một trình duyệt nhân Chromium trên máy; không có thì lệnh thoát mã 1 kèm hướng dẫn.
- Đồ họa là hình khối 2D tạm, âm thanh là tiếng bíp tổng hợp; chưa có nhạc nền.
- Mới làm 2 mở rộng (bảng xếp hạng, phụ đề SFX); các mở rộng Lao xua, Vợt, Rắn, Cháy món, Chợ Chú Sáu, Sổ tay,
  Dòng nước lũ, Khách đặt trước chưa làm (bị bỏ qua đúng hợp đồng: lệnh `buy` của chúng trả `buy_failed unknown`).
- Bot của `soak_cmd` chỉ để kiểm độ bền, không tối ưu điểm.
- `tools/check_team.py` của starter vẫn báo nhóm vượt 6 người (nhóm có 7 người, đã được giảng viên cho phép).
