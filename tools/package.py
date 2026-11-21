"""Đóng gói bản phát hành: python3 tools/package.py [ref] -> dist/quan-an-cho-noi-<version>.zip

Dùng `git archive` nên gói đúng nội dung đã commit ở `ref` (mặc định HEAD, khi phát hành dùng tag v1.0.1), không lẫn
file tạm trong thư mục làm việc. Gói chạy được ngay: giải nén, vào thư mục, `python3 -m chonoi.live --mode day`.
"""

import os
import subprocess
import sys

VERSION = "1.0.2"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv=None) -> int:
    ref = (argv or sys.argv[1:] or ["HEAD"])[0]
    name = f"quan-an-cho-noi-v{VERSION}"
    out = os.path.join(ROOT, "dist", f"{name}.zip")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["git", "archive", "--format=zip", f"--prefix={name}/", "-o", out, ref], cwd=ROOT, check=True)
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
