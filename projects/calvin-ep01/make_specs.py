#!/usr/bin/env python3
"""Calvin ep01: 20 topics x 3 variants -> clips/T01_V1.json ... T20_V3.json (+ moments.md).

V1 house look (card + headline + data panels, orange), V2 coach1 look (full-frame on the coach, bold yellow
captions, cutaways), V3 creator hyper-edit (cold-open hook line first, punch-ins, name tag, stamps/stacks).
Cuts snap to Whisper word boundaries; overlay times are mapped through the same jump-cut tightening the
engine does, so panels land on the spoken words.
usage: python projects/calvin-ep01/make_specs.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import podcast as P  # noqa: E402

TX = os.path.join(HERE, "tx")
RAW = "H:/Nizam Blr/calvin"
C55, C06, C36 = "A001_09091926_C055", "A001_09031846_C006", "A001_09031920_C036"
ORANGE, YELLOW = "#FF5A1F", "#FFD60A"
GAP = 0.35
FIXES = {"age station": "aid station", "age stations": "aid stations", "bloodlack tape": "blood lactate",
         "iron man": "Ironman", "Iron Man": "Ironman", "carbomix": "carb mix", "Morton": "Maurten", "over -ride": "override", "self -talk": "self-talk"}
# where faces sit in each wide 4:3 shot (x 0-1) -> 9:16 crops for V2/V3
COACH_X = {C55: 0.71, C06: 0.30, C36: 0.31}
ATHLETE_X = {C55: 0.29, C06: 0.68, C36: 0.74}
SHOP = {  # bike-shop B-roll for bike topics (clip, at, cx, cy, label)
    "pedals": ("A001_09031857_C018", 1.0, 0.5, 0.55),
    "quinn": ("A001_09031856_C014", 0.5, 0.5, 0.45),
    "prick": ("A001_09031901_C023", 44.0, 0.42, 0.5),
    "push": ("A001_09031905_C026", 28.0, 0.62, 0.45),
    "ride": ("A001_09031919_C035", 10.0, 0.66, 0.45),
}

T = [
 dict(id="T01", slug="swim-exit-spikes", title="Your swim exit can wreck your gut", clip=C55, s="The thing is is as you exit", e="recipe for disaster",
      kicker="IRONMAN · SWIM EXIT", head="YOUR SWIM EXIT CAN WRECK YOUR GUT", box="GUT",
      keys=["spikes", "spike", "stomach", "gut", "flat", "disaster", "conservative"],
      panels=[dict(at="Every time your heart rate spikes", label="WHAT A SPIKE DOES", text="BLOOD LEAVES YOUR GUT", accent="GUT"),
              dict(at="The best trace", label="YOUR HEART RATE TRACE", chart="flat_vs_zigzag", notes=["✓ FLAT = THE GOAL", "✕ SPIKES = RECIPE FOR DISASTER"])],
      hook="Every time your heart rate spikes, your stomach sort of gets shut down", broll=None, stamp=("disaster", "SPIKES")),
 dict(id="T02", slug="rehearse-transition", title="Rehearse your transition on race morning", clip=C55, s="The morning what I typically do", e="Just walk it through",
      kicker="IRONMAN · T1", head="REHEARSE YOUR TRANSITION BEFORE THE GUN", box="REHEARSE",
      keys=["rehearse", "landmark", "rows", "scrambling"],
      panels=[dict(at="I actually walk down to the water exit", label="RACE MORNING", notes=["1. WALK THE SWIM EXIT", "2. PICK A LANDMARK", "3. COUNT THE ROWS TO YOUR BIKE"]),
              dict(at="exit here, turn right", label="IN YOUR HEAD, IN THE WATER", text="EXIT. RIGHT. FOUR ROWS DOWN.", accent="FOUR ROWS")],
      hook="oh man, I don't know where I'm going", broll=None, stamp=("rehearse", "REHEARSE")),
 dict(id="T03", slug="shoes-on-pedals", title="Shoes on the pedals? Keep it simple", clip=C55, s="Are you going to put your shoes on your pedals", e="running on grass",
      kicker="IRONMAN · T1", head="SHOES ON THE PEDALS? KEEP IT SIMPLE", box="SIMPLE",
      keys=["simple", "disaster", "concrete", "grass", "caveat", "clips", "40"],
      panels=[dict(at="safe and simple", label="40 YEARS OF RACING SAYS", text="SAFE AND SIMPLE", accent="SIMPLE"),
              dict(at="Now the only caveat", label="THE ONLY EXCEPTION", text="400 M ON CONCRETE", accent="400 M", notes=["RUNNING IN CLEATS DAMAGES THE CLIPS"])],
      hook="What am I gaining by doing that? It's a recipe for disaster", broll=None, stamp=("safe and simple", "SAFE + SIMPLE")),
 dict(id="T04", slug="no-fuel-first-20", title="Don't eat in the first 20 minutes of the bike", clip=C55, s="to keep your gut online", e="take my first gel",
      kicker="IRONMAN · BIKE FUEL", head="DON'T EAT IN THE FIRST 20 MINUTES", box="DON'T EAT",
      keys=["gut", "fuel", "breaths", "gel", "stomach", "respiration", "easy"],
      panels=[dict(at="Easy and no fuel", label="FIRST 15-20 MIN ON THE BIKE", text="EASY. NO FUEL.", accent="NO FUEL."),
              dict(at="take some good deep breaths", label="THE SIGNAL YOU'RE READY", text="DEEP BREATHS = GUT IS BACK", accent="GUT")],
      hook="Don't consume anything either? Nope. Easy and no fuel", broll="pedals", stamp=("no fuel", "NO FUEL"),
      stack=("first gel", ["0-20 MIN: EASY", "THEN: FIRST GEL", "60-90 MIN: SOLID FOOD"])),
 dict(id="T05", slug="rules-of-two", title="Fuel like an IV drip: the rules of two", clip=C55, s="But then the fueling needs to be like", e="make sure it's like an IV drip",
      kicker="IRONMAN · BIKE FUEL", head="FUEL LIKE AN IV DRIP", box="IV DRIP",
      keys=["drip", "fast", "much", "concentrated", "water", "guzzle", "two"],
      panels=[dict(at="violate the rules of two", label="THE RULES OF TWO", text="TOO FAST. TOO MUCH. TOO STRONG.", accent="TOO"),
              dict(at="if you have a gel wash it down with water", label="THE GEL RULE", text="GEL + WATER. NEVER GEL + CARB MIX.", accent="WATER.")],
      hook="You don't ever want to violate the rules of two", broll="pedals", stamp=("IV drip", "IV DRIP"),
      stack=("consuming it too fast", ["TOO FAST", "TOO MUCH", "TOO CONCENTRATED"])),
 dict(id="T06", slug="fuel-alarm", title="Set a 15-minute fuel alarm", clip=C55, s="And then if you're if you're sort of in the moment", e="a little less to think about",
      kicker="IRONMAN · BIKE FUEL", head="SET A 15-MINUTE FUEL ALARM", box="15-MINUTE",
      keys=["watch", "15", "beeps", "fuel", "cue", "countdown"],
      panels=[dict(at="15 minute countdown", label="WATCH SETUP", text="REPEAT TIMER: 15:00", accent="15:00"),
              dict(at="every 15 minutes", label="FOR THE WHOLE BIKE", text="BEEP. FUEL. REPEAT.", accent="FUEL.")],
      hook="every 15 minutes, it's like, oh, okay, it's time for me to fuel", broll="ride", stamp=("audio cue", "AUDIO CUE")),
 dict(id="T07", slug="why-lactate-test", title="12 days out: why we tested his blood", clip=C06, s="we're doing a bloodlack tape test", e="For the entire bike ride",
      kicker="IRONMAN · LAB TEST", head="12 DAYS OUT: WE TESTED HIS BLOOD", box="BLOOD",
      keys=["override", "overriding", "precise", "run", "marathon", "struggle", "science"],
      panels=[dict(at="Overriding is not good", label="THE RULE", text="UNDERRIDE IS OK. OVERRIDE IS NOT.", accent="OVERRIDE"),
              dict(at="give him a heart rate value", label="WHAT HE LEAVES WITH", text="ONE HR VALUE. ONE POWER VALUE.", accent="HR POWER")],
      hook="Overriding is not good", broll="prick", stamp=("science", "SCIENCE")),
 dict(id="T08", slug="lactate-threshold", title="Find the point where your lactate jumps", clip=C55, s="So here's the lactate scores", e="call it FTP",
      kicker="IRONMAN · LACTATE TEST", head="FIND THE POINT WHERE LACTATE JUMPS", box="JUMPS",
      keys=["lactate", "linear", "threshold", "FTP", "jumps", "curvilinear", "aerobic"],
      panels=[dict(at="well below four millimoles", label="160 → 220 WATTS", text="LINEAR. AEROBIC SYSTEM HANDLES IT.", accent="LINEAR."),
              dict(at="where your lactate jumps", label="YOUR LACTATE CURVE", lines=[{"pts": [[0, .85], [.2, .83], [.4, .79], [.6, .72], [.7, .6], [.8, .42], [.9, .22], [1, .05]], "color": "A"}],
                   notes=["▲ ~225-230 W", "= LACTATE THRESHOLD / FTP"])],
      hook="there comes a point", broll="prick", stamp=("FTP", "FTP")),
 dict(id="T09", slug="burn-your-tank", title="Go over FTP and you burn your fuel tank", clip=C55, s="So what we know is that if you head out", e="burned your fuel tanks",
      kicker="IRONMAN · BIKE PACING", head="GO OVER FTP AND YOU BURN YOUR TANK", box="BURN",
      keys=["accelerator", "glycogen", "burn", "fuel", "tanks", "backfire"],
      panels=[dict(at="So glycogen is in your liver", label="YOUR FUEL TANK", text="GLYCOGEN: LIVER + MUSCLE", accent="GLYCOGEN:"),
              dict(at="eventually it'll backfire", label="WHAT HAPPENS LATER", chart="drop", notes=["▼ 150 W: \"THIS IS ALL I GOT\""])],
      hook="this is all I got, because you burned your fuel tanks", broll="push", stamp=("accelerator", "ACCELERATOR")),
 dict(id="T10", slug="climbs-under-160", title="Never cross 160 on the climbs", clip=C55, s="So the bottom line is that in an Ironman", e="keep it under 160",
      kicker="IRONMAN · BIKE CLIMBS", head="NEVER CROSS 160 ON THE CLIMBS", box="160",
      keys=["160", "climbs", "fat", "sugar", "FTP", "efficient"],
      panels=[dict(at="your Ironman max heart rate is 160", label="IRONMAN MAX HEART RATE", text="160 BPM. EVEN ON CLIMBS.", accent="160"),
              dict(at="turn off a little bit of the fat", label="CROSS THE LINE AND", text="FAT OFF. SUGAR ON.", accent="SUGAR")],
      hook="your Ironman max heart rate is 160 even on climbs", broll="push", stamp=("160", "160 BPM")),
 dict(id="T11", slug="ironman-hr-zone", title="Settling into your Ironman heart rate zone", clip=C55, s="and then your Ironman heart rate zone is 145", e="get it in that zone",
      kicker="IRONMAN · BIKE PACING", head="HIS IRONMAN ZONE: 145 TO 152", box="145",
      keys=["145", "152", "zone", "nasal", "calm", "tight"],
      panels=[dict(at="So it's pretty tight", label="IRONMAN BIKE ZONE", text="145-152 BPM", accent="145-152"),
              dict(at="just nasal breathe", label="FIRST MINUTES ON THE BIKE", notes=["→ NASAL BREATHING", "→ CALM THOUGHTS", "→ LET HR SETTLE TO 145"])],
      hook="your Ironman heart rate zone is 145 to 152", broll="ride", stamp=("nasal", "NASAL"),
      stack=("nasal breathe", ["NASAL BREATHE", "CALM THOUGHTS", "SETTLE TO 145"])),
 dict(id="T12", slug="cardiac-drift", title="Why your heart rate creeps up on the bike", clip=C55, s="And then as you get slightly dehydrated", e="at that 160 mark",
      kicker="IRONMAN · BIKE PACING", head="WHY YOUR HEART RATE CREEPS UP", box="CREEPS",
      keys=["drift", "dehydrated", "160", "162", "zone", "alarmed"],
      panels=[dict(at="cardiac drift", label="CARDIAC DRIFT", lines=[{"pts": [[0, .75], [.25, .7], [.5, .62], [.75, .52], [1, .4]], "color": "A"},
                                                                        {"pts": [[0, .75], [1, .75]], "color": "#777777", "w": 2}],
                   notes=["SAME POWER → HEART RATE CLIMBS"]),
              dict(at="threshold heart rate is 162", label="THE CEILING", text="THRESHOLD 162. STAY UNDER 160.", accent="160.")],
      hook="don't be alarmed if later on it gets into that", broll="ride", stamp=("cardiac drift", "CARDIAC DRIFT")),
 dict(id="T13", slug="the-120k-check", title="How you should feel at 120 km", clip=C55, s="that's gonna make or break the last", e="solid marathon",
      kicker="IRONMAN · 120 KM CHECK", head="HOW YOU SHOULD FEEL AT 120 KM", box="120 KM",
      keys=["120k", "fatigue", "good", "marathon", "feeding", "proper"],
      panels=[dict(at="when they get to 120k", label="WHERE FATIGUE HITS", text="120 KM INTO 180", accent="120"),
              dict(at="with the proper feeding", label="GET THERE WITH", notes=["✓ PROPER FEEDING", "✓ PROPER HEART RATE TARGETS", "✓ PROPER AMOUNT OF WORK"])],
      hook="This is good. This is good. This is good", broll="pedals", stamp=("120k", "120 KM"),
      stack=("proper feeding", ["FEEDING", "HR TARGETS", "WORKLOAD"])),
 dict(id="T14", slug="good-run-good-day", title="Nobody brags about a great bike", clip=C36, s="And most people will say that they had a successful day", e="best day right there",
      kicker="IRONMAN · RACE DAY", head="NOBODY BRAGS ABOUT A GREAT BIKE", box="BIKE",
      keys=["run", "walked", "marathon", "killed", "awesome", "best"],
      panels=[dict(at="On the other side is", label="THE TRAP", text="KILL THE BIKE. WALK FOR 7 HOURS.", accent="WALK"),
              dict(at="I had a great swim", label="THE BEST DAY", notes=["✓ GREAT SWIM", "✓ GREAT BIKE", "✓ AWESOME RUN"])],
      hook="nobody ever says, yeah, I killed the bike", broll=None, stamp=("killed the bike", "KILLED THE BIKE?")),
 dict(id="T15", slug="first-10k-slowest", title="Your first 10K should be your slowest", clip=C55, s="when we looked at the run marathon", e="really, really relax",
      kicker="IRONMAN · RUN", head="YOUR FIRST 10K SHOULD BE YOUR SLOWEST", box="SLOWEST",
      keys=["slowest", "10K", "easy", "relax", "blood"],
      panels=[dict(at="first 10K often was their slowest", label="WHAT THE BEST RUNS SHOW", text="FIRST 10K = SLOWEST 10K", accent="SLOWEST"),
              dict(at="Your blood has to come out", label="WHY (~10 MIN)", notes=["BLOOD LEAVES BIKE LEGS + GUT", "→ MOVES TO RUNNING MUSCLES"])],
      hook="their first 10K often was their slowest", broll=None, stamp=("slowest", "SLOWEST")),
 dict(id="T16", slug="marathon-pace-330", title="5:00 per km = a 3:30 marathon", clip=C55, s="And so what does that mean", e="is pretty good",
      kicker="IRONMAN · RUN PACE", head="5:00 PER KM = A 3:30 MARATHON", box="3:30",
      keys=["superstar", "330", "five", "awesome", "elite"],
      panels=[dict(at="five minute per kilometer pace", label="MID-MARATHON TARGET", text="5:00 / KM", accent="5:00"),
              dict(at="you're a superstar", label="AGE-GROUP IRONMAN MARATHON", notes=["3:30  SUPERSTAR", "3:45  AWESOME", "< 4:00  PRETTY GOOD"])],
      hook="you're a superstar", broll=None, stamp=("superstar", "SUPERSTAR"),
      stack=("345 would be awesome", ["3:30 SUPERSTAR", "3:45 AWESOME", "<4:00 GOOD"])),
 dict(id="T17", slug="dark-moments", title="Expect 2-3 dark moments", clip=C55, s="However, even the pros", e="Keep moving",
      kicker="IRONMAN · MINDSET", head="EXPECT 2-3 DARK MOMENTS", box="DARK",
      keys=["dark", "expect", "moving", "fueling", "walking", "self-talk"],
      panels=[dict(at="Expect those", label="EVEN THE PROS", text="2-3 DARK MOMENTS. EXPECT THEM.", accent="DARK"),
              dict(at="So the worst thing", label="WHEN IT HITS", notes=["✕ SIT IN A CHAIR FOR 20 MIN", "✓ DRINK. FUEL. FAST-WALK.", "✓ KEEP MOVING"])],
      hook="even the pros will always report there's two or three really dark moments", broll=None, stamp=("Keep moving", "KEEP MOVING"), bw="So the worst thing", bw_end="The best thing you can do"),
 dict(id="T18", slug="walk-the-hills", title="Walking the hills can be faster", clip=C55, s="Just just remember the best runners", e="what you're trying to protect",
      kicker="IRONMAN · RUN", head="WALKING THE HILLS CAN BE FASTER", box="WALKING",
      keys=["walk", "hills", "quads", "matches", "10K", "steep"],
      panels=[dict(at="Sometimes your best strategy is to walk", label="STEEP HILLS", text="POWER WALK UP. EASY DOWN.", accent="WALK"),
              dict(at="burn a couple of matches", label="MATCHES BURNED EARLY", text="= WALKING THE LAST 10K", accent="10K")],
      hook="Sometimes your best strategy is to walk", broll=None, stamp=("matches", "MATCHES")),
 dict(id="T19", slug="aid-station-crashes", title="Most bike crashes happen at aid stations", clip=C55, s="Going back to the bike be very very careful", e="clear shot at the aid station",
      kicker="IRONMAN · BIKE SAFETY", head="MOST BIKE CRASHES HAPPEN HERE", box="CRASHES",
      keys=["crashes", "accidents", "verbal", "slow", "clear"],
      panels=[dict(at="The majority of the accidents", label="DANGER ZONE", text="AID STATIONS", accent="AID"),
              dict(at="make sure you're very verbal", label="HOW TO GET THROUGH", notes=["→ SLOW DOWN", "→ SAY IT + POINT", "→ DROP BACK FROM GROUPS"])],
      hook="The majority of the accidents or bike crashes happen totally at the age stations", broll="ride", stamp=("verbal", "BE VERBAL"),
      stack=("very verbal", ["SLOW DOWN", "SAY IT + POINT", "CLEAR SHOT"])),
 dict(id="T20", slug="aid-station-rule", title="The aid station rule on the run", clip=C55, s="And hit every aid station", e="30 seconds at the most",
      kicker="IRONMAN · RUN", head="THE AID STATION RULE", box="RULE",
      keys=["running", "rule", "table", "walk", "seconds"],
      panels=[dict(at="Once you reach the last table", label="YOUR PERSONAL RULE", text="LAST TABLE = START RUNNING", accent="RUNNING"),
              dict(at="how much time did you lose", label="COST OF GETTING WHAT YOU NEED", text="15-30 SECONDS", accent="15-30")],
      hook="they haven't even started running again", broll=None, stamp=("get running", "GET RUNNING")),
]

_words = {}


def words(clip):
    if clip not in _words:
        _words[clip] = [w for sg in json.load(open(os.path.join(TX, clip + ".json"), encoding="utf-8")) for w in sg["w"] if w[2].strip()]
    return _words[clip]


def find(clip, phrase, after=0.0):
    """(start, end) of the first word sequence matching phrase at/after `after` (fuzzy: punctuation/case ignored)."""
    ws = words(clip)
    toks = [P.bare(t) for t in phrase.split()]
    toks = [t for t in toks if t]
    bw = [P.bare(w[2]) for w in ws]
    for i in range(len(ws) - len(toks) + 1):
        if ws[i][0] < after - 0.01:
            continue
        if bw[i:i + len(toks)] == toks:
            return ws[i][0], ws[i + len(toks) - 1][1]
    sys.exit(f"phrase not found in {clip}: {phrase!r}")


def pieces(clip, s, e):
    return P.tighten({"clip": clip, "start": s, "end": e}, TX, GAP, True)


def out_time(pcs, t):
    """source time -> output time through the jump-cut pieces."""
    acc = 0.0
    for p in pcs:
        if t < p["start"]:
            return acc
        if t <= p["end"]:
            return acc + t - p["start"]
        acc += round((p["end"] - p["start"]) * 30) / 30
    return acc


def total(pcs):
    return sum(round((p["end"] - p["start"]) * 30) / 30 for p in pcs)


def main():
    os.makedirs(os.path.join(HERE, "clips"), exist_ok=True)
    rows = []
    for t in T:
        clip = t["clip"]
        s0, _ = find(clip, t["s"])
        _, e1 = find(clip, t["e"], s0)
        s, e = round(max(s0 - 0.1, 0), 2), round(e1 + 0.15, 2)
        pcs = pieces(clip, s, e)
        dur = total(pcs)
        hs, he = find(clip, t["hook"], s - 1)
        hs, he = round(hs - 0.08, 2), round(he + 0.12, 2)
        ptimes = [round(out_time(pcs, find(clip, p["at"], s)[0]), 2) for p in t["panels"]]
        base = dict(title=t["title"], topic=t["title"], format="short", fixes=FIXES, keywords=t["keys"], tighten=GAP)
        names = [{"at": 0.4, "dur": 2.8, "name": "Coach Cal", "role": "Calvin Zaryski · XTERRA world champion", "y": 0.16, "x": 0.07}]

        # ---------------- V1: house look
        panels = []
        for k, (p, at) in enumerate(zip(t["panels"], ptimes)):
            nxt = ptimes[k + 1] if k + 1 < len(ptimes) else dur
            pp = {kk: v for kk, v in p.items() if kk != "at"}
            pp.update(at=max(at - 0.15, 0.3), dur=max(nxt - at, 3.0))
            panels.append(pp)
        until = max(ptimes[0] - 0.25, 2.5)
        segs = [{"clip": clip, "start": s, "end": e}]
        if t.get("broll"):  # one shop cutaway inside the card, on the panel-2 beat (voice continues)
            bc, bat, bcx, bcy = SHOP[t["broll"]]
            cs, _ = find(clip, t["panels"][1]["at"], s)
            cs = round(cs - 0.05, 2)
            ce = min(cs + 2.6, e - 0.5)
            if ce - cs > 1.2:
                segs = [{"clip": clip, "start": s, "end": cs},
                        {"clip": clip, "start": cs, "end": ce, "tighten": 0, "broll": {"file": f"{RAW}/{bc}.mov", "at": bat, "cx": bcx, "cy": bcy}},
                        {"clip": clip, "start": ce, "end": e}]
        v1 = dict(id=f"{t['id']}_V1", slug=t["slug"], layout="card", captions="bold", accent=ORANGE,
                  cap_y=0.795, cap_size=72, cap_spacing=5, progress={},
                  headline={"kicker": t["kicker"], "text": t["head"], "box": t["box"], "until": until},
                  panels=panels, segments=segs, **base)

        # ---------------- V2: coach1 look (full frame on the coach, yellow captions, cutaways)
        cx, ax = COACH_X[clip], ATHLETE_X[clip]
        cuts = []
        c1, _ = find(clip, t["panels"][0]["at"], s)
        cuts.append((round(c1 + 0.6, 2), {"file": f"{RAW}/{clip}.mov", "cx": ax, "cy": 0.5, "same": True}))
        if t.get("broll"):
            bc, bat, bcx, bcy = SHOP[t["broll"]]
            c2, _ = find(clip, t["panels"][1]["at"], s)
            cuts.append((round(c2 + 0.3, 2), {"file": f"{RAW}/{bc}.mov", "at": bat, "cx": bcx, "cy": bcy}))
        else:
            c2, _ = find(clip, t["panels"][1]["at"], s)
            cuts.append((round(c2 + 0.8, 2), {"file": f"{RAW}/{clip}.mov", "cx": ax, "cy": 0.5, "same": True}))
        segs, cur = [], s
        for at, br in sorted(cuts):
            ln = 1.8 if br.get("same") else 2.4
            if at - cur < 1.0 or at + ln > e - 0.6:
                continue
            segs.append({"clip": clip, "start": cur, "end": at, "cx": cx})
            b = {k: v for k, v in br.items() if k != "same"}
            if br.get("same"):
                b["at"] = at
            segs.append({"clip": clip, "start": at, "end": round(at + ln, 2), "tighten": 0, "broll": {**b, "push": 0.02}})
            cur = round(at + ln, 2)
        segs.append({"clip": clip, "start": cur, "end": e, "cx": cx})
        v2 = dict(id=f"{t['id']}_V2", slug=t["slug"], layout="full", captions="bold", accent=YELLOW,
                  cap_y=0.70, cap_size=70, cap_spacing=3, cap_outline=5, jump_zoom=[1.0, 1.15], segments=segs, **base)

        # ---------------- V3: creator hyper-edit, cold-open hook line first
        hook = {"clip": clip, "start": hs, "end": he, "cx": cx, "zoom": 1.28, "cy": 0.42, "tighten": 0}
        hd = round((he - hs) * 30) / 30
        main_segs = [{"clip": clip, "start": s, "end": e, "cx": cx}]
        if t.get("bw"):
            b0, _ = find(clip, t["bw"], s)
            b0 = round(b0 - 0.05, 2)
            nx = find(clip, t["bw_end"], b0)[0]
            main_segs = [{"clip": clip, "start": s, "end": b0, "cx": cx}, {"clip": clip, "start": b0, "end": round(nx - 0.05, 2), "cx": cx, "look": "bw"},
                         {"clip": clip, "start": round(nx - 0.05, 2), "end": e, "cx": cx}]
        st_phrase, st_text = t["stamp"]
        sat = hd + out_time(pcs, find(clip, st_phrase, s)[0])
        v3 = dict(id=f"{t['id']}_V3", slug=t["slug"], layout="full", captions="creator", accent=ORANGE, cap_y=0.68,
                  jump_zoom=[1.0, 1.18], names=[{**names[0], "at": hd + 0.2}],
                  stamps=[{"at": round(sat, 2), "text": st_text, "color": ORANGE, "dur": 1.3, "y": 0.2}],
                  segments=[hook, {"card": True, "dur": 0.12, "bg": ["0x000000", "0x000000"]}] + main_segs, **base)
        if t.get("stack"):
            sp, items = t["stack"]
            v3["stacks"] = [{"at": round(hd + 0.12 + out_time(pcs, find(clip, sp, s)[0]), 2), "items": items, "every": 0.7,
                             "color": ORANGE, "y": 0.14, "dur": 3.6}]
        for v in (v1, v2, v3):
            json.dump(v, open(os.path.join(HERE, "clips", v["id"] + ".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        rows.append((t, s, e, dur, hd))
        flag = "  <-- OVER 60" if dur + hd > 60 else ""
        print(f"{t['id']} {t['slug']:22s} {clip[-4:]} {s:7.1f}-{e:7.1f}  ~{dur:4.1f}s (V3 {dur + hd + 0.12:4.1f}s){flag}")

    md = ["# Calvin ep01: 20 topics x 3 variants (60 shorts)", "",
          "Coach Cal (Calvin Zaryski) briefs his athlete before his first Ironman (C055 sit-down, 27 min) + the",
          "blood-lactate step test on Quinn in the bike shop (C006, C036; other shop clips = B-roll).", "",
          "V1 house look (card, headline, data panels, orange) · V2 full-frame coach, yellow bold captions, cutaways ·",
          "V3 creator edit, cold-open hook line, punch-ins, name tag, stamps/stacks.", "",
          "| ID | Topic | Source | Range (s) | Length | V3 hook |", "|---|---|---|---|---|---|"]
    for t, s, e, dur, hd in rows:
        md.append(f"| {t['id']} | {t['title']} | {t['clip'][-4:]} | {s:.1f}-{e:.1f} | ~{dur:.0f} s | \"{t['hook']}\" |")
    open(os.path.join(HERE, "moments.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
