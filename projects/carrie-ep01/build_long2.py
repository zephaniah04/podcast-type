#!/usr/bin/env python3
"""Carrie ep01 long-form v2: the whole consult as ONE YouTube episode with B-roll, floating 3D elements, side cards,
split screens and captions all the way through.

Beats are pinned to the exact phrase in the transcript (searched near an approximate timecode):
  ("A", "12:56", "salt on my eyes", "br", "salt-sweat", 3.0)        full-frame B-roll photo for ~3 s from the phrase
  ("A", "06:36", "and so based on your", "card", {...}, "just so you know")   side card until the to-phrase
  ("A", "12:30", "how do you know that", "sbs", None, "i sweat and")          side-by-side split until the to-phrase
  ("A", "05:30", "one banana", "st", [("Banana", "1 banana")])                 floating 3D element(s) at the phrase
Renders as chunks (cold open + 4 body parts), then concat -> exports/carrie/ep01/L01_full-episode.mp4
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_shorts as B  # noqa: E402
import build_long as L  # noqa: E402  (chapters, END, cold-open beats)
P = B.P

EP = B.EP
OUT = os.path.join(EP, "long2"); os.makedirs(OUT, exist_ok=True)
AF = {"zoom": 1.8, "zoom_right": 1.5, "punch": 1.1, "wide_every": 4, "cy": 0.38, "min_turn": 1.6}
GAP = 0.6
CARDS, STICKERS = [], {}
ZN, ZC = 1.8, 1.5  # tight framing: Nizam / Carrie (Carrie wider: she sits at a desk, often in profile)

EV = [
 # ---------------------------------------------------------------- file A (IMG_4342)
 ("A", "01:13", "food record", "br", "food-diary", 3.0),
 ("A", "01:20", "around 637", "st", [("Alarm clock", "6:37 am")]),
 ("A", "01:36", "my milkshake", "st", [("Glass of milk", "milkshake")]),
 ("A", "01:43", "overcooked eggs", "st", [("Egg", "2 eggs")]),
 ("A", "01:46", "guacamole", "st", [("Avocado", "guacamole")]),
 ("A", "01:59", "greek yogurt at work", "br", "yogurt-granola", 3.4),
 ("A", "02:12", "a little honey", "st", [("Honey pot", "+ honey")]),
 ("A", "02:33", "worked out at night", "br", "night-run", 3.0),
 ("A", "02:40", "protein shake", "st", [("Cup with straw", "just a shake?")]),
 ("A", "03:25", "rice with chicken", "br", "chicken-rice", 3.2),
 ("A", "05:00", "more veggies", "st", [("Broccoli", "more veggies"), ("Carrot", ""), ("Leafy green", "")]),
 ("A", "05:15", "between one and nine", "st", [("Stopwatch", "1 pm -> 9 pm?")]),
 ("A", "05:31", "one banana", "st", [("Banana", "1 banana")]),
 ("A", "05:32", "one apple", "st", [("Red apple", "1 apple")]),
 ("A", "05:33", "one orange", "st", [("Tangerine", "1 orange")]),
 ("A", "05:49", "a sip of", "st", [("Droplet", "just a sip")]),
 ("A", "06:04", "and how much water", "sbs", None, "two liters ish"),
 ("A", "06:36", "and so based on your", "card", {"type": "bignum", "value": 2.2, "decimals": 1, "suffix": " L", "label": "of water a day", "kicker": "at 74 kg", "sub": "more on heavy-sweat days"}, "just so you know"),
 ("A", "06:52", "really trained heavy", "br", "sweaty-athlete", 3.0),
 ("A", "07:28", "drumsticks", "st", [("Poultry leg", "chicken")]),
 ("A", "07:30", "tortilla or roti", "br", "roti", 3.0),
 ("A", "07:47", "rocks training", "br", "hyrox", 3.2),
 ("A", "08:19", "back in india", "br", "indian-food", 3.2),
 ("A", "08:59", "any supplements", "br", "supplements", 3.0),
 ("A", "09:16", "my dietitian", "st", [("Robot", "ChatGPT")]),
 ("A", "09:30", "omega tablets", "br", "fish-oil", 3.0),
 ("A", "09:33", "omega three", "st", [("Fish", "omega-3")]),
 ("A", "09:48", "multi -vitamin tablets", "br", "multivitamin", 3.0),
 ("A", "10:10", "whey protein powder", "br", "protein-powder", 3.0),
 ("A", "10:28", "vitamin d supplement in the winter", "br", "winter-sun", 3.2),
 ("A", "11:04", "october to april", "st", [("Sun", "Oct -> Apr")]),
 ("A", "11:07", "every day", "card", {"type": "bignum", "value": 1000, "suffix": " IU", "label": "vitamin D a day", "kicker": "October -> April", "sub": "we can't get enough from food"}, "would be fine"),
 ("A", "11:55", "maximum amount you should take", "st", [("Warning", "max 4,000 IU")]),
 ("A", "12:08", "but as long as you just take", "card", {"type": "list", "title": "Why vitamin D", "items": ["Bone strength", "Immunity", "Inflammation"], "at": [2.2, 4.3, 5.4]}, "things like that"),
 ("A", "12:30", "how do you know that you sweat", "sbs", None, "i sweat and"),
 ("A", "12:57", "salt on my eyes", "br", "salt-sweat", 3.0),
 ("A", "13:00", "on my cheek", "st", [("Salt", "salty sweater")]),
 ("A", "13:12", "electrolyte drinks", "br", "sports-drink", 3.0),
 ("A", "13:51", "i cramp a lot", "br", "cramp", 3.4),
 ("A", "14:20", "sandbag lunges", "br", "sandbag-lunge", 3.2),
 ("A", "15:26", "half ironman", "br", "ironman-bike", 3.2),
 ("A", "16:01", "there's a little bit of debate", "card", {"type": "versus", "title": "Why the cramps?", "left": {"title": "Muscle", "lines": ["Fatigue from new loads"]}, "right": {"title": "Sodium + fluid", "lines": ["Worth testing first"]}, "delay": 3.0}, "see if it helps"),
 ("A", "16:49", "just gels", "st", [("Stopwatch", "1-2 gels in 1:42")]),
 ("A", "16:58", "so i had just two gels", "card", {"type": "bignum", "value": 2, "suffix": " gels", "label": "in 1 h 42 min of HYROX", "kicker": "what I used", "count": False}, "course of 1 42"),
 ("A", "17:06", "after my row", "br", "rowing-machine", 2.8),
 ("A", "19:02", "carry water in the event", "br", "race-water-cups", 3.2),
 ("A", "19:54", "a wait before", "st", [("Balance scale", "weigh before + after")]),
 ("A", "21:00", "if you went in at 74", "card", {"type": "bignum", "value": 1, "suffix": " L", "label": "of sweat per kilo lost", "kicker": "74 kg -> 73 kg", "sub": "that you didn't replace"}, "didn't replace"),
 ("A", "21:20", "because as you're", "card", {"type": "list", "title": "Rehydrate", "numbered": True, "items": ["Weigh before", "Weigh after", "Drink the loss", "+250-500 ml"], "at": [0.3, 0.8, 1.5, 5.0]}, 15.0),
 ("A", "22:16", "sports drink instead", "st", [("Cup with straw", "sports drink")]),
 ("A", "23:16", "sodium tablets", "br", "salt-tablets", 3.0),
 ("A", "24:00", "fins on", "br", "swim-fins", 3.0),
 ("A", "24:07", "bike uphill", "br", "cycling-uphill", 3.0),
 ("A", "24:36", "muscle adaptation", "st", [("Flexed biceps", "adaptation")]),
 ("A", "25:34", "so one packet here", "card", {"type": "bignum", "value": 1000, "suffix": " mg", "label": "sodium in one packet", "kicker": "salty sweater?"}, "lot of sodium"),
 ("A", "26:12", "caffeine gel", "br", "coffee", 2.8),
 ("A", "26:17", "caffeine electrolyte", "st", [("Hot beverage", "caffeine")]),
 ("A", "26:43", "it's making you believe", "card", {"type": "dodont", "title": "Caffeine in long races", "dont": ["All race long", "Upset gut"], "do": ["Save it for the end", "For the final push"], "delay": 4.0}, "extra push"),
 ("A", "27:27", "scientifically", "card", {"type": "versus", "title": "Carbs in intervals", "left": {"title": "No carbs", "lines": ["Last 1K fades"]}, "right": {"title": "Carbs all race", "lines": ["Last 1K = first 1K"]}, "delay": 3.5}, "maintain consistency"),
 ("A", "28:38", "running is one of the key", "br", "runner-road", 3.0),
 ("A", "29:35", "gain muscle", "br", "weightlifting", 3.0),
 ("A", "30:23", "fine balance", "st", [("Balance scale", "fine balance")]),
 ("A", "33:09", "drinking water", "br", "gym-drink", 3.0),
 ("A", "34:10", "a little bit drier", "st", [("Droplet", "you wake up dry")]),
 ("A", "34:30", "you're doing it fasted", "sbs", None, "wanting to gain mass"),
 ("A", "35:03", "a banana", "st", [("Banana", "banana")]),
 ("A", "35:11", "peanut butter sandwich", "st", [("Peanuts", "peanut butter")]),
 ("A", "35:41", "so let's say something like a banana", "card", {"type": "list", "title": "Before a morning lift", "items": ["Banana", "+ peanut butter", "or PB on toast"], "at": [0.6, 2.6, 15.0]}, "peanut butter on toast"),
 ("A", "37:31", "carbs and protein in it", "st", [("Cup with straw", "carbs + protein")]),
 ("A", "38:23", "within the first two hours", "card", {"type": "versus", "title": "When to refuel", "left": {"title": "1 workout", "lines": ["Within 2 hours"]}, "right": {"title": "2 workouts", "lines": ["Within 30 min"]}, "delay": 4.0}, "workout two"),
 # ---------------------------------------------------------------- file B (IMG_4343)
 ("B", "00:47", "source of fat", "st", [("Fish", "just a source of fat")]),
 ("B", "01:33", "ever taken creatine", "br", "creatine", 3.0),
 ("B", "02:44", "the way it works", "card", {"type": "list", "title": "How creatine helps", "numbered": True, "items": ["Regenerates ATP", "More power", "Muscle builds faster"], "at": [1.5, 5.0, 9.0]}, "muscle faster"),
 ("B", "03:09", "biceps", "st", [("Flexed biceps", "")]),
 ("B", "04:23", "1000 calories", "st", [("Glass of milk", "1,000 kcal shake")]),
 ("B", "04:29", "roughly 45 to 50", "card", {"type": "bignum", "value": 50, "suffix": " g", "label": "protein in one shake", "kicker": "that's plenty"}, "more than that"),
 ("B", "06:24", "banana and dates", "st", [("Banana", "banana + dates")]),
 ("B", "07:52", "broccoli", "st", [("Broccoli", "broccoli")]),
 ("B", "07:53", "corn", "st", [("Ear of corn", "corn")]),
 ("B", "07:54", "carrots", "st", [("Carrot", "carrots")]),
 ("B", "08:02", "three to four eggs", "st", [("Egg", "3-4 eggs")]),
 ("B", "08:27", "add some veggies", "br", "veg-curry", 3.2),
 ("B", "10:11", "bunch of carrots", "br", "baby-carrots", 3.0),
 ("B", "10:33", "bag of frozen", "br", "frozen-veg", 3.0),
 ("B", "11:17", "saw my fists", "st", [("Raised fist", "1 fist = 1 cup")]),
 ("B", "11:50", "two cups of rice cooked", "st", [("Cooked rice", "2 cups cooked")]),
 ("B", "12:16", "water with my meals", "st", [("Droplet", "water with meals")]),
 ("B", "12:37", "every three to five hours", "st", [("Stopwatch", "every 3-5 h")]),
 ("B", "14:18", "so like your lunch will", "card", {"type": "timeline", "title": "Don't train on empty", "points": [{"t": "1 pm", "label": "Lunch", "at": 0.4}, {"t": "3-4 pm", "label": "Snack / fruit", "at": 1.6}, {"t": "6 pm", "label": "Training", "at": 8.4}]}, "five hours"),
 ("B", "14:58", "overweight from eating fruit", "br", "fruit-bowl", 3.0),
 ("B", "16:33", "bike to mount royal", "br", "city-cycling", 3.2),
 ("B", "17:39", "public transport", "br", "city-bus", 3.0),
 ("B", "18:29", "like an example could be", "card", {"type": "list", "title": "Prime before you train", "items": ["Fruit snacks", "Honey wafer", "A small bar", "A gel"], "at": [5.0, 7.5, 11.5, 22.0]}, "just before you do it"),
 ("B", "18:59", "my protein bars", "br", "protein-bar", 3.0),
 ("B", "19:11", "forgot about calves", "st", [("Bread", "forgot carbs!")]),
 ("B", "23:12", "pieces of fruit", "st", [("Banana", "fruit before a hard one")]),
 ("B", "23:48", "before swim", "br", "swimming-pool", 3.0),
 ("B", "24:31", "tortilla or roti", "br", "chicken-wrap", 3.0),
 ("B", "25:22", "overnight oats", "br", "overnight-oats", 3.2),
 ("B", "25:25", "is that something", "st", [("Bowl with spoon", "overnight oats")]),
 ("B", "27:29", "in your bag", "br", "gym-bag", 3.0),
 ("B", "28:26", "okay, so you know what you could do", "card", {"type": "timeline", "title": "Double session day", "points": [{"t": "Cardio", "label": "Run / bike", "at": 0.5}, {"t": "Eat", "label": "In between", "at": 2.5}, {"t": "Gym", "label": "Strength", "at": 5.0}, {"t": "Finish", "label": "The rest after", "at": 15.5}]}, "finish it afterwards"),
 ("B", "30:21", "take a tuna sandwich", "br", "tuna-sandwich", 3.0),
 ("B", "30:25", "tuna's got", "st", [("Sandwich", "protein + carbs")]),
 ("B", "31:05", "hard -boiled a bunch of eggs", "br", "boiled-eggs", 3.2),
 ("B", "31:19", "in their shell", "st", [("Egg", "1 week in the shell")]),
 ("B", "35:14", "greek yogurt and some berries", "br", "smoothie-berries", 3.2),
 ("B", "35:16", "and a banana", "st", [("Blueberries", "berries"), ("Banana", "banana")]),
 ("B", "36:10", "fish with any dairy", "st", [("Fish", "fish + dairy?")]),
 ("B", "41:40", "do you think realistically", "sbs", None, "more muscle mass"),
 ("B", "42:36", "training itself is going to have a huge response", "br", "muscle-flex", 3.0),
 ("B", "43:40", "what some people do", "card", {"type": "list", "title": "Weekend meal prep", "items": ["Chicken", "Rice", "Veggies", "Eat it all week"], "at": [7.0, 9.0, 10.5, 13.5]}, "throughout the week"),
 ("B", "44:16", "three recipes", "br", "meal-prep", 3.0),
 ("B", "44:52", "oatmeal pancakes", "br", "pancakes", 3.0),
 ("B", "45:24", "hash browns", "br", "hash-browns", 3.0),
 ("B", "45:58", "some color in there", "st", [("Green salad", "add colour")]),
 ("B", "46:10", "you're going to be sleeping", "st", [("Crescent moon", "no food overnight")]),
 ("B", "46:24", "let's say you did a workout at night", "card", {"type": "timeline", "title": "The empty-tank cycle", "points": [{"t": "Night", "label": "Workout", "at": 0.5}, {"t": "Bed", "label": "Shake only", "at": 5.0}, {"t": "6 am", "label": "Gym + banana", "at": 11.0}]}, "did a banana"),
 ("B", "47:33", "vitamin c", "st", [("Tangerine", "vitamin C")]),
 ("B", "47:42", "vitamin a and vitamin", "st", [("Carrot", "vitamin A"), ("Leafy green", "vitamin K")]),
 ("B", "48:03", "bag of spinach", "br", "spinach-kale", 3.0),
 ("B", "48:26", "mineral supplement", "br", "multivitamin", 3.0),
 ("B", "49:01", "there is benefits", "card", {"type": "versus", "title": "Real food vs a pill", "left": {"title": "Multivitamin", "lines": ["Fills the gaps"]}, "right": {"title": "Real food", "lines": ["Fibre + phytochemicals"]}, "delay": 3.0}, "in a bottle"),
]


def ws(f):
    d = json.load(open(os.path.join(B.TX, B.FILES[f] + ".json"), encoding="utf-8"))
    return [(w[0], w[1], P.bare(w[2]), w[4] if len(w) > 4 else "?") for sg in d for w in sg["w"] if P.bare(w[2])]


WS = {f: ws(f) for f in B.FILES}


def find(f, approx, phrase, win=25.0):
    k = [P.bare(x) for x in phrase.split() if P.bare(x)]
    w = WS[f]; t0 = B.sec(approx)
    hits = [i for i in range(len(w) - len(k) + 1) if abs(w[i][0] - t0) <= win and [x[2] for x in w[i:i + len(k)]] == k]
    if not hits:
        raise SystemExit(f"phrase not found: {f} {approx} '{phrase}'")
    i = min(hits, key=lambda i: abs(w[i][0] - t0))
    return i, len(k)


def span(f, i, end):
    """start/end of a device that begins at word i: `end` = seconds or a to-phrase."""
    w = WS[f]
    s = round(max(w[i][0] - 0.05, w[i - 1][1] + 0.02 if i else 0), 3)
    if isinstance(end, str):  # the first occurrence of the to-phrase AFTER the start word
        k = [P.bare(x) for x in end.split() if P.bare(x)]
        hits = [q for q in range(i, len(w) - len(k) + 1) if w[q][0] - w[i][0] <= 40 and [x[2] for x in w[q:q + len(k)]] == k]
        if not hits:
            raise SystemExit(f"to-phrase not found after start: {f} '{end}'")
        j = hits[0] + len(k) - 1
    else:
        j = max(range(i, len(w)), key=lambda q: -abs(w[q][1] - (w[i][0] + end)) if w[q][0] < w[i][0] + end + 1 else -999)
    e = w[j][1] + 0.1
    if j + 1 < len(w):
        e = min(e, w[j + 1][0] - 0.02)
    return s, round(e, 3)


def talker(f, s, e):
    labs = [x[3] for x in WS[f] if s <= x[0] < e and x[3] in "LR"]
    return max(set(labs), key=labs.count) if labs else "L"


def sticker_id(emoji, label):
    sid = (emoji + "_" + label).lower()
    sid = "".join(ch if ch.isalnum() else "-" for ch in sid).strip("-")[:48]
    STICKERS[sid] = {"id": sid, "emoji": emoji, "label": label, "dur": 2.8 if label else 2.4, "size": 180}
    return sid


def body(part):
    i0, i1 = L.PARTS[part]
    segs, stick = [], []  # stick: (file, src_time, [sticker ids], talker)
    for ci in range(i0, i1):
        f, st, title = L.CH[ci]
        nxt = L.CH[ci + 1] if ci + 1 < len(L.CH) else None
        en = B.sec(nxt[1]) if nxt and nxt[0] == f else B.sec(L.END[f])
        st = B.sec(st)
        s0, s1 = B.snap(f, st, st + 3.0)
        segs.append({"clip": B.FILES[f], "start": s0, "end": s1, "chapter": title, "tighten": 0, "nocaps": True,
                     "broll": {"file": f"projects/carrie-ep01/cards/T{ci + 1:02d}.mp4", "push": 0}})
        cur = s1
        evs = []
        for ev in EV:
            if ev[0] != f or not (st <= B.sec(ev[1]) < en):
                continue
            i, n = find(f, ev[1], ev[2])
            if WS[f][i][0] < cur:
                continue
            if ev[3] == "st":
                stick.append((f, WS[f][i][0], [sticker_id(e, l) for e, l in ev[4]], talker(f, WS[f][i][0] - 1, WS[f][i][1] + 1)))
                continue
            if ev[3] == "br" and not os.path.exists(os.path.join(EP, "broll", ev[4] + ".jpg")):
                continue  # no usable photo found for this beat
            s, e = span(f, i, ev[5])
            evs.append((s, e, ev))
        evs.sort()
        for s, e, ev in evs:
            if s < cur + 0.3:
                continue  # overlaps the previous device: skip
            if s - cur > 0.3:
                segs.append({"clip": B.FILES[f], "start": cur, "end": s})
            seg = {"clip": B.FILES[f], "start": s, "end": e, "tighten": 0}
            kind = ev[3]
            if kind == "br":
                seg["broll"] = {"file": f"projects/carrie-ep01/broll/{ev[4]}.jpg", "push": 0.07}
            elif kind == "card":
                who = talker(f, s, e)
                cid = f"L2_{part}_c{len(CARDS)}"
                CARDS.append({"id": cid, **{k: v for k, v in ev[4].items()}, "w": 806, "h": 1080, "dur": round(e - s + 0.8, 2)})
                seg.update(cx="right" if who == "R" else "left", zoom=ZC if who == "R" else ZN, cy=0.38,
                           broll={"file": f"projects/carrie-ep01/cards/{cid}.mp4", "panel": "left" if who == "R" else "right", "push": 0})
            elif kind == "sbs":
                seg.update(layout="sbs", zoom=1.45, zoom_r=1.3, cy=0.36)
            segs.append(seg)
            cur = e
        if en - cur > 0.3:
            segs.append({"clip": B.FILES[f], "start": cur, "end": round(en, 3)})
    # output timeline: replicate the engine's tightening to place stickers exactly
    t, pos = 0.0, []
    for sg in segs:
        g = sg.get("tighten", GAP)
        pieces = P.tighten(sg, B.TX, float(g), True) if g else [sg]
        for p in pieces:
            d = round((p["end"] - p["start"]) * 30) / 30
            pos.append((sg["clip"], p["start"], p["end"], t, bool(sg.get("broll") and sg["broll"].get("panel")) or sg.get("layout") == "sbs"))
            t += d
    stickers = []
    for f, ts, ids, who in stick:
        clip = B.FILES[f]
        hit = next((p for p in pos if p[0] == clip and p[1] - 0.05 <= ts < p[2]), None) or \
            next((p for p in pos if p[0] == clip and p[1] >= ts), None)
        if not hit or hit[4]:
            continue  # inside a split / side card: skip (no clutter over cards)
        at = hit[3] + max(ts - hit[1], 0)
        for k, sid in enumerate(ids):  # x placed by the engine, away from the faces actually on screen
            stickers.append({"at": round(at + 0.25 * k, 3), "file": f"projects/carrie-ep01/stickers/{sid}.mov", "x": "auto",
                             "group": f"g{len(stickers) - k}_{ts:.1f}", "y": 0.30})
    spec = {"_piece": True, "id": f"L2_{part}", "slug": "body", "format": "long", "title": f"v2 body {part}",
            "topic": "long-form part", "auto_frame": AF, "tighten": GAP, "captions": "pod", "cap_y": 0.935, "cap_size": 68,
            "fixes": B.FIX, "accent": B.ACCENT, "segments": segs, "stickers": stickers,
            "sfx": [{"at": round(p[3], 2), "file": "whoosh_soft.mp3", "vol": 0.22} for k, p in enumerate(pos)
                    if p[4] and (k == 0 or not pos[k - 1][4])]}
    if part == "P1":
        spec["names"] = [{"at": 3.5, "dur": 4.0, "name": "Carrie Mullin Innes", "role": B.NAMES["C"][1], "x": 0.55, "y": 0.72},
                         {"at": 8.0, "dur": 4.0, "name": "Nizam", "role": B.NAMES["N"][1], "x": 0.06, "y": 0.72}]
    return spec, t


CO_ST = {"salt": ("Salt", "salty sweater"), "kilo": ("Balance scale", "1 kg = 1 L"), "caffeine": ("Hot beverage", "caffeine"),
         "gels": ("Stopwatch", "2 gels / 1:42"), "chatgpt": ("Robot", "ChatGPT"), "shake": ("Cup with straw", "not enough"),
         "carbs": ("Bread", "forgot carbs"), "fruit": ("Red apple", "eat the fruit")}


def cold_open():
    sp = L.cold_open("CO1")
    sp.update(id="L2_CO1", captions="pod", cap_y=0.935, cap_size=68, keywords=[])
    keys, _ = L.OPENS["CO1"]
    t, st = 0.0, []
    for k, sg in zip(keys + ["_title"], sp["segments"]):
        if k in CO_ST:
            who = L.BEATS[k][3]
            st.append({"at": round(t + 0.4, 2), "file": f"projects/carrie-ep01/stickers/{sticker_id(*CO_ST[k])}.mov",
                       "x": "auto", "y": 0.30})
        g = sg.get("tighten", sp.get("tighten"))
        pieces = P.tighten(sg, B.TX, float(g), True) if g else [sg]
        t += sum(round((p["end"] - p["start"]) * 30) / 30 for p in pieces)
    sp["stickers"] = st
    return sp


if __name__ == "__main__":
    tot = 0
    for p in L.PARTS:
        sp, t = body(p); tot += t
        json.dump(sp, open(os.path.join(OUT, f"L2_{p}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        n = lambda k: sum(1 for s in sp["segments"] if k(s))
        print(p, f"{t / 60:.1f} min", "broll", n(lambda s: s.get("broll") and not s["broll"].get("panel") and "cards/T" not in s["broll"]["file"]),
              "cards", n(lambda s: (s.get("broll") or {}).get("panel")), "sbs", n(lambda s: s.get("layout") == "sbs"),
              "stickers", len(sp["stickers"]))
    json.dump(cold_open(), open(os.path.join(OUT, "L2_CO1.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump({"accent": B.ACCENT, "cards": CARDS}, open(os.path.join(EP, "cards_long2.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump({"accent": B.ACCENT, "stickers": list(STICKERS.values())}, open(os.path.join(EP, "stickers.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"total {tot / 60:.1f} min,", len(CARDS), "cards,", len(STICKERS), "sticker clips")
