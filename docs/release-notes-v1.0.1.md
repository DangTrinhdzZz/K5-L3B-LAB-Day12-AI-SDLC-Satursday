# Quán Ăn Chợ Nổi v1.0.1 — nhóm Satursday

Bản sửa lỗi cho v1.0.0. Gameplay, contract (**v1.3**), file kho và cách chạy giữ nguyên; chỉ sửa các luật chưa
đúng PRD-0 / Ticket-02 / Ticket-03.

## Cách chạy (Python 3.10+, không cài thêm gì)

```bash
git clone https://github.com/DangTrinhdzZz/K5-L3B-LAB-Day12-AI-SDLC-Satursday.git
cd K5-L3B-LAB-Day12-AI-SDLC-Satursday
python3 -m chonoi.live --mode day      # mở địa chỉ in ra (mặc định http://127.0.0.1:8000/)
```

Hoặc giải nén `quan-an-cho-noi-v1.0.1.zip` đính kèm Release, `cd` vào thư mục rồi chạy lệnh cuối ở trên.

## Đã sửa
| Phần | Luật đúng | PR |
|---|---|---|
| Quán | Khách đầu tiên đến đúng `first_customer_tick` | #15 |
| Quán | `customer_left.reputation` là uy tín sau khi trừ | #15 |
| Quán | Khách rời lúc đóng ca không bị trừ uy tín | #15 |
| Day | Khách chỉ gọi món thuộc kế hoạch Ngày | #15 |
| Gather | Cá Sấu chạm: rơi `floor(số đang mang × loss_ratio)` món | #13 |
| Độ tươi | Ươn khi `fresh < 30` (đúng 30 chưa ươn) | #11 |

## Lỗi đã biết
- Giữ chỗ chọn cá thể theo **id nhỏ nhất** thay vì **tươi nhất** (`Freshness.freshest()`, Ticket-03 mục 1): khách có
  thể giữ hàng cũ hơn nên giá chốt thấp hơn. Chưa sửa trong bản này.

## Kiểm chứng
`PYTHONPATH=tests:. python3 -m unittest discover -s tests` → Ran 134 tests, OK (skipped=1).

Chi tiết: [`CHANGELOG.md`](../CHANGELOG.md). Bản trước: [`release-notes-v1.0.0.md`](release-notes-v1.0.0.md).
