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


class Leaderboard(unittest.TestCase):
    """Mở rộng `leaderboard` (Ticket-04 mục 3)."""

    def _day5(self, w, *extra, out="d.jsonl", seed="42"):
        return run_headless("--mode", "day", "--days", "5", "--seed", seed, "--ticks", "120000",
                            "--out", w.path(out), *extra)

    def test_declared_in_extensions(self):
        self.assertIn("leaderboard", manifest().get("extensions", []))

    def test_flag_pair_and_mode_exit_2(self):
        with Workdir() as w:
            out, lb = w.path("o.jsonl"), w.path("lb.json")
            base = ("--seed", "1", "--ticks", "1", "--out", out)
            self.assertEqual(run_headless("--mode", "day", *base, "--leaderboard", lb)[0], 2)
            self.assertEqual(run_headless("--mode", "day", *base, "--player-name", "Út Sen")[0], 2)
            self.assertEqual(run_headless("--mode", "gather", *base, "--leaderboard", lb, "--player-name", "A")[0], 2)
            self.assertEqual(run_headless("--mode", "day", *base, "--leaderboard", lb, "--player-name", "")[0], 2)
            self.assertFalse(os.path.exists(lb))

    def test_standard_run_writes_once_ties_keep_order_and_jsonl_unchanged(self):
        with Workdir() as w:
            lb = w.path("lb.json")
            code, err = self._day5(w, "--leaderboard", lb, "--player-name", "Út Sen", out="a.jsonl")
            self.assertEqual(code, 0, err)
            code, err = self._day5(w, "--leaderboard", lb, "--player-name", "Bé Hai", out="b.jsonl")
            self.assertEqual(code, 0, err)
            code, err = self._day5(w, out="c.jsonl")  # không cờ xếp hạng
            self.assertEqual(code, 0, err)
            with open(w.path("a.jsonl"), "rb") as a, open(w.path("c.jsonl"), "rb") as c:
                self.assertEqual(a.read(), c.read(), "file xếp hạng không đổi JSONL")
            end = read_jsonl(w.path("a.jsonl"))[-1]
            code, _, err = run_cmd("run_cmd", "--export-leaderboard", w.path("x.json"), "--leaderboard", lb)
            self.assertEqual(code, 0, err)
            with open(w.path("x.json"), encoding="utf-8") as f:
                entries = json.load(f)["entries"]
            self.assertEqual([e["name"] for e in entries], ["Út Sen", "Bé Hai"], "hòa điểm: mục ghi trước đứng trước")
            self.assertEqual(entries[0], {"name": "Út Sen", "score": end["score"], "days_completed": 5, "seed": 42})

    def test_non_standard_runs_not_recorded(self):
        with Workdir() as w:
            lb = w.path("lb.json")
            sc = write_json(w.path("sc.json"), {"gather": {"random_fish": False}})
            self.assertEqual(self._day5(w, "--leaderboard", lb, "--player-name", "A", "--scenario", sc)[0], 0)
            code, _ = run_headless("--mode", "day", "--days", "4", "--seed", "1", "--ticks", "100000",
                                   "--out", w.path("o.jsonl"), "--leaderboard", lb, "--player-name", "A")
            self.assertEqual(code, 0)
            code, _ = run_headless("--mode", "day", "--days", "5", "--seed", "1", "--ticks", "100",
                                   "--out", w.path("o.jsonl"), "--leaderboard", lb, "--player-name", "A")
            self.assertEqual(code, 0)  # chạm --ticks trước khi xong 5 Ngày
            self.assertFalse(os.path.exists(lb))

    def test_top10_sorted_desc(self):
        from chonoi import leaderboard
        with Workdir() as w:
            lb = w.path("lb.json")
            for i, score in enumerate([5, 9, 1, 9, 7, 3, 8, 2, 6, 4, 10, 0]):
                leaderboard.add(lb, f"P{i}", score, 5, i)
            entries = leaderboard.load(lb)
            self.assertEqual(len(entries), 10)
            self.assertEqual([e["score"] for e in entries], [10, 9, 9, 8, 7, 6, 5, 4, 3, 2])
            self.assertEqual([e["name"] for e in entries[1:3]], ["P1", "P3"])


if __name__ == "__main__":
    unittest.main()
