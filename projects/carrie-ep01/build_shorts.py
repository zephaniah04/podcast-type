#!/usr/bin/env python3
"""Carrie ep01: the 25-short plan -> cards.json + clips/C01..C25.json (run, then render with scripts/podcast.py).

Each part = (file, "mm:ss.s", "mm:ss.s", who, opts). file A = IMG_4342-001, B = IMG_4343-002. who N = Nizam (left), C = Carrie
(right), W = wide (letterbox two-shot). Times are snapped to word boundaries from the transcript.
opts: card={...} (card panel top half while this part plays), bw=True ("before / mistake" beat), zoom=x (punch).
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.argv = sys.argv[:1]
import podcast as P  # noqa: E402

EP = os.path.join(ROOT, "projects", "carrie-ep01")
TX = os.path.join(EP, "tx")
FILES = {"A": "IMG_4342-001", "B": "IMG_4343-002"}
ACCENT = "#FFB238"
GAP = 0.35
FIX = {"high rocks": "HYROX", "high rods": "HYROX", "hydrox": "HYROX", "hyrox": "HYROX", "high rock": "HYROX",
       "gait rate": "Gatorade", "elani": "Alani", "lani": "Alani", "omega -3": "omega-3", "omega 3": "omega-3",
       "o 'clock": "o'clock", "pre -workout": "pre-workout", "hard -boiled": "hard-boiled", "go -to": "go-to",
       "iron one chat, gpd": "Ironman, ChatGPT", "chat gpt": "ChatGPT", "cops": "calves", "camping": "cramping",
       "minute -for -minute": "minute-for-minute", "anti -inflammatory": "anti-inflammatory", "150 -ish": "150-ish",
       "multi -vitamin": "multivitamin", "6 p .m.": "6 p.m.", "mils": "ml", "1.42": "1:42", "fence": "fins",
       "lmnt": "LMNT", "forgot about calves": "forgot about carbs", "1 .42": "1:42", "1 .2": "1.2", "1 .5": "1.5", "ious": "IUs", "ius": "IUs", "salami": "salad", "roadie": "roti", "boon river": "Bow River",
       "two x": "2x", "homo milk": "homo milk", "1,000 ius": "1,000 IUs"}
NAMES = {"N": ("Nizam", "Training to become an endurance athlete"),
         "C": ("Carrie Mullin Innes", "High-Performance Sports Dietitian · IOC Dip. Sports Nutrition")}

_words = {}


def words(f):
    if f not in _words:
        d = json.load(open(os.path.join(TX, FILES[f] + ".json"), encoding="utf-8"))
        _words[f] = [(w[0], w[1]) for sg in d for w in sg["w"] if w[2].strip()]
    return _words[f]


def sec(t):
    m, s = t.split(":"); return int(m) * 60 + float(s)


def snap(f, s, e):
    ws = words(f)
    st = min((w for w in ws if w[0] >= s - 0.35), key=lambda w: abs(w[0] - s))[0]
    en = min((w for w in ws if w[1] <= e + 0.35), key=lambda w: abs(w[1] - e))[1]
    return round(max(st - 0.08, 0), 3), round(en + 0.12, 3)


# exact sentence edges: "Cnn.i": (from-phrase, to-phrase, start override, end override)
EDGES = {
 "C01.0": (None, "lot of salt", None, None), "C01.1": ("if i do my", "after my run", None, None),
 "C01.2": ("while i end", None, None, None), "C01.3": (None, "electrolyte drinks", None, None),
 "C01.4": ("i have like gait", None, None, None),
 "C02.0": ("i don't know if", None, None, None), "C02.1": ("if you weigh yourself before", "lost a kilo", "20:45.5", None),
 "C02.2": ("that means", "didn't replace", None, None), "C02.3": ("because as you're", None, None, None),
 "C02.4": ("if it's really off", None, None, None),
 "C03.0": ("in high", None, None, None), "C03.1": ("i cramp a lot", None, None, None),
 "C03.4": ("there's a little bit of debate", "see if it helps", None, None),
 "C04.0": ("during my races", None, None, None), "C04.1": ("so i had just two gels", "course of 1 42", "16:57.0", None),
 "C04.2": ("i still think", None, None, None), "C04.3": (None, "because i cramped", None, None),
 "C04.4": (None, "bit more", None, "28:09.5"),
 "C05.0": ("like when i have", "what difference does it make", None, None),
 "C05.1": ("they're basically a stimulant", None, "26:29.0", None),
 "C06.0": ("so one packet", None, None, None), "C06.1": ("i just pulled up", "find out what it is", "25:01.0", None),
 "C06.2": ("that is a lot", "salty sweater", None, None), "C06.3": ("to train with it", None, None, None),
 "C07.0": ("do you take", None, None, None), "C07.1": ("you should", None, None, None),
 "C07.2": ("every day", None, None, None),
 "C08.0": ("before i started", "omega tablets after that", None, None), "C08.1": (None, "burn the fat", None, None),
 "C08.3": (None, "end of the world", None, None),
 "C09.1": (None, "might lie", None, None), "C09.4": (None, "you'd be okay", None, "07:11.0"),
 "C10.0": ("so when you're at the gym", "every 10 minutes", "33:04.5", "33:15.0"),
 "C10.2": ("when i go to the gym", "almost between every set", None, None),
 "C10.3": ("if you're working out in the morning", "between every set", None, None),
 "C11.0": ("you're doing it fasted", "wanting to gain mass", "34:28.5", None),
 "C11.3": (None, "through the workout", None, None), "C11.4": (None, "peanut butter on toast", None, None),
 "C12.1": (None, "i just heard it", None, None), "C12.2": ("as far as we know", None, None, None),
 "C12.3": (None, "your shake as is", None, None),
 "C13.2": (None, "than just that protein shake", None, None),
 "C14.0": (None, "and get faster", None, "29:49.4"), "C14.1": ("because with getting stronger", None, None, None),
 "C14.2": (None, "fine balance", None, None), "C14.3": ("for high", "to do the gym", "31:18.5", None),
 "C15.2": ("you could look at it another way", "response to creatine", "02:30.0", None),
 "C15.3": ("the way it works", None, None, None), "C15.4": ("just taking the one little scoop", "you could do that", "03:31.0", None),
 "C16.0": ("i did my math", None, None, None), "C16.1": (None, "about protein intake", None, "04:50.5"),
 "C17.0": ("typically people need", None, None, None), "C17.2": (None, "enough in your day", None, None),
 "C17.4": ("so like your lunch", None, None, None),
 "C18.0": ("in our office", None, None, None),
 "C19.0": ("i have just loaded", None, None, None), "C19.1": ("before the 6", None, None, None),
 "C19.2": (None, "just before you do it", None, None), "C19.3": (None, "before you go", None, None),
 "C20.0": ("do you think realistically", "more muscle mass", "41:39.0", "41:57.2"),
 "C20.1": ("can you gain muscle mass", "follow up to see", None, None),
 "C20.2": ("because the training itself", "fueling yourself well enough", None, None),
 "C21.0": ("let's say you're now doing", None, None, None), "C21.1": (None, "then the gym", None, "28:24.2"),
 "C21.2": (None, "finish it afterwards", None, "28:49.0"), "C21.3": (None, "doing resistance training", None, None),
 "C22.0": ("if you can't make that meal", "sitting in your fridge", "25:12.0", "25:31.0"),
 "C22.1": ("i'm hearing that you come home", "make anything", None, None),
 "C22.2": ("if you don't feel like cooking", "doing a sandwich", None, None), "C22.4": (None, "in the shell, okay", None, None),
 "C23.0": ("what some people do", None, None, None), "C23.2": ("here's three recipes", "to make it", None, "44:31.0"),
 "C23.3": ("i think i can spare", None, "44:29.0", None), "C23.4": ("do you have hash browns", None, None, None),
 "C24.1": (None, "did a banana", None, None), "C24.2": (None, "workout in the morning", None, None),
 "C24.3": ("there's no energy", None, None, None),
 "C25.0": ("or you take a multi", None, None, None), "C25.1": ("why don't we put", "fiber to your diet", None, None),
 "C25.2": ("and it's going to add natural", None, "49:00.5", None),
}


def anchor(f, s, e, frm, to):
    """Move s / e onto the exact phrase (first match of `frm` near the start, first match of `to` ending near e)."""
    d = json.load(open(os.path.join(TX, FILES[f] + ".json"), encoding="utf-8"))
    ws = [(w[0], w[1], P.bare(w[2])) for sg in d for w in sg["w"] if P.bare(w[2])]
    def find(ph, lo, hi, last=False):
        k = [P.bare(x) for x in ph.split() if P.bare(x)]
        hits = [i for i in range(len(ws) - len(k) + 1) if lo <= ws[i][0] <= hi and [w[2] for w in ws[i:i + len(k)]] == k]
        return (hits[-1] if last else hits[0], len(k)) if hits else (None, 0)
    if frm:
        i, n = find(frm, s - 2.0, e)
        if i is None:
            raise SystemExit(f"from-phrase '{frm}' not found {f} {s}-{e}")
        s = round(max(ws[i][0] - 0.08, 0), 3)
        if i > 0:  # start after the previous word has ended
            s = round(max(s, ws[i - 1][1] + 0.02), 3)
    if to:
        i, n = find(to, s, e + 1.0)
        if i is None:
            raise SystemExit(f"to-phrase '{to}' not found {f} {s}-{e}")
        e = round(ws[i + n - 1][1] + 0.12, 3)
        if i + n < len(ws):  # stop before the next word starts
            e = round(min(e, ws[i + n][0] - 0.02), 3)
    return s, e


def out_dur(seg, gap):
    g = seg.get("tighten", gap)
    pieces = P.tighten(seg, TX, float(g), True) if g else [seg]
    return sum(round((p["end"] - p["start"]) * 30) / 30 for p in pieces)


CARDS = []


def build(c):
    look = c["look"]
    spec = {"id": c["id"], "slug": c["slug"], "title": c["title"], "topic": c["topic"], "format": "short",
            "look_name": {"A": "A letterbox lockup", "B": "B creator hyper-edit", "C": "C clean minimal"}[look],
            "accent": ACCENT, "fixes": FIX, "keywords": c.get("keywords", []), "tighten": GAP, "segments": [],
            "names": [], "sfx": []}
    if look == "A":
        spec.update(layout="letterbox", captions="lockup", cap_y=0.76)
    elif look == "B":
        spec.update(layout="full", captions="creator", cap_y=0.62, jump_zoom=[1.42, 1.6])
    else:
        spec.update(layout="full", captions="minimal", cap_y=0.70, jump_zoom=[1.42, 1.58])
    t = 0.0; seen = set(); k = 0
    for pi, part in enumerate(c["parts"]):
        f, a, b, who = part[:4]; o = part[4] if len(part) > 4 else {}
        ed = EDGES.get(f"{c['id']}.{pi}")
        if ed and ed[2]:
            a = ed[2]
        if ed and ed[3]:
            b = ed[3]
        s, e = snap(f, sec(a), sec(b))
        if ed:
            s, e = anchor(f, s, e, ed[0], ed[1])
        # never let the end pad catch the first sound of the next word
        nxt = [w[0] for w in words(f) if e - 0.12 + 0.005 < w[0] < e and w[0] > s + 0.3]
        if nxt:
            e = round(min(nxt) - 0.02, 3)
        seg = {"clip": FILES[f], "start": s, "end": e}
        side = {"N": "left", "C": "right"}.get(who)
        if look == "A":
            seg["cx"] = 0.5 if who == "W" else side
            seg["zoom"] = 1.0 if who == "W" else o.get("zoom", 1.35)
            seg["cy"] = 0.5 if who == "W" else 0.40
            if not spec["segments"]:
                seg["open"] = True
        else:
            seg["cx"] = side or 0.5
            seg["cy"] = 0.36
            if "zoom" in o:
                seg["zoom"] = o["zoom"]
        if o.get("bw"):
            seg["look"] = "bw"
        if o.get("card"):
            k += 1
            cid = f"{c['id']}_{k}"
            card = {"id": cid, "w": 1080, "h": 960, **o["card"]}
            card["dur"] = round(e - s + 0.8, 2)
            CARDS.append(card)
            seg.update(broll={"file": f"projects/carrie-ep01/cards/{cid}.mp4", "panel": "top", "push": 0},
                       zoom=2.0, cy=0.26, tighten=0)
            seg.pop("open", None)
            spec["sfx"].append({"at": round(t, 2), "file": "whoosh_soft.mp3", "vol": 0.35})
        d = out_dur(seg, GAP)
        if look == "B" and who in NAMES and who not in seen and not o.get("card"):
            nm, role = NAMES[who]
            if d > 1.6:
                spec["names"].append({"at": round(t + 0.25, 2), "dur": round(min(2.6, d - 0.45), 2), "name": nm, "role": role, "y": 0.47})
        if who in NAMES:
            seen.add(who)
        for ov in o.get("stamp", []):
            spec.setdefault("stamps", []).append({"at": round(t + ov.get("dt", 0.2), 2), "text": ov["text"], "color": ACCENT,
                                                  "dur": ov.get("dur", 1.3), "y": ov.get("y", 0.20)})
        if o.get("counter"):
            cn = o["counter"]
            spec.setdefault("counters", []).append({"at": round(t + cn.get("dt", 0.3), 2), "dur": cn.get("dur", 2.6), "from": 0,
                                                    "to": cn["to"], "suffix": cn.get("suffix", ""), "label": cn["label"], "y": cn.get("y", 0.22)})
        spec["segments"].append(seg)
        t += d
    if c.get("hook"):
        spec["hook"] = {"text": c["hook"], "until": 999 if look == "A" else c.get("hook_until", 3.0), "y": 0.19 if look == "A" else 0.11}
    if look == "A":
        spec["sfx"].append({"at": 0.0, "file": "whoosh_soft2.mp3", "vol": 0.3})
    spec["_est"] = round(t, 1)
    return spec


# ----------------------------------------------------------------------------------------------- the 25 shorts
S = [
 dict(id="C01", slug="salty-sweater", look="B", title="How to know you're a salty sweater", topic="Sodium / sweat",
      hook=["Salt on your face", "after a run?"], keywords=["salt", "electrolyte", "sodium"],
      parts=[("A", "12:30.4", "12:33.3", "C"),
             ("A", "12:38.0", "12:51.3", "N"),
             ("A", "12:51.4", "13:06.8", "N", {"zoom": 1.6}),
             ("A", "13:07.9", "13:19.0", "C", {"card": {"type": "list", "title": "Salty sweater? Compensate", "items": ["More salt in your diet", "Electrolyte drinks"], "at": [3.0, 6.8]}}),
             ("A", "13:19.1", "13:30.6", "N"),
             ("A", "21:57.5", "22:00.9", "C", {"zoom": 1.6})]),
 dict(id="C02", slug="sweat-test", look="B", title="The 1 kg = 1 litre sweat test", topic="Hydration",
      hook=["Do this before", "your next long run"], keywords=["deficit", "kilo", "liter"],
      parts=[("A", "19:48.5", "19:57.4", "C"),
             ("A", "20:50.9", "21:05.7", "C"),
             ("A", "21:05.7", "21:14.3", "C", {"card": {"type": "bignum", "value": 1, "suffix": " L", "label": "of sweat lost per kilo", "kicker": "74 kg -> 73 kg", "sub": "that you didn't replace"}}),
             ("A", "21:19.2", "21:35.8", "C", {"card": {"type": "list", "title": "Rehydrate", "numbered": True, "items": ["Weigh before (no clothes)", "Weigh after", "Drink the loss", "+250-500 ml extra"], "at": [0.3, 0.8, 1.5, 5.0]}}),
             ("A", "21:49.7", "21:57.3", "C", {"zoom": 1.6})]),
 dict(id="C03", slug="cramp-story", look="C", title="Cramping in HYROX: 'If I fall, take me out'", topic="Cramping",
      hook=["\"If I fall,", "just take me out\""], hook_until=3.2, keywords=[],
      parts=[("A", "14:33.0", "14:40.0", "N"),
             ("A", "13:49.8", "14:07.3", "N"),
             ("A", "14:19.0", "14:32.6", "N"),
             ("A", "14:51.6", "14:58.3", "N"),
             ("A", "15:56.8", "16:12.4", "C")]),
 dict(id="C04", slug="two-gels", look="B", title="2 gels in 1:42 of racing isn't enough", topic="Race fuelling",
      hook=["Your last 1K", "took twice as long?"], keywords=["carbs", "consistency", "gels"],
      parts=[("A", "16:40.5", "16:53.8", "N"),
             ("A", "16:55.9", "17:02.7", "N", {"card": {"type": "bignum", "value": 2, "suffix": " gels", "label": "in 1 h 42 min of HYROX", "kicker": "what I used", "count": False}}),
             ("A", "27:22.1", "27:46.9", "C"),
             ("A", "27:47.9", "27:56.1", "N", {"card": {"type": "versus", "title": "First 1K vs last 1K", "left": {"title": "Few carbs", "lines": ["Last 1K: 2x slower"]}, "right": {"title": "Carbs all race", "lines": ["Last 1K as good as the first"]}, "delay": 2.5}}),
             ("A", "28:01.6", "28:07.2", "C", {"zoom": 1.6})]),
 dict(id="C05", slug="caffeine-gel", look="B", title="Caffeine gel vs carb gel: what's the difference?", topic="Caffeine",
      hook=["Caffeine gel", "or carb gel?"], keywords=["stimulant", "perceived effort", "gut"],
      parts=[("A", "26:08.8", "26:21.9", "N"),
             ("A", "26:35.6", "26:49.3", "C"),
             ("A", "26:50.1", "27:11.7", "C", {"card": {"type": "dodont", "title": "Caffeine in long races", "dont": ["Use it all race long", "Upset your gut"], "do": ["Save it for the end", "When you need a push"], "delay": 4.0}})]),
 dict(id="C06", slug="1000mg-sodium", look="B", title="1,000 mg of sodium in one packet", topic="Electrolytes",
      hook=["1,000 mg of sodium", "in ONE packet"], keywords=["sodium", "salty sweater", "train"],
      parts=[("A", "25:33.0", "25:39.4", "C", {"card": {"type": "bignum", "value": 1000, "suffix": " mg", "label": "sodium in one packet", "kicker": "no-carb electrolyte"}}),
             ("A", "25:06.6", "25:18.9", "C"),
             ("A", "25:39.6", "25:51.5", "C", {"zoom": 1.6}),
             ("A", "25:51.5", "26:02.9", "C")]),
 dict(id="C07", slug="vitamin-d", look="B", title="Vitamin D: October to April, every day", topic="Supplements",
      hook=["Take this every day", "October to April"], keywords=["vitamin D", "4,000", "bone"],
      parts=[("A", "10:26.7", "10:32.6", "C"),
             ("A", "10:55.6", "11:06.0", "C"),
             ("A", "11:06.0", "11:17.9", "C", {"card": {"type": "bignum", "value": 1000, "suffix": " IU", "label": "vitamin D a day", "kicker": "October -> April", "sub": "we can't get enough from food"}}),
             ("A", "11:54.5", "12:01.9", "C", {"stamp": [{"text": "MAX 4,000 IU", "dt": 1.6, "y": 0.2}]}),
             ("A", "12:07.6", "12:16.2", "C", {"card": {"type": "list", "title": "Why it matters", "items": ["Bone strength", "Immunity", "Inflammation"], "at": [2.2, 4.3, 5.4]}})]),
 dict(id="C08", slug="chatgpt-dietitian", look="B", title="ChatGPT was my dietitian. Omega-3 doesn't burn fat", topic="Supplements myths",
      hook=["ChatGPT was", "my dietitian"], keywords=["ChatGPT", "burn", "carbs and protein"],
      parts=[("A", "09:12.0", "09:33.1", "N"),
             ("B", "00:29.4", "00:35.8", "N"),
             ("B", "00:39.0", "00:55.7", "C", {"zoom": 1.6}),
             ("B", "01:11.7", "01:24.0", "C")]),
 dict(id="C09", slug="water-2-2-litres", look="B", title="You probably need only 2.2 L of water", topic="Hydration",
      hook=["How much water", "do you really need?"], keywords=["2.2", "sweat"],
      parts=[("A", "06:04.7", "06:08.1", "C"),
             ("A", "06:10.5", "06:13.2", "N"),
             ("A", "06:15.3", "06:17.9", "N"),
             ("A", "06:36.6", "06:51.4", "C", {"card": {"type": "bignum", "value": 2.2, "decimals": 1, "suffix": " L", "label": "a day at 74 kg", "kicker": "based on body weight", "sub": "more on heavy-sweat days"}}),
             ("A", "06:51.6", "07:06.6", "C")]),
 dict(id="C10", slug="drink-every-set", look="B", title="Why you wake up dehydrated (morning gym)", topic="Hydration",
      hook=["Training in the morning?", "You start dehydrated"], keywords=["every set", "drier", "heavy sweater"],
      parts=[("A", "33:07.1", "33:12.5", "C"),
             ("A", "33:15.0", "33:18.4", "N"),
             ("A", "33:38.4", "34:04.0", "C"),
             ("A", "34:04.0", "34:25.5", "C", {"card": {"type": "list", "title": "Morning gym", "items": ["You wake up drier", "No water all night", "Sip between every set"], "at": [1.2, 3.6, 17.0]}})]),
 dict(id="C11", slug="fasted-gym", look="B", title="Training fasted? Eat this first", topic="Pre-workout",
      hook=["Lifting fasted", "to gain muscle?"], keywords=["fasted", "blood sugar", "banana", "peanut butter"],
      parts=[("A", "34:30.1", "34:42.6", "N"),
             ("A", "34:43.8", "34:56.4", "C"),
             ("A", "35:02.7", "35:03.4", "N"),
             ("A", "35:30.6", "35:40.4", "C", {"zoom": 1.6}),
             ("A", "35:40.4", "35:59.1", "C", {"card": {"type": "list", "title": "Before a morning lift", "items": ["Banana", "+ peanut butter", "or PB on toast"], "at": [0.6, 2.6, 15.0]}})]),
 dict(id="C12", slug="30-minute-window", look="B", title="The 30-minute protein window, explained", topic="Recovery timing",
      hook=["Is it really", "30 minutes?"], keywords=["two hours", "30 minutes", "sooner"],
      parts=[("A", "38:18.0", "38:30.0", "N"),
             ("A", "38:30.1", "38:33.0", "N"),
             ("A", "38:33.0", "38:48.2", "C", {"card": {"type": "versus", "title": "When to refuel", "left": {"title": "1 workout today", "lines": ["Within 2 hours"]}, "right": {"title": "2 workouts today", "lines": ["Within 30 minutes"]}, "delay": 5.0}}),
             ("A", "38:49.3", "39:03.2", "C", {"zoom": 1.6})]),
 dict(id="C13", slug="shake-not-enough", look="A", title="A protein shake alone won't recover you", topic="Recovery",
      hook=["A protein shake", "is NOT a meal"], keywords=["never", "not enough", "real food", "something"],
      parts=[("A", "02:26.4", "02:35.4", "C"),
             ("A", "02:35.7", "02:50.8", "C"),
             ("B", "34:05.3", "34:16.2", "C"),
             ("B", "34:23.7", "34:27.5", "C"),
             ("B", "34:39.8", "34:43.8", "W")]),
 dict(id="C14", slug="fine-balance", look="C", title="Gain muscle without getting slower", topic="Body composition",
      hook=["Stronger AND faster", "in 4 months?"], keywords=[],
      parts=[("A", "29:34.6", "29:48.0", "N"),
             ("A", "29:49.5", "30:05.0", "C"),
             ("A", "30:05.1", "30:28.0", "C"),
             ("A", "31:21.2", "31:38.4", "C")]),
 dict(id="C15", slug="creatine", look="B", title="What creatine actually does", topic="Supplements",
      hook=["Creatine:", "what it really does"], keywords=["ATP", "power", "training tool"],
      parts=[("B", "01:30.8", "01:35.0", "C"),
             ("B", "01:38.3", "01:46.9", "N"),
             ("B", "02:32.9", "02:41.8", "C"),
             ("B", "02:41.8", "02:58.5", "C", {"card": {"type": "list", "title": "How creatine helps", "numbered": True, "items": ["Regenerates ATP faster", "More power", "Muscle builds faster"], "at": [5.0, 10.0, 14.0]}}),
             ("B", "03:32.5", "03:41.3", "C")]),
 dict(id="C16", slug="protein-enough", look="A", title="50 g of protein is plenty", topic="Protein",
      hook=["1,000-calorie shake,", "50 g protein"], keywords=["plenty", "protein intake", "muscle"],
      parts=[("B", "04:16.5", "04:33.3", "N", {"counter": {"to": 1000, "label": "calories in my shake", "dt": 4.0, "y": 0.80}}),
             ("B", "04:34.0", "04:47.8", "C")]),
 dict(id="C17", slug="5-hour-gap", look="B", title="The 5-hour gap that kills your evening session", topic="Meal timing",
      hook=["Lunch at 1,", "training at 6?"], keywords=["three to five", "energy stores", "five hours"],
      parts=[("B", "12:33.6", "12:56.0", "C"),
             ("B", "12:57.8", "13:04.1", "N"),
             ("B", "13:05.3", "13:16.5", "C"),
             ("B", "14:07.8", "14:17.0", "C"),
             ("B", "14:17.1", "14:28.8", "C", {"card": {"type": "timeline", "title": "Don't train on empty", "points": [{"t": "1 pm", "label": "Lunch", "at": 0.4}, {"t": "3-4 pm", "label": "Snack / fruit", "at": 1.6}, {"t": "6 pm", "label": "Training", "at": 8.4}]}})]),
 dict(id="C18", slug="fruit", look="A", title="No one gets overweight from eating fruit", topic="Snacks",
      hook=["Banana, apple,", "orange. Every day."], keywords=["fruit", "flexibility", "need"],
      parts=[("A", "05:27.8", "05:43.1", "N"),
             ("B", "14:40.4", "14:50.8", "C"),
             ("B", "14:53.0", "14:55.6", "W"),
             ("B", "14:56.2", "15:10.7", "C")]),
 dict(id="C19", slug="forgot-carbs", look="B", title="I loaded up on protein and forgot carbs", topic="Pre-workout",
      hook=["\"I forgot", "about carbs\""], keywords=["blood sugar", "gel", "carbs", "prime"],
      parts=[("B", "19:02.2", "19:12.3", "N"),
             ("B", "18:15.5", "18:28.0", "C"),
             ("B", "18:28.5", "18:54.1", "C", {"card": {"type": "list", "title": "Prime before you train", "items": ["Fruit snacks", "Honey waffle", "A small bar", "A gel"], "at": [5.0, 7.5, 11.5, 22.0]}}),
             ("B", "19:13.3", "19:21.0", "C")]),
 dict(id="C20", slug="anyone-can-gain", look="A", title="Can I gain muscle in 4 months?", topic="Goals",
      hook=["Can I gain muscle", "before race day?"], keywords=["anyone", "huge response", "fueling"],
      parts=[("B", "41:37.0", "41:54.3", "N"),
             ("B", "42:02.8", "42:20.4", "C"),
             ("B", "42:33.7", "42:50.4", "C", {"zoom": 1.5})]),
 dict(id="C21", slug="eat-between-sessions", look="B", title="Cardio then gym? Eat in between", topic="Double sessions",
      hook=["Two sessions", "back to back?"], keywords=["tolerate", "stomach", "gym"],
      parts=[("B", "28:08.5", "28:21.2", "C"),
             ("B", "28:21.5", "28:23.4", "N"),
             ("B", "28:24.0", "28:44.3", "C", {"card": {"type": "timeline", "title": "Double session day", "points": [{"t": "Cardio", "label": "Run / bike", "at": 0.5}, {"t": "Eat", "label": "Between sessions", "at": 2.5}, {"t": "Gym", "label": "Strength", "at": 5.0}, {"t": "Finish", "label": "The rest after", "at": 15.5}]}}),
             ("B", "29:15.1", "29:29.2", "C")]),
 dict(id="C22", slug="no-cook-dinners", look="B", title="Too tired to cook after training? Eat this", topic="Quick meals",
      hook=["Too tired", "to cook tonight?"], keywords=["overnight oats", "sandwich", "eggs"],
      parts=[("B", "25:15.6", "25:26.8", "C"),
             ("B", "26:44.0", "26:49.4", "C"),
             ("B", "30:41.7", "30:49.2", "C"),
             ("B", "31:03.8", "31:21.9", "C", {"card": {"type": "list", "title": "No-cook recovery dinner", "items": ["Overnight oats", "2 tuna sandwiches", "Hard-boiled eggs"], "at": [0.4, 1.4, 2.4]}}),
             ("B", "31:21.9", "31:24.1", "N")]),
 dict(id="C23", slug="meal-prep", look="B", title="2 hours on Sunday = fed all week", topic="Meal prep",
      hook=["2 hours on Sunday", "= fed all week"], keywords=["meal prep", "weekend", "hacks"],
      parts=[("B", "43:38.4", "43:45.0", "C"),
             ("B", "43:45.0", "43:53.9", "C", {"card": {"type": "list", "title": "Weekend meal prep", "items": ["Chicken", "Rice", "Veggies", "Eat it all week"], "at": [0.4, 2.4, 3.9, 6.9]}}),
             ("B", "44:14.0", "44:27.0", "C"),
             ("B", "44:27.0", "44:37.0", "N"),
             ("B", "45:21.0", "45:38.4", "C")]),
 dict(id="C24", slug="skip-dinner", look="B", title="Skip dinner after a night session and this happens", topic="Recovery",
      hook=["Night workout,", "no dinner?"], keywords=["recovery", "build mass", "energy"],
      parts=[("B", "46:06.2", "46:16.5", "C"),
             ("B", "46:16.5", "46:36.3", "C", {"card": {"type": "timeline", "title": "The empty-tank cycle", "points": [{"t": "Night", "label": "Workout", "at": 1.5}, {"t": "Bed", "label": "Shake only", "at": 6.5}, {"t": "6 am", "label": "Gym + banana", "at": 13.5}]}}),
             ("B", "46:37.2", "46:50.3", "C", {"bw": True}),
             ("B", "46:50.3", "47:00.4", "C", {"zoom": 1.6})]),
 dict(id="C25", slug="real-food", look="A", title="What a multivitamin can't give you", topic="Micronutrients",
      hook=["Multivitamin", "or real food?"], keywords=["bottle", "phytochemicals", "fiber"],
      parts=[("B", "48:23.4", "48:34.6", "N"),
             ("B", "48:47.7", "49:02.5", "C"),
             ("B", "49:02.5", "49:19.7", "C", {"zoom": 1.5})]),
]

if __name__ == "__main__":
    os.makedirs(os.path.join(EP, "clips"), exist_ok=True)
    for c in S:
        sp = build(c)
        json.dump(sp, open(os.path.join(EP, "clips", c["id"] + ".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(c["id"], c["look"], sp["_est"], "s", c["slug"])
    json.dump({"accent": ACCENT, "cards": CARDS}, open(os.path.join(EP, "cards.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(len(CARDS), "cards")
