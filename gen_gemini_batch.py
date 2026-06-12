#!/usr/bin/env python3
# 用 Gemini 圖像模型批次生成剩餘未完成的 v2 示意圖，逐張即存到 batch-v2/ 與 tw/imgs/
import json
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
KEY = open("/tmp/found_gemini_key.txt").read().strip()
from google import genai  # noqa: E402

client = genai.Client(api_key=KEY)
MODELS = ["gemini-3-pro-image-preview", "gemini-3.1-flash-image",
          "gemini-2.5-flash-image"]

data = json.load(open("prompts_tw.json", encoding="utf-8"))
have = {f[:-4] for f in os.listdir("tw/imgs") if f.endswith(".jpg")}
order = ["活動宣傳", "增員招募", "個人品牌", "業績榮耀客戶見證版型",
         "情境故事圖", "節慶賀圖", "社群觀念圖卡", "客戶關懷",
         "觀念圖解資訊圖", "理賠流程保單觀念圖解"]
todo = [d for d in data if not d.get("img") and d["id"] not in have]
todo.sort(key=lambda d: (order.index(d["category"])
                         if d["category"] in order else 99, d["id"]))
print(f"待生成: {len(todo)} 張", flush=True)

ok = fail = 0
failed_ids = []
for i, d in enumerate(todo):
    iid = d["id"]
    prompt = d["prompt"]
    saved = False
    for attempt in range(3):
        for model in MODELS:
            try:
                r = client.models.generate_content(model=model, contents=prompt)
                parts = r.candidates[0].content.parts
                imgs = [p for p in parts if getattr(p, "inline_data", None)]
                if not imgs:
                    continue
                raw = imgs[0].inline_data.data
                if len(raw) < 3000:
                    continue
                open(f"batch-v2/{iid}.jpg", "wb").write(raw)
                open(f"tw/imgs/{iid}.jpg", "wb").write(raw)
                ok += 1
                saved = True
                print(f"[{i+1}/{len(todo)}] ✅ {iid} ({d['category']}/"
                      f"{d['ratio']}) {model.split('-image')[0]} {len(raw)}B",
                      flush=True)
                break
            except Exception as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
                    wait = 30 * (attempt + 1)
                    print(f"   ⏳ {iid} 限流, 等 {wait}s 重試...", flush=True)
                    time.sleep(wait)
                    break  # retry outer loop
                else:
                    print(f"   ⚠ {iid} {model}: {type(e).__name__} {msg[:70]}",
                          flush=True)
                    continue
        if saved:
            break
    if not saved:
        fail += 1
        failed_ids.append(iid)
        print(f"[{i+1}/{len(todo)}] ❌ {iid} 放棄", flush=True)
    time.sleep(2)  # 緩衝避免限流

print(f"\n=== 完成: 成功 {ok} / 失敗 {fail} ===", flush=True)
if failed_ids:
    print("失敗清單:", ",".join(failed_ids), flush=True)
