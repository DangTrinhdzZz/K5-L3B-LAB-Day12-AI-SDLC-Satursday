"""Test Phase 3 (contract v1.2, Ticket-03): kho cá thể, độ tươi, ươn, giữ chỗ theo id, giá theo tươi, bàn giao."""

import json
import unittest

from helpers import Workdir, events, frames, id_kind, items, kinds_of, read_jsonl, run_headless, snapshots, write_json

G_QUIET = {"random_fish": False, "monsters": [], "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [99, 0]}]}
C1 = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}


def run(w, mode, sc, inputs=None, ticks=10, every=1, extra=(), out="o.jsonl"):
    args = ["--mode", mode, "--seed", "1", "--ticks", str(ticks), "--scenario", write_json(w.path("sc.json"), sc),
            "--snapshot-every", str(every), "--out", w.path(out), *extra]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(err)
    return read_jsonl(w.path(out))


def at(rows, tick):
    return [r for r in snapshots(rows) if r["tick"] == tick][-1]


class GatherFreshness(unittest.TestCase):
    def test_new_items_get_ids_in_order_and_full_fresh(self):
        with Workdir() as w:
            sc = {"gather": dict(G_QUIET, player={"pos": [20, 10]}, hold=items("bong_sung"),
                                 fish=[{"id": "F1", "kind": "ca_linh", "pos": [21, 10]}])}
            rows = run(w, "gather", sc, [{"tick": 0, "catch": True}], ticks=2)
            s1 = at(rows, 1)
            self.assertEqual(id_kind(s1["hold"]), [("I1", "bong_sung"), ("I2", "ca_linh"), ("I3", "ca_linh"),
                                                   ("I4", "ca_linh")])
            self.assertEqual([it["fresh"] for it in s1["hold"][1:]], [100, 100, 100], "hàng mới chưa hao ở bước bắt")
            self.assertAlmostEqual(at(rows, 2)["hold"][1]["fresh"], 100 - 0.5 / 60, places=3)

    def test_hold_decays_half_point_per_second(self):
        with Workdir() as w:
            rows = run(w, "gather", {"gather": dict(G_QUIET, hold=items("ca_loc", fresh=80))}, ticks=120, every=60)
            self.assertAlmostEqual(at(rows, 120)["hold"][0]["fresh"], 79.0, places=2)

    def test_spoiled_once_and_still_takes_a_slot(self):
        with Workdir() as w:
            rows = run(w, "gather", {"gather": dict(G_QUIET, hold=items("ca_linh", "ca_loc", fresh=31))},
                       ticks=200, every=50)
            sp = events(rows, "spoiled")
            self.assertEqual([e["data"] for e in sp], [{"item_id": "I1", "kind": "ca_linh", "location": "hold"},
                                                       {"item_id": "I2", "kind": "ca_loc", "location": "hold"}])
            self.assertEqual(sp[0]["tick"], sp[1]["tick"], "cùng vượt ngưỡng thì phát cùng tick, theo id")
            last = snapshots(rows)[-1]
            self.assertEqual(last["hold_count"], 2)
            self.assertTrue(all(it["fresh"] < 30 for it in last["hold"]))

    def test_old_count_hold_rejected(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"hold": ["ca_loc"]}})
            code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc,
                                   "--out", w.path("o.jsonl"))
            self.assertEqual(code, 2)


class Handover(unittest.TestCase):
    def test_file_handover_keeps_id_kind_fresh(self):
        """Smoke bàn giao Ticket-03: cập bến ở frame 0, quán đọc file với --ticks 0."""
        with Workdir() as w:
            kho = w.path("kho.json")
            run(w, "gather", {"gather": dict(G_QUIET, hold=items("ca_linh"))}, [{"tick": 0, "interact": True}],
                ticks=1, extra=("--inventory-out", kho))
            with open(kho, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(id_kind(saved["items"]), [("I1", "ca_linh")])
            self.assertEqual(saved["items"][0]["fresh"], 100 - 0.5 / 60, "file giữ đủ độ chính xác")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", kho,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            stock = snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"]
            self.assertEqual(id_kind(stock), [("I1", "ca_linh")])
            self.assertAlmostEqual(stock[0]["fresh"], saved["items"][0]["fresh"], places=2)

    def test_day_handover_same_tick_no_extra_decay(self):
        with Workdir() as w:
            rows = run(w, "day", {"gather": dict(G_QUIET, hold=items("ca_loc", "bong_sung"))},
                       [{"tick": 0, "interact": True}], ticks=2)
            s1 = at(rows, 1)
            self.assertEqual(s1["phase"], "quan")
            self.assertEqual(id_kind(s1["stock"]), [("I1", "ca_loc"), ("I2", "bong_sung")])
            self.assertAlmostEqual(s1["stock"][0]["fresh"], 100 - 0.5 / 60, places=3)
            self.assertAlmostEqual(at(rows, 2)["stock"][0]["fresh"], 100 - 0.5 / 60 - 0.25 / 60, places=2)

    def test_day2_template_hold_gets_new_ids(self):
        sc = {"gather": dict(G_QUIET, hold=items("ca_loc", "bong_sung")),
              "quan": {"time_left_ticks": 1, "random_customers": False}}
        with Workdir() as w:
            rows = run(w, "day", sc, [{"tick": 0, "interact": True}, {"tick": 2, "shop_done": True}],
                       ticks=4, extra=("--days", "2"))
            s3 = at(rows, 3)
            self.assertEqual((s3["day"], s3["phase"]), (2, "gather"))
            self.assertEqual(id_kind(s3["hold"]), [("I3", "ca_loc"), ("I4", "bong_sung")])
            self.assertEqual([it["fresh"] for it in s3["hold"]], [100, 100])


class QuanFreshness(unittest.TestCase):
    def test_stock_decays_quarter_point_per_second(self):
        with Workdir() as w:
            rows = run(w, "quan", {"quan": {"stock": items("ca_loc", fresh=50), "random_customers": False}},
                       ticks=240, every=240)
            self.assertAlmostEqual(at(rows, 240)["stock"][0]["fresh"], 49.0, places=2)

    def test_spoiled_items_not_cookable(self):
        with Workdir() as w:
            rows = run(w, "quan", {"quan": {"stock": items("ca_loc", "bong_sung", "bong_sung", fresh=10)}},
                       ticks=1200, every=200)
            self.assertGreaterEqual(len(events(rows, "no_dish")), 1)
            self.assertEqual(events(rows, "customer_arrived"), [])

    def test_reserved_item_spoils_then_rereserve(self):
        stock = items("ca_loc", fresh=30.1) + items("ca_loc", fresh=80, start=2)
        with Workdir() as w:
            rows = run(w, "quan", {"quan": {"stock": stock, "customers": [dict(C1, reserved=["I1"])],
                                            "random_customers": False}}, ticks=40, every=40)
            sp = events(rows, "spoiled")
            self.assertEqual([e["data"]["item_id"] for e in sp], ["I1"])
            self.assertEqual(sp[0]["data"]["location"], "stock")
            c = at(rows, 40)["customers"][0]
            self.assertEqual((c["order_status"], c["reserved"]), ("reserved", ["I2"]))

    def test_reserved_item_spoils_not_enough_unfulfillable(self):
        with Workdir() as w:
            rows = run(w, "quan", {"quan": {"stock": items("ca_loc", fresh=30.1),
                                            "customers": [dict(C1, reserved=["I1"])], "random_customers": False}},
                       ticks=40, every=40)
            c = at(rows, 40)["customers"][0]
            self.assertEqual((c["order_status"], c["reserved"], c["state"]), ("unfulfillable", [], "waiting"))
            self.assertEqual(at(rows, 40)["stock"][0]["id"], "I1", "hàng ươn vẫn ở trong kho")

    def test_price_locked_by_average_fresh_and_tip_on_locked_price(self):
        rec_stock = items("ca_linh", "ca_linh", "ca_linh", fresh=90) + items("bong_dien_dien", fresh=70, start=4)
        c = {"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien"}
        with Workdir() as w:
            rows = run(w, "quan", {"quan": {"player": {"pos": [2, 7]}, "stock": rec_stock, "customers": [c],
                                            "random_customers": False}}, [{"tick": 0, "interact": True}], ticks=2)
            cs = events(rows, "cook_started")[0]["data"]
            # trung bình fresh sau 1 tick = 85 - 1/240 -> floor(120 × 0.849958…) = 101
            self.assertEqual(cs["base_price"], 101)
            self.assertEqual(id_kind(cs["items"]), [("I4", "bong_dien_dien"), ("I1", "ca_linh"), ("I2", "ca_linh"),
                                                    ("I3", "ca_linh")])
            self.assertEqual(at(rows, 1)["stoves"][0]["dish"]["base_price"], 101)
        hand = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 58}
        with Workdir() as w:
            rows = run(w, "quan", {"quan": {"player": {"pos": [9, 3]}, "hand": hand, "random_customers": False,
                                            "customers": [dict(C1, order_status="assigned", reserved=[], base_price=58)]}},
                       [{"tick": 0, "interact": True}], ticks=2)
            self.assertEqual(events(rows, "served")[0]["data"]["tip"], 11)  # floor(58 × 0.2)

    def test_quan_snapshot_reserved_is_id_list(self):
        with Workdir() as w:
            rows = run(w, "quan", {"quan": {"stock": items("ca_loc"), "customers": [dict(C1, reserved=["I1"])],
                                            "random_customers": False}}, ticks=0)
            s = snapshots(rows)[0]
            self.assertEqual(s["customers"][0]["reserved"], ["I1"])
            self.assertEqual(kinds_of(s["stock"]), ["ca_loc"])


if __name__ == "__main__":
    unittest.main()
