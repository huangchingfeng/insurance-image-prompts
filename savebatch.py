#!/usr/bin/env python3
# 從剪貼簿讀 dataURL/base64，驗證為 JPEG，md5 去重後存到 batch-v2/<id>.jpg
# 用法：python3 savebatch.py <id>   （剪貼簿須先有 CAP 抓到的圖片 dataURL）
import base64
import glob
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, "batch-v2")
DEDUP_DIRS = [DIR, os.path.join(ROOT, "tw", "imgs")]


def main():
    if len(sys.argv) < 2:
        print("USAGE: savebatch.py <id>")
        sys.exit(1)
    name = sys.argv[1]
    os.makedirs(DIR, exist_ok=True)
    data = subprocess.run(["pbpaste"], capture_output=True, text=True).stdout
    b = data.split(",", 1)[1] if "," in data[:64] else data
    try:
        raw = base64.b64decode(b)
    except Exception as ex:
        print("DECODE_ERR", ex)
        sys.exit(1)
    if len(raw) < 3000 or raw[:3] != b"\xff\xd8\xff":
        print(f"NOT_JPEG len={len(raw)} head={raw[:4].hex()}")
        sys.exit(1)
    md5 = hashlib.md5(raw).hexdigest()
    for dd in DEDUP_DIRS:
        for f in glob.glob(os.path.join(dd, "*.jpg")):
            if os.path.basename(f) == name + ".jpg":
                continue
            if hashlib.md5(open(f, "rb").read()).hexdigest() == md5:
                print(f"DUP of {os.path.basename(f)}")
                sys.exit(2)
    out = os.path.join(DIR, name + ".jpg")
    open(out, "wb").write(raw)
    print(f"OK {name}.jpg {len(raw)} B md5={md5[:12]}")


if __name__ == "__main__":
    main()
