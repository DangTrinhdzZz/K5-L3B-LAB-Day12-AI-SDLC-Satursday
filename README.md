# Quán Ăn Chợ Nổi — nhóm Satursday

> Day 12 · AI SDLC · K5-L3B. Út Sen lặn bắt cá, hái bông trên sông Chín Khúc buổi sáng, tối mở quán trên nhà bè của Má Tư, cuối ngày mua nâng cấp cho lần lặn sau.
> Đề bài và lịch phase: **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** · Thành viên và vai: [`TEAM.md`](TEAM.md) · Test Contract **v1.1**.

## Chạy từ clone sạch (macOS / Linux, chỉ cần Python 3.10+)

```bash
git clone https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday.git && cd K5-L3B-LAB-Day12-AI-SDLC-Satursday
python3 -m chonoi.live --mode day          # mở địa chỉ in ra trên trình duyệt: Menu -> Chơi, trọn 5 Ngày
```

Không cần cài thêm gì (chỉ thư viện chuẩn Python). `build_cmd` là `true`. Chơi riêng từng buổi:
`python3 -m chonoi.live --mode gather --inventory-out kho.json` rồi `python3 -m chonoi.live --mode quan --inventory kho.json`.

**Test của nhóm (1 lệnh):**

```bash
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v
```

**Headless (Test Contract v1.1):**
`python3 -m chonoi.headless --mode gather|quan|day --seed <int> --ticks <N> --out out.jsonl [--days 1..5] [--scenario sc.json] [--inputs in.json] [--inventory kho.json] [--inventory-out kho.json] [--snapshot-every N]`

## Vòng ngày

Menu chính (Chơi / Thoát) → **DayIntro** (Má Tư đọc món và nguyên liệu cần lấy) → **buổi sáng** (lặn & hái) → **EveningIntro** (nhập kho, món nấu được) → **buổi tối** (mở quán) → **DayResult** (khách phục vụ / bỏ đi, tiền, boa, uy tín) → **Shop** → Ngày kế; sau Ngày 5 là **Tổng kết**. Các màn giới thiệu tự chuyển sau 4 s hoặc khi nhấn phím.

## Điều khiển

| Phím | Buổi sáng | Buổi tối | Shop |
|---|---|---|---|
| WASD / mũi tên | bơi ngang, lặn / nổi | đi trong nhà bè | — |
| **E** | cập bến / hái nút ở mặt nước | nấu ở bếp, bưng món chín, phục vụ ở bàn | — |
| **Space** | bắt đàn cá gần nhất khi lặn | — | — |
| **1 / 2** | — | — | mua Bình oxy / Áo phao |
| **Enter** | — | — | đóng Shop |
| **Esc / P** | tạm dừng (Tiếp tục / Về menu) | như trái | như trái |
| **R** | chơi lại | chơi lại | chơi lại |

HUD sáng: Máu, oxy (dưới 25 % đổi đỏ, nhấp nháy), đồng hồ (≤ 30 s đổi đỏ), độ sâu và vùng, giỏ theo loại, danh sách cần lấy (đã lấy/cần), hồi bắt, gợi ý hái / cập bến / bắt cá, "Thủy quái!" + viền tím, "Hết hơi!".
HUD tối: đồng hồ ca, thu ca, tiền, uy tín, điểm, món và thanh kiên nhẫn từng bàn (dưới 25 % đổi đỏ), tiến độ bếp / món chín, món trên tay, kho khả dụng.

## Luật tóm tắt (số chuẩn Ticket-02)

- **Sáng (180 s):** oxy cơ sở 30 s, dưới nước −1/tick, mặt nước +6/tick; oxy 0 thì mất 1 Máu mỗi 60 tick. Giỏ 12 ô. Hái ở mặt nước (≤ 2 m, mọc lại 20 s): điên điển N1/N2, bông súng N3/N4, kèo nèo N5/N6. Bắt cá dưới nước (≤ 2 m, hồi 0.5 s): cá linh ×3, cá lóc ×1, cá kèo ×2. 8 đàn đầu ca, bơi 1.5 m/s, sinh thêm mỗi 6 s (trần 12).
- **Cá Sấu Năm Chèo** (d ≥ 10): M1 tuần tra [60,24]↔[64,24], M2 từ Ngày 3 [85,18]↔[89,18]; đuổi khi người chơi sâu và cách ≤ 10 m. Chạm: −1 Máu, rơi `floor(n/2)` món (LIFO), bất tử 1.5 s. Hết Máu thì ngất, quán tối mở với kho rỗng.
- **Tối (180 s):** 2 bếp, 4 bàn, 6 món; khách đến tick 120 rồi mỗi 15 s, chỉ gọi món trong kế hoạch Ngày; kiên nhẫn 60 s, ăn 10 s; boa `floor(20 % giá)` nếu còn ≥ 50 % kiên nhẫn (+0.2 uy tín); khách bỏ đi −0.5 uy tín; uy tín kẹp [0, 5].
- **Shop:** Bình oxy 200 → 45 s, 400 → 60 s · Áo phao 250 → 4 Máu, 500 → 5 Máu. Trừ `money`, giữ `earned`; có hiệu lực từ Ngày kế. Shop tự đóng sau 10 s.

| Món | Công thức | Nấu | Giá |
|---|---|---|---|
| Cá lóc nướng trui | cá lóc ×1 | 6 s | 60 |
| Gỏi bông súng | bông súng ×2 | 4 s | 40 |
| Lẩu cá linh bông điên điển | cá linh ×3 + điên điển ×1 | 10 s | 120 |
| Canh chua cá lóc bông điên điển | cá lóc ×1 + điên điển ×1 | 8 s | 90 |
| Cá kèo nướng muối ớt | cá kèo ×2 | 6 s | 70 |
| Lẩu mắm miền Tây | cá linh ×2 + cá kèo ×1 + kèo nèo ×1 + điên điển ×1 | 12 s | 200 |

## Cách tính điểm

`score = earned + 100 × floor(reputation)`. `earned` là tổng thu cả lượt (nghìn đồng, gồm tiền món và boa; mua nâng cấp không làm giảm). Điểm có ở mọi snapshot và dòng `end`.

## Hợp đồng tích hợp

File kho, sự kiện, giao diện sim ↔ UI và phần thêm của v1.1 (mode day, pause, Shop): [`docs/contracts/README.md`](docs/contracts/README.md).

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `chonoi/sim/gather.py`, `fish.py`, `monsters.py` | buổi sáng, cá bơi/sinh, Cá Sấu |
| `chonoi/sim/quan.py` | buổi tối |
| `chonoi/sim/day.py` | vòng ngày, Shop, nâng cấp |
| `chonoi/runner.py` | vòng tick, pause, ba bộ đếm tick |
| `chonoi/scenario.py`, `chonoi/contract.py` | kiểm fixture / tuning (sai → mã 2) |
| `chonoi/web/index.html`, `chonoi/live.py` | cửa sổ chơi: menu, intro, pause, HUD, Shop |
| `tests/` | smoke hộp đen + test luật P1/P2 |
| `docs/` | hợp đồng, kế hoạch, kiểm chứng, bằng chứng, clarify, nhật ký AI, retro |

## Mở rộng

Chưa làm mở rộng nào ở Phase 2 (ưu tiên lõi). `extensions` chưa khai trong manifest.

## Sáng tạo của nhóm

Bảng màu theo PRD: nước phù sa, trời hồng buổi sớm, đèn dây vàng ở nhà bè; tên món / nguyên liệu tiếng Việt trên HUD. Chỉ là lớp hiển thị của `chonoi/web/`, không đụng sim nên headless giữ nguyên (bằng chứng: `docs/proof/phase-2/unittest.txt`).
