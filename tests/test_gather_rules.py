"""Test luật buổi sáng (gather) của nhóm — hộp đen qua headless_cmd (PRD-0 mục F "Gather")."""

import json
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning_gather():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]["gather"]


def run_gather(w, block, inputs=None, ticks=10, every=1, inv_out=None):
    sc = write_json(w.path("sc.json"), {"gather": block})
    args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--scenario", sc,
            "--snapshot-every", str(every), "--out", w.path("o.jsonl")]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    if inv_out:
        args += ["--inventory-out", inv_out]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(err)
    return read_jsonl(w.path("o.jsonl"))


def by_tick(rows):
    return {r["tick"]: r for r in snapshots(rows)}


class Oxygen(unittest.TestCase):
    def test_underwater_spends_one_tick_per_tick(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10]}, "random_fish": False}, ticks=30)
            omax = tuning_gather()["oxygen_max_s"] * 60
            self.assertEqual(by_tick(rows)[30]["player"]["oxygen_ticks"], omax - 30)

    def test_surface_refills_and_clamps(self):
        g = tuning_gather()
        omax = g["oxygen_max_s"] * 60
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0], "oxygen_ticks": 100}, "random_fish": False}, ticks=5)
            s = by_tick(rows)
            self.assertEqual(s[1]["player"]["oxygen_ticks"], 100 + g["oxygen_refill_per_tick"])
            self.assertTrue(s[1]["player"]["at_surface"])
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0], "oxygen_ticks": omax - 1}, "random_fish": False}, ticks=2)
            self.assertEqual(by_tick(rows)[2]["player"]["oxygen_ticks"], omax)

    def test_oxygen_empty_once_when_reaching_zero(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 5}, "random_fish": False}, ticks=20)
            ev = events(rows, "oxygen_empty")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 5)
            self.assertEqual(ev[0]["data"], {"oxygen_ticks": 0})

    def test_dive_event_when_leaving_surface(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 0]}, "random_fish": False},
                              inputs=[{"tick": 0, "move": [0, 1]}], ticks=40)
            ev = events(rows, "dive")
            self.assertEqual(len(ev), 1)
            self.assertGreater(ev[0]["data"]["pos"][1], tuning_gather()["surface_depth"])

    def test_surface_event_when_coming_up(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 2]}, "random_fish": False},
                              inputs=[{"tick": 0, "move": [0, -1]}], ticks=60)
            self.assertEqual(len(events(rows, "surface")), 1)
            self.assertEqual(len(events(rows, "dive")), 0)


class Faint(unittest.TestCase):
    def test_choke_reports_hp_after_damage(self):
        # PRD E: choke ghi hp sau khi trừ (hp_max 3 -> choke đầu tiên ghi 2)
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0},
                                  "random_fish": False}, ticks=100)
            ev = events(rows, "choke")
            self.assertEqual(ev[0]["data"], {"hp": tuning_gather()["hp_max"] - 1})
            self.assertEqual(by_tick(rows)[ev[0]["tick"]]["player"]["hp"], ev[0]["data"]["hp"])

    def test_faint_ends_gather_with_reason_fainted(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0, "hp": 1},
                                  "random_fish": False}, ticks=200)
            self.assertEqual(len(events(rows, "faint")), 1)
            end = events(rows, "gather_end")
            self.assertEqual(len(end), 1)
            self.assertEqual(end[0]["data"]["reason"], "fainted")
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["reason"], "fainted")
            self.assertEqual(snapshots(rows)[-1]["state"], "finished")

    def test_faint_lost_is_lifo(self):
        # PRD E: faint.lost theo thứ tự bỏ, nhặt sau bỏ trước (LIFO)
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0, "hp": 1},
                                  "hold": ["ca_loc", "bong_sung"], "random_fish": False}, ticks=100)
            ev = events(rows, "faint")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["data"]["lost"], ["bong_sung", "ca_loc"])

    def test_faint_empties_hold_and_inventory(self):
        # PRD F/G: Máu 0 thì bỏ giỏ; gather_end fainted với kho rỗng; file kho ghi rỗng
        with Workdir() as w:
            inv = w.path("kho.json")
            rows = run_gather(w, {"player": {"pos": [50, 10], "oxygen_ticks": 0, "hp": 1},
                                  "hold": ["ca_loc", "bong_sung"], "random_fish": False},
                              ticks=100, inv_out=inv)
            self.assertEqual(events(rows, "gather_end")[0]["data"]["inventory"], {"items": {}})
            self.assertEqual(snapshots(rows)[-1]["hold"], [])
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


class Harvest(unittest.TestCase):
    def test_gather_nearest_ready_node_at_surface(self):
        with Workdir() as w:
            nodes = [{"id": "N1", "kind": "bong_dien_dien", "pos": [21, 0]},
                     {"id": "N2", "kind": "bong_sung", "pos": [20.5, 0]}]
            rows = run_gather(w, {"player": {"pos": [20, 0]}, "nodes": nodes, "random_fish": False},
                              inputs=[{"tick": 0, "interact": True}], ticks=2)
            ev = events(rows, "gather")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["tick"], 1)
            self.assertEqual(ev[0]["data"], {"node_id": "N2", "kind": "bong_sung", "amount": 1})
            s = by_tick(rows)[1]
            self.assertEqual(s["hold"], ["bong_sung"])
            n2 = [n for n in s["nodes"] if n["id"] == "N2"][0]
            self.assertFalse(n2["ready"])

    def test_hold_full_keeps_node(self):
        cap = tuning_gather()["hold_capacity"]
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 0]}, "hold": ["ca_loc"] * cap, "random_fish": False,
                                  "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [21, 0]}]},
                              inputs=[{"tick": 0, "interact": True}], ticks=2)
            ev = events(rows, "hold_full")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["data"], {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
            self.assertTrue(by_tick(rows)[1]["nodes"][0]["ready"])
            self.assertEqual(events(rows, "gather"), [])


class Catch(unittest.TestCase):
    def test_catch_nearest_fish_underwater(self):
        g = tuning_gather()
        with Workdir() as w:
            fish = [{"id": "F1", "kind": "ca_linh", "pos": [21, 10]}, {"id": "F2", "kind": "ca_loc", "pos": [22, 10]}]
            rows = run_gather(w, {"player": {"pos": [20, 10]}, "fish": fish},
                              inputs=[{"tick": 0, "catch": True}], ticks=2)
            ev = events(rows, "fish_caught")
            self.assertEqual(len(ev), 1)
            self.assertEqual(ev[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": g["fish_yield"]["ca_linh"]})
            s = by_tick(rows)[1]
            self.assertEqual(s["hold"], ["ca_linh"] * g["fish_yield"]["ca_linh"])
            self.assertEqual([f["id"] for f in s["fish"]], ["F2"])
            self.assertEqual(s["player"]["catch_cd_ticks"], int(g["catch_cooldown_s"] * 60))

    def test_catch_ignored_at_surface(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 0]}, "fish": [{"id": "F1", "kind": "ca_loc", "pos": [20, 1]}]},
                              inputs=[{"tick": 0, "catch": True}], ticks=2)
            self.assertEqual(events(rows, "fish_caught"), [])
            self.assertEqual(by_tick(rows)[2]["player"]["catch_cd_ticks"], 0)

    def test_no_fish_in_range_no_cooldown(self):
        with Workdir() as w:
            rows = run_gather(w, {"player": {"pos": [20, 10]}, "fish": [{"id": "F1", "kind": "ca_loc", "pos": [40, 10]}]},
                              inputs=[{"tick": 0, "catch": True}], ticks=2)
            self.assertEqual([r for r in rows if r["type"] == "event"], [])
            self.assertEqual(by_tick(rows)[2]["player"]["catch_cd_ticks"], 0)


class DockInventory(unittest.TestCase):
    def test_dock_checked_before_harvest(self):
        with Workdir() as w:
            inv = w.path("kho.json")
            rows = run_gather(w, {"player": {"pos": [3, 0]}, "random_fish": False,
                                  "nodes": [{"id": "N1", "kind": "bong_sung", "pos": [4, 0]}]},
                              inputs=[{"tick": 0, "interact": True}, {"tick": 1, "interact": False},
                                      {"tick": 2, "interact": True}], ticks=10, inv_out=inv)
            # tick 0: trong bến -> docked ngay (bến xét trước hái)
            end = events(rows, "gather_end")
            self.assertEqual(end[0]["tick"], 1)
            self.assertEqual(end[0]["data"]["reason"], "docked")
            with open(inv, encoding="utf-8") as f:
                self.assertEqual(json.load(f), {"items": {}})


if __name__ == "__main__":
    unittest.main()
