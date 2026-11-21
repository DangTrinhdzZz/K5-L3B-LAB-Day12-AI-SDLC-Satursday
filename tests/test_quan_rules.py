"""Test luật buổi tối (quan) của nhóm — hộp đen qua headless_cmd (PRD-0 mục F "Quán")."""

import json
import unittest

from helpers import Workdir, events, frames, id_kind, items, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def run_quan(w, block, inputs=None, ticks=10, every=1, seed=1, out="q.jsonl"):
    sc = write_json(w.path("sc.json"), {"quan": block})
    args = ["--mode", "quan", "--seed", str(seed), "--ticks", str(ticks), "--scenario", sc,
            "--snapshot-every", str(every), "--out", w.path(out)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(err)
    return read_jsonl(w.path(out))


def by_tick(rows):
    return {r["tick"]: r for r in snapshots(rows)}


C1 = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}


class Kitchen(unittest.TestCase):
    def test_cook_then_ready_then_pick(self):
        t = tuning()
        cook = t["menu"]["ca_loc_nuong_trui"]["cook_s"] * 60
        with Workdir() as w:
            rows = run_quan(w, {"player": {"pos": [2, 7]}, "stock": items("ca_loc"), "customers": [dict(C1)],
                                "random_customers": False},
                            inputs=[{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                                    {"tick": cook + 1, "interact": True}], ticks=cook + 3, every=1)
            cs = events(rows, "cook_started")
            self.assertEqual(len(cs), 1)
            self.assertEqual(cs[0]["tick"], 1)
            # v1.2: items là mảng cá thể; giá chốt theo trung bình fresh (100 - 1/240 sau 1 tick) -> floor = 59
            d = cs[0]["data"]
            self.assertEqual((d["stove_id"], d["order_id"], d["dish_id"]), ("B1", "C1", "ca_loc_nuong_trui"))
            self.assertEqual(id_kind(d["items"]), [("I1", "ca_loc")])
            self.assertEqual(d["base_price"], 59)
            s1 = by_tick(rows)[1]
            self.assertEqual(s1["stock"], [])
            self.assertEqual(s1["customers"][0]["order_status"], "assigned")
            self.assertEqual(s1["stoves"][0]["state"], "cooking")
            ready = events(rows, "dish_ready")
            self.assertEqual(ready[0]["tick"], 1 + cook)
            picked = events(rows, "dish_picked")
            self.assertEqual(picked[0]["tick"], cook + 2)
            s = by_tick(rows)[cook + 2]
            self.assertEqual(s["hand"], {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 59})
            self.assertEqual(s["stoves"][0]["state"], "idle")

    def test_idle_stove_without_order_does_nothing(self):
        with Workdir() as w:
            rows = run_quan(w, {"player": {"pos": [2, 7]}, "stock": items("ca_loc"), "random_customers": False},
                            inputs=[{"tick": 0, "interact": True}], ticks=3)
            self.assertEqual([r for r in rows if r["type"] == "event"], [])


class Serve(unittest.TestCase):
    def _served_block(self):
        c = dict(C1, order_status="assigned", reserved=[], base_price=60)
        return {"player": {"pos": [9, 3]}, "customers": [c], "random_customers": False,
                "hand": {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}}

    def test_serve_full_patience_gets_tip_then_pays(self):
        t = tuning()
        eat = t["quan"]["eat_s"] * 60
        with Workdir() as w:
            rows = run_quan(w, self._served_block(), inputs=[{"tick": 0, "interact": True}], ticks=eat + 5, every=10)
            sv = events(rows, "served")
            self.assertEqual(len(sv), 1)
            self.assertEqual(sv[0]["tick"], 1)
            self.assertEqual(sv[0]["data"]["tip"], 12)
            self.assertEqual(sv[0]["data"]["base_price"], 60)
            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1)
            self.assertEqual(paid[0]["tick"], 1 + eat)
            self.assertEqual(paid[0]["data"]["amount"], 72)
            self.assertEqual(paid[0]["data"]["reason"], "finished_eating")
            last = snapshots(rows)[-1]
            self.assertEqual(last["customers"], [])
            self.assertEqual(last["tables"][0]["customer_id"], None)
            self.assertAlmostEqual(last["reputation"], 3.2, places=2)

    def test_empty_hand_at_table_is_skipped(self):
        with Workdir() as w:
            rows = run_quan(w, {"player": {"pos": [9, 3]}, "stock": items("ca_loc"), "customers": [dict(C1)],
                                "random_customers": False},
                            inputs=[{"tick": 0, "interact": True}], ticks=3)
            self.assertEqual(events(rows, "served"), [])

    def test_tip_when_patience_ratio_exactly_half(self):
        # PRD-0 F: boa nếu tỷ lệ kiên nhẫn còn lại sau bước 1 ĐẠT tip_min_patience_ratio (>=)
        with Workdir() as w:
            b = self._served_block()
            b["customers"][0]["patience_ticks_left"] = 1801  # sau bước 1 còn 1800/3600 = 0.5
            rows = run_quan(w, b, inputs=[{"tick": 0, "interact": True}], ticks=2)
            self.assertEqual(events(rows, "served")[0]["data"]["tip"], 12)

    def test_tip_reputation_clamped_to_max(self):
        # PRD-0 F: boa dương cộng tip_reputation khi thu tiền, kẹp uy tín theo tuning
        eat = tuning()["quan"]["eat_s"] * 60
        with Workdir() as w:
            b = dict(self._served_block(), reputation=5)
            rows = run_quan(w, b, inputs=[{"tick": 0, "interact": True}], ticks=eat + 5, every=100)
            self.assertEqual(len(events(rows, "paid")), 1)
            self.assertEqual(rows[-1]["reputation"], tuning()["quan"]["reputation_max"])

    def test_money_and_earned_include_tip(self):
        # PRD-0 E / Ticket-02: earned là tổng thu, gồm tiền món và boa
        eat = tuning()["quan"]["eat_s"] * 60
        with Workdir() as w:
            rows = run_quan(w, self._served_block(), inputs=[{"tick": 0, "interact": True}], ticks=eat + 5, every=100)
            paid = events(rows, "paid")[0]["data"]
            self.assertEqual(paid["amount"], 72)
            self.assertEqual((rows[-1]["money"], rows[-1]["earned"]), (72, 72))


class Customers(unittest.TestCase):
    def test_customer_arrives_at_first_tick(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": items("ca_loc", "ca_loc", "ca_loc")}, ticks=121, every=1)
            arrived = events(rows, "customer_arrived")
            self.assertEqual(len(arrived), 1)
            self.assertEqual(arrived[0]["tick"], tuning()["quan"]["first_customer_tick"])

    def test_patience_runs_out(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": items("ca_loc"), "random_customers": False,
                                "customers": [dict(C1, patience_ticks_left=5)]}, ticks=10)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["tick"], 5)
            self.assertEqual(left[0]["data"]["reason"], "patience")
            self.assertAlmostEqual(by_tick(rows)[5]["reputation"], 2.5, places=2)
            self.assertEqual(by_tick(rows)[5]["customers"], [])

    def test_customer_left_reports_updated_reputation(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": items("ca_loc"), "random_customers": False,
                                "customers": [dict(C1, patience_ticks_left=5)]}, ticks=10)
            left = events(rows, "customer_left")
            self.assertEqual(left[0]["data"]["reputation"], 2.5)
            self.assertEqual(by_tick(rows)[5]["reputation"], 2.5)

    def test_closing_customer_does_not_lose_reputation(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": items("ca_loc"), "random_customers": False,
                                "time_left_ticks": 3, "customers": [dict(C1)]}, ticks=10)
            left = events(rows, "customer_left")
            self.assertEqual(left[0]["data"]["reason"], "closing")
            self.assertEqual(left[0]["data"]["reputation"], 3.0)
            self.assertEqual(events(rows, "quan_end")[0]["data"]["reputation"], 3.0)

    def test_missing_reserved_is_filled_from_recipe(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": items("ca_loc", "ca_loc"), "random_customers": False,
                                "customers": [dict(C1)]}, ticks=0)
            self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"], ["I1"])

    def test_no_dish_when_stock_empty(self):
        with Workdir() as w:
            rows = run_quan(w, {}, ticks=1200, every=100)
            self.assertGreaterEqual(len(events(rows, "no_dish")), 1)
            self.assertEqual(events(rows, "customer_arrived"), [])

    def test_customer_arrives_and_reserves_recipe(self):
        with Workdir() as w:
            rows = run_quan(w, {"stock": items(*["ca_loc"] * 5, *["bong_sung"] * 4, *["ca_linh"] * 3, "bong_dien_dien")},
                            ticks=1200, every=100)
            arr = events(rows, "customer_arrived")
            self.assertGreaterEqual(len(arr), 1)
            d = arr[0]["data"]
            self.assertEqual(d["table_id"], "T1")
            self.assertIn(d["dish_id"], tuning()["menu"])


class Shift(unittest.TestCase):
    def test_quan_end_on_time(self):
        with Workdir() as w:
            rows = run_quan(w, {"time_left_ticks": 3}, ticks=50)
            qe = events(rows, "quan_end")
            self.assertEqual(len(qe), 1)
            self.assertEqual(qe[0]["tick"], 3)
            self.assertEqual(rows[-1]["reason"], "time")
            self.assertEqual(rows[-1]["score"], 0 + 100 * 3)

    def test_eating_customer_pays_at_closing(self):
        c = dict(C1, state="eating", order_status="served", reserved=[], eat_ticks_left=500, base_price=60, tip=0)
        with Workdir() as w:
            rows = run_quan(w, {"time_left_ticks": 2, "customers": [c], "random_customers": False}, ticks=10)
            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1)
            self.assertEqual(paid[0]["data"]["reason"], "closing")
            self.assertEqual(paid[0]["tick"], 2)

    def test_quan_deterministic_bytes(self):
        block = {"stock": items(*["ca_loc"] * 3, *["bong_sung"] * 4, *["ca_linh"] * 3, "bong_dien_dien")}
        with Workdir() as w:
            run_quan(w, block, inputs=[{"tick": 0, "move": [-1, 1]}], ticks=2500, every=7, seed=9, out="a.jsonl")
            run_quan(w, block, inputs=[{"tick": 0, "move": [-1, 1]}], ticks=2500, every=7, seed=9, out="b.jsonl")
            with open(w.path("a.jsonl"), "rb") as a, open(w.path("b.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
