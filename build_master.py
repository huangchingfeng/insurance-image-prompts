#!/usr/bin/env python3
# 重建 tw/index.html 的 const DATA：依 tw/imgs/<id>.jpg 是否存在設定 img 欄位
# 用法：cd ~/insurance-image-gallery-work && python3 build_master.py
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, "tw", "index.html")
ROOT_INDEX = os.path.join(ROOT, "index.html")
IMGS = os.path.join(ROOT, "tw", "imgs")
PROMPTS = os.path.join(ROOT, "prompts_tw.json")

# 縮寫鍵對應（index.html DATA 用縮寫）
FULL2MIN = {"id": "id", "title": "t", "category": "c", "ratio": "r",
            "tags": "g", "prompt": "p", "note": "n", "img": "img"}


def extract_data_span(html):
    """以括號平衡擷取 const DATA = [...] 的陣列字串範圍 (start,end)。"""
    i = html.find("const DATA")
    start = html.find("[", i)
    depth = 0
    j = start
    instr = False
    esc = False
    q = ""
    while j < len(html):
        c = html[j]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == q:
                instr = False
        else:
            if c in ("\"", "'"):
                instr = True
                q = c
            elif c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    return start, j + 1
        j += 1
    raise RuntimeError("DATA 陣列未正確結束")


def main():
    data = json.load(open(PROMPTS, encoding="utf-8"))
    have = {f[:-4] for f in os.listdir(IMGS) if f.endswith(".jpg")}
    hung = 0
    minified = []
    for d in data:
        # 保留既有 img（含 6 個 pilot 特殊檔名）；缺的才用 <id>.jpg 補
        img = d.get("img") or ""
        if not img and d["id"] in have:
            img = d["id"] + ".jpg"
        if img:
            hung += 1
        d["img"] = img
        # 只上架「已成功生圖」的卡片；未生成的先不放（用戶指示：沒成功的先不要上）
        if not img:
            continue
        o = {}
        for full, mn in FULL2MIN.items():
            if full in d:
                o[mn] = d[full]
        minified.append(o)
    # 同步寫回 prompts_tw.json（img 欄位更新；保留全部 280 題供日後補生）
    json.dump(data, open(PROMPTS, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    shown = len(minified)
    shown_cats = len({o["c"] for o in minified})

    def fix_counts(h):
        h = re.sub(r"台灣版 \d+ 張", f"台灣版 {shown} 張", h)
        h = re.sub(r"已生成示意圖 \d+ 張", f"已上架示意圖 {shown} 張", h)
        h = re.sub(r"分 \d+ 類", f"分 {shown_cats} 類", h)
        return h

    # 換進 tw/index.html
    html = open(HTML, encoding="utf-8").read()
    s, e = extract_data_span(html)
    arr = json.dumps(minified, ensure_ascii=False, separators=(",", ":"))
    html = fix_counts(html[:s] + arr + html[e:])
    open(HTML, "w", encoding="utf-8").write(html)

    # 同步產生「根 index.html」＝同一份完整畫廊，但圖片路徑指到 tw/imgs/，
    # 並移除 noindex（根網址是對外分享頁，要可被索引）。
    root_html = html.replace('"imgs/\'+d.img', '"tw/imgs/\'+d.img')
    root_html = root_html.replace(
        '<meta name="robots" content="noindex">', "")
    open(ROOT_INDEX, "w", encoding="utf-8").write(root_html)

    cats = len({d["category"] for d in data})
    print(f"重建:全{len(data)}題 / 已生圖{hung} / 上架顯示{shown}張 / "
          f"{shown_cats}類（tw + 根 index.html 同步，未生成的隱藏）")


if __name__ == "__main__":
    main()
