"""Test luật Phase 2 (contract v1.1): cá bơi / sinh, Cá Sấu, 2 bếp / 4 bàn, 6 món — hộp đen qua headless_cmd."""

import json
import math
import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning():
    with open("game.contract.json", encoding="utf-8") as f:
        return json.load(f)["tuning"]


def run(w, mode, block, inputs=None, ticks=10, every=1, seed=1, out="o.jsonl"):
    sc = write_json(w.path("sc.json"), {mode: block})
    args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--scenario", sc,
            "--snapshot-every", str(every), "--out", w.path(out)]
    if inputs is not None:
        args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
    code, err = run_headless(*args)
    if code != 0:
        raise AssertionError(err)
    return read_jsonl(w.path(out))


def by_tick(rows):
    return {r["tick"]: r for r in snapshots(rows)}


NO_NODES = {"nodes": [{"id": "N1", "kind": "bong_sung", "pos": [99, 0]}]}
NO_MONSTERS = {"monsters": []}


class StandardNumbers(unittest.TestCase):
    def test_contract_v11_data(self):
        with open("game.contract.json", encoding="utf-8") as f:
            c = json.load(f)
        t = c["tuning"]
        self.assertEqual(c["contract_version"], "1.1")
        self.assertEqual(len(t["menu"]), 6)
        self.assertEqual([s["id"] for s in t["quan"]["stoves"]], ["B1", "B2"])
        self.assertEqual([s["id"] for s in t["quan"]["tables"]], ["T1", "T2", "T3", "T4"])
        self.assertEqual(t["gather"]["fish_yield"], {"ca_linh": 3, "ca_loc": 1, "ca_keo": 2})
        self.assertEqual([e["day"] for e in t["day_plan"]], [1, 2, 3, 4, 5])
        self.assertEqual(t["day_plan"][3]["ingredients"], {"bong_dien_dien": 1, "bong_sung": 2, "ca_keo": 1,
                                                           "ca_linh": 2, "ca_loc": 2, "keo_neo": 1})

    def test_default_gather_has_8_fish_6_nodes_m1(self):
        t = tuning()["gather"]
        with Workdir() as w:
            s = snapshots(run(w, "gather", {}, ticks=0))[0]
            self.assertEqual(len(s["fish"]), 8)
            self.assertEqual([f["id"] for f in s["fish"]], [f"F{i}" for i in range(1, 9)])
            self.assertEqual(len({tuple(f["pos"]) for f in s["fish"]}), 8, "8 điểm khác nhau")
            for f in s["fish"]:
                self.assertIn(f["pos"][0], t["fish_spawn_x"])
                self.assertIn(f["pos"][1], t["fish_spawn_depths"][f["kind"]])
            self.assertEqual([n["id"] for n in s["nodes"]], ["N1", "N2", "N3", "N4", "N5", "N6"])
            self.assertEqual([m["id"] for m in s["monsters"]], ["M1"])
            self.assertEqual(s["monsters"][0]["state"], "patrol")


class FishSwim(unittest.TestCase):
    def test_swim_speed_and_age(self):
        speed = tuning()["gather"]["fish_speed"]
        with Workdir() as w:
            block = dict(NO_NODES, **NO_MONSTERS, fish=[{"id": "F1", "kind": "ca_loc", "pos": [50, 14]}])
            s = by_tick(run(w, "gather", block, ticks=60, every=60))
            self.assertAlmostEqual(s[60]["fish"][0]["pos"][0], 50 + speed, places=2)
            self.assertEqual(s[60]["fish"][0]["age_ticks"], 60)

    def test_reflect_at_depth_edge(self):
        with Workdir() as w:
            block = dict(NO_NODES, **NO_MONSTERS,
                         fish=[{"id": "F1", "kind": "ca_linh", "pos": [50, 11.99], "heading_deg": 90}])
            s = by_tick(run(w, "gather", block, ticks=3))
            f = s[3]["fish"][0]
            self.assertLessEqual(f["pos"][1], 12)
            self.assertAlmostEqual(f["heading_deg"], 270, places=3)

    def test_turn_on_swim_step_120(self):
        with Workdir() as w:
            block = dict(NO_NODES, **NO_MONSTERS, fish=[{"id": "F1", "kind": "ca_loc", "pos": [50, 14]}])
            s = by_tick(run(w, "gather", block, ticks=121))
            self.assertEqual(s[119]["fish"][0]["heading_deg"], 0)
            self.assertNotEqual(s[120]["fish"][0]["heading_deg"], 0)

    def test_random_fish_false_keeps_fixture_still(self):
        with Workdir() as w:
            block = dict(NO_NODES, **NO_MONSTERS, random_fish=False,
                         fish=[{"id": "F1", "kind": "ca_loc", "pos": [50, 14]}])
            rows = run(w, "gather", block, ticks=400, every=100)
            self.assertEqual(snapshots(rows)[-1]["fish"][0]["pos"], [50, 14])
            self.assertEqual(events(rows, "fish_spawned"), [])

    def test_spawn_on_schedule(self):
        t = tuning()["gather"]
        with Workdir() as w:
            block = dict(NO_NODES, **NO_MONSTERS, fish=[])
            rows = run(w, "gather", block, ticks=800, every=100)
            ev = events(rows, "fish_spawned")
            self.assertEqual([e["tick"] for e in ev], [t["fish_spawn_ticks"], 2 * t["fish_spawn_ticks"]])
            self.assertEqual(ev[0]["data"]["id"], "F1")
            self.assertIn(ev[0]["data"]["kind"], t["fish_yield"])

    def test_deterministic_with_swimming_fish(self):
        with Workdir() as w:
            for i in (1, 2):
                run(w, "gather", {}, inputs=[{"tick": 0, "move": [1, 1]}], ticks=1500, every=7, seed=5,
                    out=f"o{i}.jsonl")
            with open(w.path("o1.jsonl"), "rb") as a, open(w.path("o2.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


class Crocodile(unittest.TestCase):
    def test_patrol_toward_second_waypoint(self):
        with Workdir() as w:
            s = by_tick(run(w, "gather", dict(NO_NODES, random_fish=False), ticks=60, every=60))
            m = s[60]["monsters"][0]
            self.assertAlmostEqual(m["pos"][0], 61.0, places=2)
            self.assertEqual(m["target_idx"], 1)

    def test_chase_when_player_deep_and_near(self):
        with Workdir() as w:
            rows = run(w, "gather", dict(NO_NODES, random_fish=False, player={"pos": [60, 16]}), ticks=10)
            m = by_tick(rows)[1]["monsters"][0]
            self.assertEqual(m["state"], "chase")
            self.assertLess(m["pos"][1], 24)

    def test_chase_at_minimum_detection_depth(self):
        scenario = dict(
            NO_NODES,
            random_fish=False,
            player={"pos": [60, 10]},
            monsters=[{"id": "M1", "kind": "ca_sau", "pos": [60, 15],
                       "waypoints": [[60, 15], [64, 15]]}],
        )
        with Workdir() as w:
            rows = run(w, "gather", scenario, ticks=2)
            self.assertEqual(by_tick(rows)[1]["monsters"][0]["state"], "chase")

    def test_no_chase_when_player_shallow(self):
        with Workdir() as w:
            rows = run(w, "gather", dict(NO_NODES, random_fish=False, player={"pos": [60, 5]}), ticks=10)
            self.assertEqual(by_tick(rows)[10]["monsters"][0]["state"], "patrol")

    def test_hit_loses_hp_drops_lifo_and_invuln(self):
        t = tuning()["gather"]
        hold = ["ca_loc", "bong_sung", "ca_linh", "keo_neo"]
        with Workdir() as w:
            rows = run(w, "gather", dict(NO_NODES, random_fish=False, hold=hold, player={"pos": [60, 23]}), ticks=3)
            hit = events(rows, "monster_hit")
            self.assertEqual(len(hit), 1)
            self.assertEqual(hit[0]["tick"], 1)
            self.assertEqual(hit[0]["data"]["monster_id"], "M1")
            self.assertEqual(hit[0]["data"]["hp"], t["hp_max"] - 1)
            self.assertEqual(hit[0]["data"]["lost"], ["keo_neo", "ca_linh"])
            s = by_tick(rows)[1]
            self.assertEqual(s["hold"], ["ca_loc", "bong_sung"])
            self.assertEqual(s["player"]["invuln_ticks"], t["monsters"]["invuln_ticks"])
            self.assertEqual(s["monsters"][0]["state"], "recoil")
            self.assertEqual(s["monsters"][0]["state_ticks_left"], t["monsters"]["species"]["ca_sau"]["recoil_ticks"])

    def test_faint_by_monster(self):
        with Workdir() as w:
            rows = run(w, "gather", dict(NO_NODES, random_fish=False, hold=["ca_loc", "bong_sung"],
                                         player={"pos": [60, 23], "hp": 1}), ticks=5)
            f = events(rows, "faint")
            self.assertEqual(len(f), 1)
            self.assertEqual(f[0]["data"]["cause"], "monster")
            self.assertEqual(f[0]["data"]["hp"], 0)
            self.assertEqual(events(rows, "gather_end")[0]["data"], {"reason": "fainted", "inventory": {"items": {}}})

    def test_bad_monster_fixture_exit_2(self):
        bad = [{"id": "M1", "kind": "ca_sau", "pos": [60, 5], "waypoints": [[60, 24], [64, 24]]},
               {"id": "M1", "kind": "rong", "waypoints": [[60, 24], [64, 24]]},
               {"id": "M1", "kind": "ca_sau", "waypoints": [[60, 24], [64, 24]], "state": "recoil"}]
        with Workdir() as w:
            for m in bad:
                sc = write_json(w.path("sc.json"), {"gather": {"monsters": [m]}})
                code, _ = run_headless("--mode", "gather", "--seed", "1", "--ticks", "1", "--scenario", sc,
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, m)


class QuanV11(unittest.TestCase):
    def test_four_tables_two_stoves(self):
        stock = {"ca_loc": 9, "bong_sung": 9, "ca_linh": 9, "bong_dien_dien": 9, "ca_keo": 9, "keo_neo": 9}
        with Workdir() as w:
            rows = run(w, "quan", {"stock": stock}, ticks=4000, every=100)
            arr = events(rows, "customer_arrived")
            self.assertEqual(sorted(e["data"]["table_id"] for e in arr[:4]), ["T1", "T2", "T3", "T4"])

    def test_cook_lau_mam_on_b2(self):
        rec = tuning()["menu"]["lau_mam"]["recipe"]
        c = {"id": "C1", "table_id": "T1", "dish_id": "lau_mam"}
        with Workdir() as w:
            rows = run(w, "quan", {"player": {"pos": [5, 7]}, "stock": dict(rec), "customers": [c],
                                   "random_customers": False}, inputs=[{"tick": 0, "interact": True}], ticks=2)
            cs = events(rows, "cook_started")[0]["data"]
            self.assertEqual(cs["stove_id"], "B2")
            self.assertEqual(cs["items"], ["bong_dien_dien", "ca_keo", "ca_linh", "ca_linh", "keo_neo"])
            self.assertEqual(cs["base_price"], 200)

    def test_new_kinds_in_inventory_file(self):
        with Workdir() as w:
            inv = write_json(w.path("inv.json"), {"items": {"ca_keo": 2, "keo_neo": 1}})
            code, err = run_headless("--mode", "quan", "--seed", "1", "--ticks", "0", "--inventory", inv,
                                     "--out", w.path("q.jsonl"))
            self.assertEqual(code, 0, err)
            self.assertEqual(snapshots(read_jsonl(w.path("q.jsonl")))[0]["stock"], {"ca_keo": 2, "keo_neo": 1})


if __name__ == "__main__":
    unittest.main()
