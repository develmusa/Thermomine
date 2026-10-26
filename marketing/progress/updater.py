"""Feeds the progress page: writes status.json + preview images next to index.html every few seconds.

Sources:
  - Hailuo AI clip: progress text read from the temporary Chromium over CDP (port 9333)
  - Colour animation: frame count + latest frame from the desktop over SSH (Tailscale)
"""
import json
import os
import re
import shutil
import subprocess
import time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
TIKTOK = os.path.join(HERE, "..", "tiktok")
REMOTE = "render/aquarium_mine/frames_colour"
TOTAL_FRAMES = 180


def ssh(cmd, timeout=20):
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "desktop", cmd],
                       capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()


def hailuo_status(pw):
    try:
        br = pw.chromium.connect_over_cdp("http://127.0.0.1:9333")
        page = [pg for c in br.contexts for pg in c.pages if "hailuoai" in pg.url][-1]
        text = page.evaluate("document.body.innerText.replace(/\\s+/g, ' ')")
        br.close()
    except Exception as e:  # browser closed or busy
        return {"state": "unknown", "detail": str(e)[:120]}
    if os.path.exists(os.path.join(TIKTOK, "clip_ai_pushin.mp4")):
        return {"state": "done", "percent": 100}
    m = re.search(r"(\d{1,3})%\s*Generating", text)
    if m:
        return {"state": "generating", "percent": int(m.group(1))}
    if "Generating" in text:
        return {"state": "generating", "percent": None}
    return {"state": "waiting for download", "percent": 100}


def colour_status(last_preview):
    try:
        listing = ssh(f"ls -1t {REMOTE} 2>/dev/null | head -1; ls -1 {REMOTE} 2>/dev/null | wc -l")
        newest, count = (listing.splitlines() + ["", "0"])[:2]
        count = int(count or 0)
    except Exception as e:
        return {"state": "unknown", "detail": str(e)[:120]}, last_preview
    if newest and newest != last_preview:
        tmp = os.path.join(HERE, "_colour_latest.png")
        if subprocess.run(["scp", "-o", "BatchMode=yes", "-q", f"desktop:{REMOTE}/{newest}", tmp]).returncode == 0:
            shutil.move(tmp, os.path.join(HERE, "colour_latest.png"))
            last_preview = newest
    done = os.path.exists(os.path.join(TIKTOK, "clip_colour_change.mp4"))
    state = "done" if done else ("rendering" if count < TOTAL_FRAMES else "assembling clip")
    return {"state": state, "frames": count, "total": TOTAL_FRAMES, "latest": newest}, last_preview


def main():
    last_preview = None
    with sync_playwright() as pw:
        while True:
            colour, last_preview = colour_status(last_preview)
            status = {
                "updated": time.strftime("%H:%M:%S"),
                "hailuo": hailuo_status(pw),
                "colour": colour,
                "clips": {name: os.path.exists(os.path.join(TIKTOK, name))
                          for name in ("clip_ai_pushin.mp4", "clip_colour_change.mp4", "tiktok_final.mp4")},
            }
            tmp = os.path.join(HERE, "status.json.tmp")
            json.dump(status, open(tmp, "w"), indent=1)
            os.replace(tmp, os.path.join(HERE, "status.json"))
            time.sleep(8)


if __name__ == "__main__":
    main()
