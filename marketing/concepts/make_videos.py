"""Turn concept first-frames into Hailuo videos through the MiniMax API.
   MINIMAX_API_KEY=... python3 make_videos.py CONCEPT [CONCEPT ...]
Progress for the website goes to jobs.json (one entry per concept).
"""
import base64
import json
import os
import sys
import threading
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.minimax.io"
KEY = os.environ["MINIMAX_API_KEY"]
MODEL, RES, DUR = "MiniMax-Hailuo-2.3", "1080P", 6
KEEP = (" The black spherical decoration with the glowing slots stays completely unchanged in shape, size, "
        "colour and position; no morphing, no new objects on it, no text, no logos.")
PROMPTS = {
    "1_warning_red": "[Static shot] A dark living room at night. The aquarium on the cabinet glows with a faint red "
                     "light from the object on its gravel. A person in silhouette walks slowly into frame from the "
                     "left, stops in front of the tank and leans closer, concerned. Subtle, tense, cinematic." + KEEP,
    "2_aesthetic_tank": "[Push in] Slow push in toward the object on the gravel. A small school of neon tetras "
                        "swims calmly into frame and around it, plants sway gently, tiny bubbles rise, soft "
                        "caustic light ripples over the gravel. Calm, beautiful aquascape." + KEEP,
    "4_asmr_macro": "[Static shot] Extreme macro. Small air bubbles rise slowly past the glowing blue slots, tiny "
                    "particles drift in the water, the light shimmers softly. Satisfying, calm, ASMR." + KEEP,
    "6_shipwreck_theme": "[Truck left] Slow sideways camera move past the object on the sand next to the old "
                         "shipwreck. Light rays shift through the water, a few small fish dart past the wreck, "
                         "fine sand particles float. Adventurous treasure-hunt mood." + KEEP,
}
LOCK = threading.Lock()
JOBS = os.path.join(HERE, "jobs.json")


def save(name, **kw):
    with LOCK:
        jobs = json.load(open(JOBS)) if os.path.exists(JOBS) else {}
        jobs.setdefault(name, {}).update(kw, updated=time.strftime("%H:%M:%S"))
        tmp = JOBS + ".tmp"; json.dump(jobs, open(tmp, "w"), indent=1); os.replace(tmp, JOBS)


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def run(name):
    img = os.path.join(HERE, f"{name}.png")
    out_dir = os.path.join(HERE, "videos"); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{name}.mp4")
    try:
        save(name, state="submitting", model=MODEL, prompt=PROMPTS[name])
        data = base64.b64encode(open(img, "rb").read()).decode()
        r = call("POST", "/v1/video_generation", {"model": MODEL, "first_frame_image": f"data:image/png;base64,{data}",
                                                  "prompt": PROMPTS[name], "prompt_optimizer": False,
                                                  "duration": DUR, "resolution": RES})
        if r.get("base_resp", {}).get("status_code") != 0:
            save(name, state="failed", error=r.get("base_resp")); return
        task = r["task_id"]; save(name, state="queued", task_id=task)
        while True:
            time.sleep(15)
            q = call("GET", f"/v1/query/video_generation?task_id={task}")
            st = q.get("status")
            save(name, state=st.lower() if st else "unknown")
            if st == "Success":
                break
            if st == "Fail":
                save(name, state="failed", error=q.get("base_resp")); return
        f = call("GET", f"/v1/files/retrieve?file_id={q['file_id']}")
        urllib.request.urlretrieve(f["file"]["download_url"], out)
        save(name, state="done", video=f"videos/{name}.mp4", size=f"{q.get('video_width')}x{q.get('video_height')}")
    except Exception as e:
        save(name, state="failed", error=str(e)[:300])


threads = [threading.Thread(target=run, args=(n,)) for n in sys.argv[1:]]
for t in threads: t.start()
for t in threads: t.join()
print(json.dumps(json.load(open(JOBS)), indent=1))
