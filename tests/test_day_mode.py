"""Test mode day, Shop, nâng cấp và pause (Ticket-02 mục 2, 4.2–4.5) — hộp đen qua headless_cmd."""

import json
import time
import unittest

from helpers import Workdir, events, frames, id_kind, items, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def run_day(w, scenario=None, inputs=None, ticks=22200, days=None, every=10, seed=1):
    args = ["--mode", "day", "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every),
            "--out", w.path("d.jsonl")]
    if scenario is not None:
        args += ["--scenario", write_json(w.path("sc.json"), scenario)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if days is not None:
        args += ["--days", str(days)]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(err)
    return read_jsonl(w.path("d.jsonl"))


def names(rows):
    return [(r["tick"], r["phase"], r["name"]) for r in rows if r["type"] == "event"
            and r["name"] in ("day_start", "day_plan", "phase_start", "gather_end", "quan_end", "shop_end")]


# cập bến ngay tick 0, ca quán 1 tick -> vào Shop ở tick 2
FAST = {"gather": {"random_fish": False}, "quan": {"time_left_ticks": 1, "random_customers": False}}


class DayFlow(unittest.TestCase):
    def test_one_full_day_phases_and_end(self):
        t = tuning()
        g, q, s = (int(t["gather"]["duration_s"] * 60), int(t["quan"]["duration_s"] * 60), t["shop"]["max_ticks"])
        with Workdir() as w:
            start = time.time()
            rows = run_day(w, ticks=22200)
            self.assertLess(time.time() - start, 20, "một Ngày headless phải chạy <= 20 s")
            self.assertEqual(names(rows), [
                (0, "gather", "day_start"), (0, "gather", "day_plan"), (0, "gather", "phase_start"),
                (g, "gather", "gather_end"), (g, "quan", "phase_start"),
                (g + q, "quan", "quan_end"), (g + q, "shop", "phase_start"),
                (g + q + s, "shop", "shop_end")])
            self.assertEqual(rows[0]["type"], "event")
            self.assertEqual(rows[0]["day"], 1)
            plan = events(rows, "day_plan")[0]["data"]
            self.assertEqual(plan, {"dishes": t["day_plan"][0]["dishes"], "ingredients": t["day_plan"][0]["ingredients"]})
            snap_q = [r for r in snapshots(rows) if r["tick"] == g][0]
            self.assertEqual((snap_q["phase"], snap_q["phase_tick"]), ("quan", 0))
            end = rows[-1]
            self.assertEqual((end["reason"], end["days_completed"], end["ticks"]), ("days_complete", 1, g + q + s))
            for r in snapshots(rows):
                for key in ("day", "day_plan", "upgrades", "active_upgrades"):
                    self.assertIn(key, r)

    def test_scenario_example_docks_and_opens_quan_with_hold(self):
        sc = {"day": {"money": 200, "earned": 200},
              "gather": {"hold": items("ca_loc", "bong_sung", "bong_sung"), "random_fish": False}}
        with Workdir() as w:
            rows = run_day(w, sc, inputs=[{"tick": 0, "interact": True}], ticks=3, every=1)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "docked")
            s = [r for r in snapshots(rows) if r["tick"] == 1][0]
            self.assertEqual(s["phase"], "quan")
            self.assertEqual(id_kind(s["stock"]), [("I1", "ca_loc"), ("I2", "bong_sung"), ("I3", "bong_sung")])
            self.assertEqual((s["money"], s["earned"]), (200, 200))

    def test_shop_done_closes_and_next_day_starts(self):
        with Workdir() as w:
            rows = run_day(w, FAST, inputs=[{"tick": 0, "interact": True}, {"tick": 2, "shop_done": True}],
                           days=2, ticks=6, every=1)
            self.assertEqual(events(rows, "shop_end")[0]["data"], {"reason": "done"})
            self.assertEqual(events(rows, "shop_end")[0]["tick"], 3)
            starts = events(rows, "day_start")
            self.assertEqual([(e["tick"], e["day"]) for e in starts], [(0, 1), (3, 2)])
            self.assertEqual(events(rows, "day_plan")[1]["data"]["dishes"], tuning()["day_plan"][1]["dishes"])

    def test_buy_hp_applies_next_day(self):
        sc = dict(FAST, day={"money": 300, "earned": 300})
        with Workdir() as w:
            rows = run_day(w, sc, inputs=[{"tick": 0, "interact": True}, {"tick": 2, "buy": "hp"},
                                          {"tick": 3, "shop_done": True}], days=2, ticks=6, every=1)
            b = events(rows, "bought")
            self.assertEqual(b[0]["data"], {"upgrade": "hp", "level": 1, "price": 250, "money": 50})
            s3 = [r for r in snapshots(rows) if r["tick"] == 3][0]
            self.assertEqual(s3["phase"], "shop")
            self.assertEqual((s3["upgrades"], s3["active_upgrades"]), ({"hp": 1}, {}), "cấp mới hiện ngay, áp từ Ngày kế")
            self.assertEqual((s3["money"], s3["earned"]), (50, 300), "mua trừ money, giữ earned")
            s4 = [r for r in snapshots(rows) if r["tick"] == 4][0]
            self.assertEqual((s4["day"], s4["active_upgrades"]), (2, {"hp": 1}))
            self.assertEqual((s4["player"]["hp_max"], s4["player"]["hp"]), (4, 4))

    def test_buy_oxygen_raises_oxygen_max(self):
        sc = dict(FAST, day={"money": 500, "earned": 500})
        with Workdir() as w:
            rows = run_day(w, sc, inputs=[{"tick": 0, "interact": True}, {"tick": 2, "buy": "oxygen"},
                                          {"tick": 3, "shop_done": True}], days=2, ticks=5, every=1)
            s = [r for r in snapshots(rows) if r["tick"] == 4][0]
            self.assertEqual(s["player"]["oxygen_max_ticks"], 45 * 60)

    def test_buy_failed_reasons(self):
        sc = dict(FAST, day={"money": 100, "earned": 100, "upgrades": {"oxygen": 2}})
        with Workdir() as w:
            rows = run_day(w, sc, inputs=[{"tick": 0, "interact": True}, {"tick": 2, "buy": "hp"},
                                          {"tick": 3, "buy": "oxygen"}, {"tick": 4, "buy": "weapon"}], ticks=6)
            got = [e["data"] for e in events(rows, "buy_failed")]
            self.assertEqual(got, [{"action": "hp", "reason": "funds"}, {"action": "oxygen", "reason": "max_level"},
                                   {"action": "weapon", "reason": "unknown"}])
            self.assertEqual(rows[-1]["money"], 100)

    def test_faint_still_opens_quan_with_empty_stock(self):
        sc = {"gather": {"random_fish": False, "hold": items("ca_loc", "bong_sung"), "player": {"pos": [60, 23], "hp": 1}}}
        with Workdir() as w:
            rows = run_day(w, sc, ticks=3, every=1)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["reason"], "fainted")
            s = [r for r in snapshots(rows) if r["phase"] == "quan"][0]
            self.assertEqual(s["stock"], [])

    def test_day_deterministic_bytes(self):
        with Workdir() as w:
            a = json.dumps(run_day(w, ticks=12000, every=37, seed=3))
            b = json.dumps(run_day(w, ticks=12000, every=37, seed=3))
            self.assertEqual(a, b)

    def test_buy_with_exact_money(self):
        # Ticket-02 "Shop và nâng cấp": đủ đúng giá vẫn mua được
        sc = dict(FAST, day={"money": 250, "earned": 250})
        with Workdir() as w:
            rows = run_day(w, sc, inputs=[{"tick": 0, "interact": True}, {"tick": 2, "buy": "hp"}], ticks=4, every=1)
            self.assertEqual(events(rows, "bought")[0]["data"], {"upgrade": "hp", "level": 1, "price": 250, "money": 0})
            self.assertEqual(events(rows, "buy_failed"), [])


class Pause(unittest.TestCase):
    def test_pause_freezes_gameplay_counters(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False, "player": {"pos": [50, 5]}}})
            inp = write_json(w.path("in.json"), frames({"tick": 0, "move": [1, 0]}, {"tick": 5, "pause": True},
                                                       {"tick": 6, "pause": False}, {"tick": 9, "interact": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "20", "--scenario", sc, "--inputs", inp,
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual([e["tick"] for e in events(rows, "paused")], [6])
            s = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual((s[6]["state"], s[6]["sim_tick"]), ("paused", 5))
            self.assertEqual((s[15]["sim_tick"], s[15]["phase_tick"]), (5, 5))
            self.assertEqual(s[15]["time_left_ticks"], s[6]["time_left_ticks"])
            self.assertEqual(s[15]["player"]["pos"], s[6]["player"]["pos"])
            self.assertEqual(rows[-1]["ticks"], 20)

    def test_resumed_step_runs_gameplay(self):
        # Ticket-02 4.2: cạnh lên tiếp theo phát resumed, chạy gameplay ngay trong bước đó.
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False}})
            inp = write_json(w.path("in.json"), frames({"tick": 2, "pause": True}, {"tick": 3, "pause": False},
                                                       {"tick": 4, "pause": True}))
            code, err = run_headless("--mode", "gather", "--seed", "1", "--ticks", "6", "--scenario", sc, "--inputs", inp,
                                     "--snapshot-every", "1", "--out", w.path("o.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
            self.assertEqual([e["tick"] for e in events(rows, "resumed")], [5])
            s = {r["tick"]: r for r in snapshots(rows)}
            self.assertEqual((s[4]["state"], s[4]["sim_tick"]), ("paused", 2))
            self.assertEqual((s[5]["state"], s[5]["sim_tick"], s[5]["phase_tick"]), ("playing", 3, 3))
            self.assertEqual(rows[-1]["sim_tick"], 4)


class DayInputErrors(unittest.TestCase):
    def test_bad_day_inputs_exit_2(self):
        bad = [{"quan": {"stock": items("ca_loc")}}, {"quan": {"reputation": 4}},
               {"day": {"money": 300, "earned": 100}}, {"day": {"money": 50}},
               {"day": {"upgrades": {"hp": 3}}}, {"day": {"day_plan": [{"day": 1, "dishes": {"pho": 1}}]}},
               {"day": {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 1}, "ingredients": {"ca_loc": 2}}]}},
               {"day": {"coins": 1}}]
        with Workdir() as w:
            out = w.path("d.jsonl")
            for sc in bad:
                p = write_json(w.path("sc.json"), sc)
                code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "1", "--scenario", p, "--out", out)
                self.assertEqual(code, 2, sc)
            for extra in (["--days", "6"], ["--days", "0"]):
                self.assertEqual(run_headless("--mode", "day", "--seed", "1", "--ticks", "1", "--out", out, *extra)[0], 2)
            self.assertEqual(run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--days", "2",
                                          "--out", out)[0], 2)
            self.assertEqual(run_headless("--mode", "day", "--seed", "1", "--ticks", "1", "--inventory-out",
                                          w.path("k.json"), "--out", out)[0], 2)

    def test_day_plan_override_recomputes_ingredients(self):
        sc = {"day": {"day_plan": [{"day": 1, "dishes": {"ca_keo_nuong": 2}}]}}
        with Workdir() as w:
            rows = run_day(w, sc, ticks=0)
            self.assertEqual(events(rows, "day_plan")[0]["data"], {"dishes": {"ca_keo_nuong": 2},
                                                                   "ingredients": {"ca_keo": 4}})


if __name__ == "__main__":
    unittest.main()
