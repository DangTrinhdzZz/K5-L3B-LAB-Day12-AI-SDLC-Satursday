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


if __name__ == "__main__":
    unittest.main()
