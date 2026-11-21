"""Soak headless (Ticket-04 mục 2):

    python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày trong MỘT tiến trình headless bằng bot tất định (`chonoi.bot`). Mỗi Ngày đi qua gather -> quan -> shop;
kế hoạch D1–D5 lặp ở Ngày 6–10; tiền, tổng thu, uy tín, cấp nâng cấp, số Ngày và id cá thể đi tiếp xuyên suốt.
Không ghi bảng xếp hạng. Ghi soak.json: {days, days_completed, crashes, results[{day, earned, reputation, score}],
duration_s}. Trừ duration_s, mọi trường lặp lại y hệt với cùng seed.

Mã thoát: 0 khi chạy xong (kể cả có crash — crashes ghi trong file); 2 khi tham số sai; 1 khi không ghi được file.
"""

import argparse
import json
import math
import os
import sys
import time
import traceback

from .bot import Bot
from .contract import load_contract
from .errors import BadInput
from .runner import Session

MAX_DAYS = 1000


def run_soak(tuning, seed, days):
    start = time.perf_counter()
    results, crashes = [], 0
    sess = None
    try:
        sess = Session("day", tuning, {}, seed, days=days)
        bot = Bot(tuning)
        mult = tuning["score"]["reputation_multiplier"]
        while not sess.done:
            sim = sess.sim
            for row in sess.step(bot.decide(sim)):
                if row["name"] == "shop_end":
                    results.append({"day": row["day"], "earned": sim.earned, "reputation": sim.reputation,
                                    "score": sim.earned + mult * math.floor(sim.reputation)})
    except Exception:  # crash của sim: ghi nhận, dừng lượt
        crashes += 1
        sys.stderr.write(traceback.format_exc())
    return {"days": days, "days_completed": sess.sim.days_completed if sess else 0, "crashes": crashes,
            "results": results, "duration_s": round(time.perf_counter() - start, 3)}


def _write(path, obj):
    d = os.path.dirname(os.path.abspath(path))
    tmp = os.path.join(d, f".{os.path.basename(path)}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"lỗi: {message}\n")
        sys.exit(2)


def main(argv=None) -> int:
    p = _Parser(prog="chonoi.soak")
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--days", required=True, type=int)
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        if not 1 <= a.days <= MAX_DAYS:
            raise BadInput(f"--days phải trong [1, {MAX_DAYS}]")
        tuning = load_contract()["tuning"]
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    result = run_soak(tuning, a.seed, a.days)
    try:
        _write(a.out, result)
    except OSError as e:
        sys.stderr.write(f"lỗi ghi: {e}\n")
        return 1
    print(json.dumps({k: result[k] for k in ("days", "days_completed", "crashes", "duration_s")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
