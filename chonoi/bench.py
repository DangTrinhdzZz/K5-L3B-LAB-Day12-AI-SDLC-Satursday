"""Benchmark có render (Ticket-04 mục 1):

    python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json

Cảnh đo: buổi sáng lõi (độ tươi, cá bơi, Cá Sấu Năm Chèo, hiệu ứng mặc định), Út Sen đứng yên ở bến, seed 42.
Cách đo: chạy máy chủ chơi thử (`chonoi.live`, cùng sim 60 tick/s) rồi mở trang canvas bằng Chrome / Chromium /
Edge ở chế độ headless, cửa sổ 1280×720. Trang ở chế độ bench tự làm nóng 3 s, đo `--duration` giây bằng
requestAnimationFrame và gửi thời điểm từng khung về máy chủ. Python tính:
  frames, measured_s  : số khung và số giây thực tế trong khoảng đo sau làm nóng
  avg_fps             : frames / measured_s
  p1_low_fps          : max(1, ceil(1 % × frames)) khung chậm nhất -> nghịch đảo thời gian trung bình (giây)
  load_ms             : từ lúc khởi chạy lệnh tới khung hình đầu tiên của cảnh đo

Trình duyệt: biến môi trường CHONOI_BROWSER (đường dẫn), nếu không thì tự tìm google-chrome / chromium / msedge.
`--headed` mở cửa sổ thật thay vì headless. Mã thoát: 0 ghi xong bench.json; 2 tham số sai; 1 không có trình duyệt
hoặc đo thất bại.
"""

T0 = __import__("time").perf_counter()  # mốc "khởi chạy" cho load_ms, lấy sớm nhất có thể

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402

WARMUP_S = 3
WINDOW = (1280, 720)
CANDIDATES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge",
              "microsoft-edge", "microsoft-edge-stable"]
FIXED_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_browser():
    env = os.environ.get("CHONOI_BROWSER")
    if env:
        return env if os.path.exists(env) or shutil.which(env) else None
    for name in CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    return next((p for p in FIXED_PATHS if os.path.exists(p)), None)


def metrics(stamps_ms, load_ms):
    """stamps_ms: thời điểm (ms) các khung trong khoảng đo, khung đầu là mốc bắt đầu đo."""
    deltas = [(b - a) / 1000.0 for a, b in zip(stamps_ms, stamps_ms[1:]) if b > a]
    if not deltas:
        raise ValueError("không có khung hình nào trong khoảng đo")
    frames = len(deltas)
    measured_s = (stamps_ms[-1] - stamps_ms[0]) / 1000.0
    k = max(1, math.ceil(0.01 * frames))
    slow = sorted(deltas, reverse=True)[:k]
    return {"avg_fps": round(frames / measured_s, 2), "p1_low_fps": round(1.0 / (sum(slow) / k), 2),
            "frames": frames, "measured_s": round(measured_s, 3), "load_ms": int(round(load_ms))}


class BenchSink:
    """Nhận tín hiệu từ trang (qua chonoi.live): khung đầu tiên và danh sách thời điểm khung."""

    def __init__(self):
        self.first_frame_at = None
        self.stamps = None
        self.done = threading.Event()

    def __call__(self, kind, data):
        if kind == "first" and self.first_frame_at is None:
            self.first_frame_at = time.perf_counter()
        elif kind == "result":
            stamps = data.get("stamps")
            if not isinstance(stamps, list) or not all(isinstance(x, (int, float)) for x in stamps):
                raise ValueError("stamps phải là mảng số")
            self.stamps = stamps
            self.done.set()


def run_bench(seed, duration, headed=False, browser=None, timeout_pad=90):
    from .contract import load_contract
    from .live import LiveGame, LiveServer

    browser = browser or find_browser()
    if browser is None:
        raise RuntimeError("không tìm thấy Chrome/Chromium/Edge; đặt CHONOI_BROWSER=<đường dẫn trình duyệt>")
    tuning = load_contract()["tuning"]
    sink = BenchSink()
    game = LiveGame("gather", tuning, {}, seed, screen="game")
    game.bench_sink = sink
    server = LiveServer(game, port=0)
    server.start()
    profile = tempfile.mkdtemp(prefix="chonoi-bench-")
    url = f"{server.url}?bench=1&warmup={WARMUP_S}&duration={duration}"
    args = [browser, f"--window-size={WINDOW[0]},{WINDOW[1]}", f"--user-data-dir={profile}", "--no-first-run",
            "--no-default-browser-check", "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding", "--disable-backgrounding-occluded-windows", "--hide-scrollbars"]
    if not headed:
        args.append("--headless=new")
    proc = subprocess.Popen(args + [url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not sink.done.wait(WARMUP_S + duration + timeout_pad):
            raise RuntimeError("trang không gửi kết quả đo (trình duyệt không chạy được trang?)")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        server.stop()
        shutil.rmtree(profile, ignore_errors=True)
    load_ms = ((sink.first_frame_at or time.perf_counter()) - T0) * 1000.0
    return metrics(sink.stamps, load_ms)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.bench", description="Benchmark có render cảnh lặn.")
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--duration", required=True, type=float, help="số giây đo (sau 3 s làm nóng)")
    p.add_argument("--out", required=True)
    p.add_argument("--headed", action="store_true", help="mở cửa sổ thật thay vì headless")
    try:
        a = p.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    if not 1 <= a.duration <= 3600:
        sys.stderr.write("đầu vào sai: --duration phải trong [1, 3600]\n")
        return 2
    try:
        result = run_bench(a.seed, a.duration, headed=a.headed)
    except (RuntimeError, ValueError, OSError) as e:
        sys.stderr.write(f"bench thất bại: {e}\n")
        return 1
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f)
        f.write("\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
