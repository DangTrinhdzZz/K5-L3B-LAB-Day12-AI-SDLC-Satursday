"""Fixture quán mâu thuẫn -> mã 2, trước khi ghi đầu ra (PRD-0 mục D)."""

import os
import unittest

from helpers import Workdir, items, run_headless, write_json

C1 = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
HAND = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
ASSIGNED = dict(C1, order_status="assigned", reserved=[], base_price=60)

BAD = {
    "món ngoài menu": {"customers": [dict(C1, dish_id="pho_bo")]},
    "trường lạ ở khách": {"customers": [dict(C1, mood="vui")]},
    "id bếp không tồn tại": {"stoves": [{"id": "B9", "state": "idle"}]},
    "id bàn không tồn tại": {"tables": [{"id": "T9", "pos": [1, 1]}]},
    "giữ khác công thức": {"stock": items("ca_loc", "ca_loc"), "customers": [dict(C1, reserved=["I1", "I2"])]},
    "giữ sai loại": {"stock": items("bong_sung"), "customers": [dict(C1, reserved=["I1"])]},
    "giữ id không có trong kho": {"stock": items("ca_loc"), "customers": [dict(C1, reserved=["I9"])]},
    "giữ cá thể đã ươn": {"stock": items("ca_loc", fresh=10), "customers": [dict(C1, reserved=["I1"])]},
    "hai đơn giữ chung cá thể": {"stock": items("ca_loc"), "customers": [dict(C1, reserved=["I1"]),
                                                                       dict(C1, id="C2", table_id="T2", reserved=["I1"])]},
    "id cá thể trùng trong kho": {"stock": items("ca_loc") + items("bong_sung")},
    "kho đếm kiểu cũ": {"stock": {"ca_loc": 1}},
    "assigned không có món": {"customers": [ASSIGNED]},
    "bếp và tay giữ cùng đơn": {"customers": [ASSIGNED], "hand": HAND,
                                "stoves": [{"id": "B1", "state": "ready", "dish": HAND}]},
    "món không khớp đơn": {"customers": [ASSIGNED], "hand": dict(HAND, dish_id="goi_bong_sung")},
    "bếp cooking timer 0": {"customers": [ASSIGNED],
                            "stoves": [{"id": "B1", "state": "cooking", "dish": HAND, "cook_ticks_left": 0}]},
    "eating thiếu tip": {"customers": [dict(C1, state="eating", order_status="served", reserved=[],
                                            eat_ticks_left=10, base_price=60)]},
    "served mà còn chờ": {"customers": [dict(C1, order_status="served", reserved=[], base_price=60, tip=0)]},
    "kiên nhẫn âm": {"customers": [dict(C1, patience_ticks_left=-1)], "stock": items("ca_loc")},
    "kiên nhẫn vượt đầy": {"customers": [dict(C1, patience_ticks_left=99999)], "stock": items("ca_loc")},
    "uy tín ngoài dải": {"reputation": 7},
    "random_customers sai kiểu": {"random_customers": "no"},
    "nguyên liệu lạ trong kho": {"stock": items("ca_la_lung")},
}


class QuanFixture(unittest.TestCase):
    def test_contradictions_exit_2_before_output(self):
        for name, block in BAD.items():
            with self.subTest(name), Workdir() as w:
                out = w.path("q.jsonl")
                sc = write_json(w.path("sc.json"), {"quan": block})
                code, _ = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5", "--scenario", sc, "--out", out)
                self.assertEqual(code, 2, name)
                self.assertFalse(os.path.exists(out), name)

    def test_valid_fixtures_run(self):
        good = {
            "đơn reserved đủ kho": {"stock": items("ca_loc"), "customers": [dict(C1, reserved=["I1"])]},
            "món trên tay": {"customers": [ASSIGNED], "hand": HAND},
            "món trên bếp": {"customers": [ASSIGNED],
                             "stoves": [{"id": "B1", "state": "cooking", "dish": HAND, "cook_ticks_left": 30}]},
            "unfulfillable": {"customers": [dict(C1, order_status="unfulfillable", reserved=[])]},
        }
        for name, block in good.items():
            with self.subTest(name), Workdir() as w:
                sc = write_json(w.path("sc.json"), {"quan": block})
                code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "5", "--scenario", sc,
                                         "--out", w.path("q.jsonl"))
                self.assertEqual(code, 0, f"{name}: {err}")


if __name__ == "__main__":
    unittest.main()
