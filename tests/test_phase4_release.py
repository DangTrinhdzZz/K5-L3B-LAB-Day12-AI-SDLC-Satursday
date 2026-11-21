"""Test Phase 4 (contract v1.3, Ticket-04): manifest, soak headless, công thức benchmark."""

import json
import os
import shlex
import subprocess
import unittest

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, write_json

from chonoi.bench import find_browser, metrics
from chonoi.contract import load_contract
from chonoi.runner import Session


def manifest():
    with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
        return json.load(f)


def run_cmd(key, *args):
    p = subprocess.run([*shlex.split(manifest()[key]), *args], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


class Manifest(unittest.TestCase):
    def test_v13_declares_bench_and_soak(self):
        m = manifest()
        self.assertEqual(m["contract_version"], "1.3")
        for key in ("bench_cmd", "soak_cmd", "headless_cmd", "run_cmd", "build_cmd"):
            self.assertTrue(m[key].strip(), key)


class Soak(unittest.TestCase):
    def test_soak_completes_and_is_deterministic(self):
        with Workdir() as w:
            outs = []
            for i in (1, 2):
                code, _, err = run_cmd("soak_cmd", "--seed", "7", "--days", "3", "--out", w.path(f"s{i}.json"))
                self.assertEqual(code, 0, err)
                with open(w.path(f"s{i}.json"), encoding="utf-8") as f:
                    outs.append(json.load(f))
            a, b = outs
            self.assertEqual(set(a), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual((a["days"], a["days_completed"], a["crashes"]), (3, 3, 0))
            self.assertEqual([r["day"] for r in a["results"]], [1, 2, 3])
            for r in a["results"]:
                self.assertEqual(set(r), {"day", "earned", "reputation", "score"})
            a.pop("duration_s"), b.pop("duration_s")
            self.assertEqual(a, b, "cùng seed -> cùng kết quả (bỏ số đo thời gian)")

    def test_soak_bad_args_exit_2(self):
        with Workdir() as w:
            self.assertEqual(run_cmd("soak_cmd", "--seed", "7", "--days", "0", "--out", w.path("s.json"))[0], 2)
            self.assertEqual(run_cmd("soak_cmd", "--seed", "x", "--days", "1", "--out", w.path("s.json"))[0], 2)

    def test_plan_repeats_after_day_5(self):
        tuning = load_contract()["tuning"]
        sim = Session("day", tuning, {}, 1, days=10).sim
        sim.day = 6
        self.assertEqual(sim.plan()["dishes"], tuning["day_plan"][0]["dishes"])
        sim.day = 10
        self.assertEqual(sim.plan()["dishes"], tuning["day_plan"][4]["dishes"])


class DayEnvelope(unittest.TestCase):
    def test_shop_end_carries_the_finished_day(self):
        sc = {"gather": {"random_fish": False}, "quan": {"time_left_ticks": 1, "random_customers": False}}
        with Workdir() as w:
            code, err = run_headless("--mode", "day", "--days", "2", "--seed", "1", "--ticks", "6",
                                     "--scenario", write_json(w.path("sc.json"), sc),
                                     "--inputs", write_json(w.path("in.json"), frames({"tick": 0, "interact": True},
                                                                                     {"tick": 2, "shop_done": True})),
                                     "--out", w.path("d.jsonl"))
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("d.jsonl"))
            self.assertEqual(events(rows, "shop_end")[0]["day"], 1)
            self.assertEqual(events(rows, "day_start")[1]["day"], 2)


class BenchMetrics(unittest.TestCase):
    def test_formula(self):
        m = metrics([0.0, 10.0, 20.0, 40.0], load_ms=1234.4)
        self.assertEqual(m, {"avg_fps": 75.0, "p1_low_fps": 50.0, "frames": 3, "measured_s": 0.04, "load_ms": 1234})

    def test_one_percent_of_frames(self):
        stamps = [i * 10.0 for i in range(201)]  # 200 khung 10 ms
        stamps[100:] = [s + 40 for s in stamps[100:]]  # 1 khung 50 ms
        stamps[150:] = [s + 10 for s in stamps[150:]]  # 1 khung 20 ms
        m = metrics(stamps, 0)
        self.assertEqual(m["frames"], 200)
        self.assertEqual(m["p1_low_fps"], round(1 / ((0.05 + 0.02) / 2), 2))  # ceil(1 % × 200) = 2 khung chậm nhất

    @unittest.skipUnless(os.environ.get("CHONOI_RUN_BENCH") == "1" and find_browser(),
                         "đặt CHONOI_RUN_BENCH=1 (và có Chrome/Chromium) để chạy bench thật")
    def test_bench_cmd_writes_five_fields(self):
        with Workdir() as w:
            code, _, err = run_cmd("bench_cmd", "--seed", "42", "--duration", "3", "--out", w.path("bench.json"))
            self.assertEqual(code, 0, err)
            with open(w.path("bench.json"), encoding="utf-8") as f:
                b = json.load(f)
            self.assertEqual(set(b), {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"})
            self.assertGreater(b["frames"], 0)


if __name__ == "__main__":
    unittest.main()
