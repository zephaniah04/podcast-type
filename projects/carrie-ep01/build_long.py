#!/usr/bin/env python3
"""Carrie ep01 long-forms. Renders as reusable pieces, then concat:
  L01 = CO1 + P1 + P2 + P3 + P4      (whole episode)
  L02 = CO2 + P1 + P2                (Part 1: hydration, cramps, race fuelling, training)
  L03 = CO3 + P3 + P4                (Part 2: daily eating, protein, recovery meals)
Body parts: auto-frame (pitch labels), tighten 0.6, chapter title card over the first ~3 s of each chapter,
full-screen motion cards (<= 7 s) where a number / list / protocol is spoken. Captions: cold opens only (+ P1 intro).
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_shorts as B  # noqa: E402  (word snapping, fixes, file map)

EP = B.EP
LONG = os.path.join(EP, "long"); os.makedirs(LONG, exist_ok=True)
CARDS = []
AF = {"zoom": 1.9, "zoom_right": 1.55, "punch": 1.1, "wide_every": 4, "cy": 0.38, "min_turn": 1.6}

CH = [  # (file, start, title)
 ("A", "01:07.5", "What I Eat in a Day as a HYROX Athlete"),
 ("A", "06:04.7", "How Much Water You Actually Need"),
 ("A", "08:58.0", "ChatGPT Was My Dietitian: Supplements and Vitamin D"),
 ("A", "12:22.0", "Salt on My Face and Cramps in Every HYROX"),
 ("A", "18:06.1", "The 1 kg = 1 Litre Sweat Test"),
 ("A", "23:38.8", "1,000 mg of Sodium, Caffeine and Only 2 Gels"),
 ("A", "28:22.6", "Gaining Muscle Without Getting Slower"),
 ("A", "32:49.9", "Training Fasted? What to Eat Before the Gym"),
 ("A", "36:10.1", "Is the 30-Minute Window Real?"),
 ("B", "01:30.8", "What Creatine Actually Does"),
 ("B", "04:08.1", "Why 50 g of Protein Is Plenty"),
 ("B", "12:21.3", "The 5-Hour Gap Before Evening Training"),
 ("B", "18:15.5", "I Loaded Up on Protein and Forgot Carbs"),
 ("B", "24:11.0", "Too Tired to Cook: No-Cook Recovery Dinners"),
 ("B", "38:20.0", "Can I Gain Muscle Before Race Day?"),
 ("B", "43:24.0", "Meal Prep and Why Dinner Matters After Night Workouts"),
 ("B", "47:05.2", "Real Food vs Multivitamins"),
]
END = {"A": "39:11.2", "B": "51:10.5"}
PARTS = {"P1": (0, 5), "P2": (5, 10), "P3": (10, 14), "P4": (14, 17)}  # chapter index ranges

# full-screen inserts: (file, start, end, card) -- same moments the shorts use, re-laid for 16:9
INS = []
for c in B.S:
    for part in c["parts"]:
        o = part[4] if len(part) > 4 else {}
        if o.get("card"):
            INS.append((part[0], B.sec(part[1]), B.sec(part[2]), o["card"]))


def wide_card(card, dur):
    c = {k: v for k, v in card.items() if k not in ("at", "delay")}
    n = len(c.get("items", c.get("points", c.get("bars", [])))) or 1
    if "items" in c:
        c["at"] = [0.4 + 0.7 * k for k in range(n)]
    if "points" in c:
        c["points"] = [{**{k: v for k, v in p.items() if k != "at"}, "at": 0.5 + 0.8 * i} for i, p in enumerate(c["points"])]
    if c.get("type") in ("dodont", "versus"):
        c["delay"] = 1.6
    c.update(w=1920, h=1080, dur=round(dur + 0.6, 2))
    return c


def body(part):
    i0, i1 = PARTS[part]
    segs = []
    for ci in range(i0, i1):
        f, st, title = CH[ci]
        nxt = CH[ci + 1] if ci + 1 < len(CH) else None
        en = B.sec(nxt[1]) if nxt and nxt[0] == f else B.sec(END[f])
        st = B.sec(st)
        # title card over the first ~3 s (voice continues)
        s0, s1 = B.snap(f, st, st + 3.0)
        cid = f"T{ci + 1:02d}"
        CARDS.append({"id": cid, "type": "title", "w": 1920, "h": 1080, "kicker": f"Chapter {ci + 1}", "title": title,
                      "dur": round(s1 - s0 + 0.6, 2)})
        segs.append({"clip": B.FILES[f], "start": s0, "end": s1, "chapter": title, "tighten": 0, "nocaps": True,
                     "broll": {"file": f"projects/carrie-ep01/cards/{cid}.mp4", "push": 0}})
        cur = s1
        ins = sorted([x for x in INS if x[0] == f and st <= x[1] < en and x[1] >= cur])
        for k, (_, a, b, card) in enumerate(ins):
            a, b = B.snap(f, a, min(b, a + 7.0))
            if a - cur > 0.3:
                segs.append({"clip": B.FILES[f], "start": cur, "end": a})
            iid = f"{part}_i{len(CARDS)}"
            CARDS.append({"id": iid, **wide_card(card, b - a)})
            segs.append({"clip": B.FILES[f], "start": a, "end": b, "tighten": 0,
                         "broll": {"file": f"projects/carrie-ep01/cards/{iid}.mp4", "push": 0}})
            cur = b
        if en - cur > 0.3:
            segs.append({"clip": B.FILES[f], "start": cur, "end": round(en, 3)})
    spec = {"_piece": True, "id": f"L_{part}", "slug": "body", "format": "long", "title": f"Body {part}", "topic": "long-form part",
            "auto_frame": AF, "tighten": 0.6, "captions": "none", "fixes": B.FIX, "accent": B.ACCENT, "segments": segs}
    if part == "P1":  # intro: names once, captions through the opening exchange
        spec.update(captions="minimal", captions_until=25,
                    names=[{"at": 3.5, "dur": 4.0, "name": "Carrie Mullin Innes", "role": B.NAMES["C"][1], "x": 0.55, "y": 0.70},
                           {"at": 8.0, "dur": 4.0, "name": "Nizam", "role": B.NAMES["N"][1], "x": 0.06, "y": 0.70}])
    return spec


BEATS = {  # (file, start, end, who, {fr: from-phrase, to: to-phrase, bw})
 "salt": ("A", "12:56.0", "13:06.8", "N", {"fr": "can see salt", "to": "everywhere"}),
 "fall": ("A", "14:33.0", "14:40.0", "N", {"bw": True, "fr": "in high", "to": "not going to quit"}),
 "shake": ("B", "34:23.7", "34:27.5", "C", {"fr": "because i just think", "to": "not enough for you"}),
 "kilo": ("A", "20:57.0", "21:14.3", "C", {"fr": "if you went in at 74", "to": "didn't replace"}),
 "caffeine": ("A", "26:42.7", "26:49.3", "C", {"fr": "it's making you believe", "to": "perceived effort"}),
 "fruit": ("B", "14:56.2", "15:00.0", "C", {"fr": "if you had another one", "to": "eating fruit"}),
 "chatgpt": ("A", "09:12.0", "09:20.6", "N", {"fr": "before i started", "to": "my dietitian"}),
 "carbs": ("B", "19:02.2", "19:12.3", "N", {"fr": "i have just loaded", "to": "and other stuff"}),
 "mass": ("B", "46:37.2", "46:50.3", "C", {"bw": True, "fr": "you might not be able", "to": "workout in the morning"}),
 "gels": ("A", "16:55.9", "17:02.7", "N", {"fr": "so i had just two gels", "to": "course of 1 42"}),
 "twice": ("A", "27:47.9", "27:56.1", "N", {"fr": "the last one i took twice", "to": "because i cramped"}),
 "vitd": ("A", "11:54.5", "12:01.9", "C", {"fr": "but the maximum amount", "to": "in a day is 4 000"}),
 "plenty": ("B", "04:34.0", "04:50.5", "C", {"fr": "and that's plenty of protein", "to": "about protein intake"}),
 "cook": ("B", "26:44.0", "26:49.4", "C", {"fr": "i'm hearing that you come home", "to": "make anything"}),
 "cliff_q": ("B", "41:46.0", "41:57.2", "N", {"fr": "can i be in good shape", "to": "more muscle mass"}),
 "cliff_a": ("B", "42:02.8", "42:07.8", "C", {"fr": "i honestly think", "to": "can you gain muscle"}),
 "cliff1_q": ("A", "29:43.5", "29:49.4", "N", {"fr": "so for the next four months", "to": "get faster"}),
 "cliff1_a": ("A", "29:53.3", "29:58.4", "C", {"fr": "because with getting stronger", "to": "you have to make sure"}),
}
OPENS = {
 "CO1": (["fall", "salt", "kilo", "caffeine", "gels", "chatgpt", "shake", "carbs", "fruit", "mass", "cliff_q", "cliff_a"],
         {"kicker": "Nizam x Carrie Mullin Innes", "title": "Fuelling Like an Endurance Athlete", "sub": "a real sports-dietitian consult"}),
 "CO2": (["fall", "salt", "kilo", "gels", "twice", "caffeine", "vitd", "chatgpt", "cliff1_q", "cliff1_a"],
         {"kicker": "Part 1", "title": "Hydration, Cramps and Race Fuelling", "sub": "Nizam x Carrie Mullin Innes"}),
 "CO3": (["shake", "plenty", "carbs", "fruit", "cook", "mass", "cliff_q", "cliff_a"],
         {"kicker": "Part 2", "title": "Daily Eating, Protein and Recovery", "sub": "Nizam x Carrie Mullin Innes"}),
}


def cold_open(cid):
    keys, title = OPENS[cid]
    segs = []
    for k in keys:
        b = BEATS[k]; f = b[0]; o = b[4] if len(b) > 4 else {}
        s, e = B.snap(f, B.sec(b[1]), B.sec(b[2]))
        s, e = B.anchor(f, s, e, o.get("fr"), o.get("to"))
        nxt = [w[0] for w in B.words(f) if e - 0.115 < w[0] < e and w[0] > s + 0.3]
        if nxt:
            e = round(min(nxt) - 0.02, 3)
        seg = {"clip": B.FILES[f], "start": s, "end": e, "cx": "left" if b[3] == "N" else "right",
               "zoom": 1.9 if b[3] == "N" else 1.55, "cy": 0.38}
        if o.get("bw"):
            seg["look"] = "bw"
        segs.append(seg)
    segs[-1]["end"] = round(segs[-1]["end"], 3)
    tid = f"{cid}_title"
    CARDS.append({"id": tid, "type": "title", "w": 1920, "h": 1080, "dur": 3.6, **title})
    segs.append({"clip": B.FILES["A"], "start": 0.0, "end": 3.5, "nocaps": True, "tighten": 0, "mute": True,
                 "broll": {"file": f"projects/carrie-ep01/cards/{tid}.mp4", "push": 0}})
    return {"_piece": True, "id": f"L_{cid}", "slug": "open", "format": "long", "title": f"Cold open {cid}", "topic": "cold open",
            "tighten": 0.35, "captions": "lockup", "cap_y": 0.80, "accent": B.ACCENT, "fixes": B.FIX,
            "keywords": ["fall", "salt", "kilo", "harder", "two gels", "ChatGPT", "not enough", "carbs", "fruit", "mass",
                         "muscle", "twice", "4,000", "plenty", "consistency", "energy"],
            "segments": segs, "sfx": [{"at": 0.0, "file": "whoosh_slow.mp3", "vol": 0.3}]}


if __name__ == "__main__":
    for p in PARTS:
        json.dump(body(p), open(os.path.join(LONG, f"L_{p}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for c in OPENS:
        json.dump(cold_open(c), open(os.path.join(LONG, f"L_{c}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump({"accent": B.ACCENT, "cards": CARDS}, open(os.path.join(EP, "cards_long.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(len(CARDS), "long cards;", ", ".join(sorted(os.listdir(LONG))))
