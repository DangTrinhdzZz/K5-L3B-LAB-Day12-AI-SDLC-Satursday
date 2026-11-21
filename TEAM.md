# TEAM

**Tên nhóm:** Satursday  **Số người:** 7  (khớp `team_size` trong `game.contract.json`; số người đã được giảng viên cho phép)

| Thành viên | GitHub handle | Module chính | Vai quy trình | Người dự phòng cho |
|---|---|---|---|---|
| Trần Tuấn Anh | Tanh0406 | `sim/*` (khung luật gather + quan), `docs/contracts` | Integrator | mọi lát |
| Đào Vũ Minh Khánh | iamdvmk | `sim/gather` lát 1 (oxy, ngạt) | QA lead | lát 2 |
| Nguyễn Đình Minh | MinhNGD76 | `sim/gather` lát 1 (Máu, ngất, giỏ) | Scrum/Release | lát 1 |
| … | … | `sim/gather` lát 2 (hái nút) | PO | lát 2 |
| Nguyễn Văn Anh Trung | FPT-Trungocsdiogee | `sim/gather` lát 2 (bắt cá) + pause (`runner.Session`) | Dev | lát 1 |
| … | … | `sim/quan` lát 3 (khách, kiên nhẫn) | Dev | lát 4 |
| Vũ Tuấn Đạt | datkunal | `sim/day` Shop + độ tươi (`chonoi/freshness.py`: giữ chỗ tươi nhất) | Dev (pair với Tanh0406) | lát 3 |

**Vai quy trình:** PO (đầu mối hỏi Anh Năm / giảng viên, giữ `docs/clarify.md`) · Integrator (giữ `docs/contracts/`, gắn tag) · QA lead (giữ bộ test, `docs/verification/`) · Scrum/Release (theo dõi mốc, standup).

## Thỏa thuận làm việc nhóm

- Kênh liên lạc: nhóm chat của lớp (Zalo/Messenger) + issue trên GitHub cho việc dài.
- Khi bất đồng về thiết kế: mỗi bên nói 2 phút, không xong thì Integrator quyết và ghi lý do vào `docs/clarify.md` hoặc ADR.
- Khi ai đó trễ hoặc vướng quá 10 phút: báo ngay trong kênh, người dự phòng (cột cuối) nhận hỗ trợ.
- Giờ standup giữa phase: phút 20 và phút 40 của mỗi phase, 2–3 phút, ghi `docs/standup.md`.
- Cách đọc code của nhau: mỗi người đọc lát kế bên trước khi đẩy; sửa luật phải kèm test.
- Cách làm việc với Git: commit nhỏ, `git pull --rebase` trước khi push thẳng `main`; chạy test trước khi đẩy; Integrator gắn tag `phase-n`.
