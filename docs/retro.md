# Retro nhóm

## Phase 2 (nhanh)
- Retro nhanh Phase 2 **không được ghi** trong giờ (cả nhóm dồn sức sửa lát và tích hợp). Hành động thực tế nhóm đã
  làm sau Phase 2, ghi lại ở đây để rà ở Phase 4: *mỗi người sửa lát của mình trên nhánh riêng, mở PR vào `Draft`,
  PR phải kèm test hồi quy.*

## Phase 3 (đổi schema kho)
- Trước khi đổi kho đếm → kho cá thể, Integrator gộp các PR đang mở (#5, #6) để không ai phải gỡ xung đột trên
  `gather.py`; schema, Lặn, Quán, day và toàn bộ fixture test đổi trong cùng một commit (ADR-0001) nên `Draft` không
  có lúc nào đỏ.

## Phase 4 (cuối)

### Rà lại hành động sau Phase 2
- **Đã làm:** 4 bạn (iamdvmk, MinhNGD76, BSFactor, FPT-Trungocsdiogee) sửa lát trên nhánh riêng, mỗi PR có test
  (PR #3–#10). Commit của mỗi người đứng đúng tài khoản GitHub.
- **Bản vá v1.0.1:** 10 lỗi luật còn lại: totoca6969 sửa 4 (khách đầu tiên, customer_left, đóng ca, khách theo kế
  hoạch), iamdvmk sửa ngưỡng ươn, Tanh0406 sửa 3 (boa 0.5, kẹp uy tín, tiền cộng boa) và 2 (Shop đúng giá, giữ chỗ
  tươi nhất) làm cặp cùng Vũ Tuấn Đạt (datkunal) trên cùng máy, ghi `Co-authored-by`.
- **Còn vướng:** lát quán (khách / kiên nhẫn / boa / tiền) và 2 lỗi độ tươi chưa có người nhận đúng hạn → cần người
  dự phòng (cột cuối `TEAM.md`) nhận sớm hơn. Lý do: lát quán phụ thuộc kho từ lát lặn nên bắt đầu muộn, và không ai theo dõi việc chưa có người nhận.

### Số liệu (từ `git log`, không tính commit merge)
| Tác giả | Số commit | Ghi chú |
|---|---|---|
| Tanh0406 | 12 | khung luật, contract v1.1–v1.3, tích hợp, tài liệu, phát hành |
| Dao Vu Minh Khanh (iamdvmk) | 7 | oxy / ngạt, cá bơi (phản xạ mép), tài liệu cá nhân |
| MinhNGD76 | 7 | Máu / ngất, Cá Sấu rơi hàng |
| FL.Trungocsdiogee (FPT-Trungocsdiogee) | 6 | bắt cá, pause, tài liệu cá nhân |
| BSFactor | 4 | hái nút, Cá Sấu phát hiện |
| (Hai Duong) | 9 | commit của starter giảng viên, không tính |

- Cách đọc code của nhau: PR vào `Draft`, người tích hợp gộp thử trên worktree riêng và chạy toàn bộ test trước khi merge.
- Token theo người: không đo được chính xác; công cụ và việc dùng AI theo người ghi ở `docs/ai-usage-log.md`.

### Một lần AI sai và cách nhóm phát hiện
- **PR #9:** commit sửa "số món rơi = floor(…)" có trong lịch sử, nhưng khi gộp `Draft` vào nhánh, phần sửa bị mất
  (xung đột với dòng kế bên của thay đổi kho v1.2). Phát hiện nhờ **test của chính PR** đỏ khi Integrator gộp thử;
  khôi phục ở commit `f94ef1c` (Co-authored-by tác giả PR).
- **Event `shop_end` mang sai số Ngày** (mang Ngày mới thay vì Ngày vừa đóng): lọt qua test Phase 2, lộ ra khi viết
  `soak_cmd` cần `results[].day` → sửa ở commit Phase 4 và thêm test `test_shop_end_carries_the_finished_day`.

### Điều tốt / điều cần sửa / hành động tiếp
- Tốt: hợp đồng kho và sự kiện chốt sớm (`docs/contracts/`), mọi PR có test, `Draft` luôn xanh; đổi schema kho (v1.2) trong một commit nên không ai phải gỡ xung đột lớn.
- Cần sửa: phân việc quán bị dồn cuối buổi; retro P2 bị bỏ qua; tag các phase gắn muộn hơn mốc giờ; gộp nhánh làm mất phần sửa (PR #9).
- Hành động tiếp (có người nhận): (1) mỗi PR chạy toàn bộ test sau khi gộp Draft — người mở PR — mọi PR; (2) gắn tag ngay khi hết phase — Integrator (Tanh0406) — mỗi mốc; (3) mỗi lát có người dự phòng nhận khi trễ 10 phút — Scrum — từ đầu phase.
- Nếu làm lại, đổi gì: chia lát quán ngay từ kickoff, ghi retro nhanh cuối mỗi phase, bật CI để test chạy tự động trên mỗi PR.
