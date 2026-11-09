#!/usr/bin/env python3
"""Carrie ep01 v4 story edit -> v4/edit_plan.json + v4/edit_plan.md

Every range is written as phrase anchors (file, "MM:SS", from-phrase, "MM:SS", to-phrase) and resolved here to exact
word boundaries: start = first word start - 0.08, end = last word end + 0.12 (clamped so a range never starts or ends
inside a neighbouring word). Duration estimate per range = sum of word durations + every inter-word gap capped at 0.35 s
(the render engine drops pauses > 0.5 s and um/uh). Hero lines and key facts are validated with build_long2.find().

Run from the repo root:  python projects/carrie-ep01/v4/tools/make_plan.py [--check]
"""
import json, os, sys

CHECK = "--check" in sys.argv  # build_shorts truncates sys.argv on import
ROOT =os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
EP = os.path.join(ROOT, "projects", "carrie-ep01")
V4 = os.path.join(EP, "v4")
sys.path.insert(0, EP)
import build_long2 as L2  # noqa: E402  (WS word lists + find())
import build_shorts as B  # noqa: E402
P = L2.P

FILES = B.FILES
RAW = {}  # raw word text aligned 1:1 with L2.WS
for f in FILES:
    d = json.load(open(os.path.join(B.TX, FILES[f] + ".json"), encoding="utf-8"))
    RAW[f] = [w[2].strip() for sg in d for w in sg["w"] if P.bare(w[2])]
    assert len(RAW[f]) == len(L2.WS[f])

SPK = {"L": "N", "R": "C"}
CLAMPS = []


def mmss(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


def bare_list(phrase):
    return [P.bare(x) for x in phrase.split() if P.bare(x)]


def find_to(f, i, approx, phrase, win=25.0):
    """index of the LAST word of `phrase`, searched near `approx` and not before word i."""
    k = bare_list(phrase); w = L2.WS[f]; t0 = B.sec(approx)
    hits = [q for q in range(i, len(w) - len(k) + 1) if abs(w[q][0] - t0) <= win and [x[2] for x in w[q:q + len(k)]] == k]
    if not hits:
        raise SystemExit(f"to-phrase not found: {f} {approx} '{phrase}'")
    q = min(hits, key=lambda q: abs(w[q][0] - t0))
    return q + len(k) - 1


def resolve(f, t1, p1, t2, p2):
    w = L2.WS[f]
    i, _ = L2.find(f, t1, p1)
    j = find_to(f, i, t2, p2)
    s = w[i][0] - 0.08
    if i > 0 and s < w[i - 1][1]:
        CLAMPS.append((f, mmss(w[i][0]), "start", round(w[i - 1][1] - s, 3)))
        s = w[i - 1][1] + 0.005
    e = w[j][1] + 0.12
    if j + 1 < len(w) and e > w[j + 1][0]:
        CLAMPS.append((f, mmss(w[j][1]), "end", round(e - w[j + 1][0], 3)))
        e = w[j + 1][0] - 0.005
    return round(max(s, 0.0), 3), round(e, 3), i, j


def est_idx(f, i, j):
    w = L2.WS[f]; t = 0.0
    for q in range(i, j + 1):
        t += w[q][1] - w[q][0]
        if q > i:
            t += min(max(w[q][0] - w[q - 1][1], 0.0), 0.35)
    return t


def text_idx(f, i, j):
    return " ".join(RAW[f][i:j + 1])


def who_idx(f, i, j):
    labs = [L2.WS[f][q][3] for q in range(i, j + 1)]
    lab = max(set(labs), key=labs.count)
    return SPK.get(lab, "?")


# =====================================================================================================================
TITLE = "Fuelling Like an Endurance Athlete"
SUBTITLE = "A real consult with high-performance sports dietitian Carrie Mullin Innes: salt, cramps, sweat tests, protein and the evening-fuel gap"

# cold open beats: (file, t_from, from-phrase, t_to, to-phrase, who, why)
COLD = [
    ("A", "14:37", "If I fall, just take me out", "14:40", "I'm not going to quit.", "N",
     "Scroll-stopper: a cramping athlete telling the medics to drag him off rather than let him quit. Stakes in 2 s."),
    ("A", "12:58", "I can see salt", "13:03", "everywhere.", "N",
     "Vivid physical image (salt crust on his face) that sets up the whole sodium thread."),
    ("A", "21:03", "you lost a kilo.", "21:10", "you didn't replace.", "C",
     "The single most useful rule in the episode (1 kg lost = 1 L of sweat not replaced) as a number hit."),
    ("A", "09:15", "before I started iron one chat,", "09:20", "my dietitian.", "N",
     "Laugh + relatable confession: ChatGPT was his dietitian before a real one."),
    ("A", "38:30", "Isn't it 30 minutes?", "38:37", "the first two hours.", "C",
     "Myth vs fact in one breath: Nizam asks about the 30-minute window, Carrie corrects to 2 hours (Nizam asks, Carrie answers)."),
    ("B", "19:02", "but I have just loaded protein", "19:12", "and other stuff.", "N",
     "Self-aware mistake most gym-goers make: all protein, no carbs (caption fix: 'calves' -> 'carbs')."),
    ("B", "34:23", "Because I just think", "34:27", "not enough for you.", "C",
     "Bold verdict from the expert: the protein shake is not enough."),
    ("B", "14:56", "If you had another one,", "15:00", "from eating fruit.", "C",
     "Light laugh beat, breaks the run of warnings."),
    ("B", "41:46", "the goal before the race,", "41:56", "more muscle mass", "N",
     "Cliffhanger question: the episode's real stakes - can he gain muscle before race day?"),
    ("B", "42:05", "i honestly think like", "42:08", "can you gain muscle mass", "C",
     "Unresolved answer: cut before her verdict - viewers stay to hear it (chapter 13)."),
]

# chapters: title (<=34), kicker (<=40), summary, keeps [(file, t_from, from, t_to, to, note)]
CHAPTERS = [
    {"title": "WHAT I EAT IN A DAY", "kicker": "a HYROX athlete's food log, line by line",
     "summary": "Carrie walks through Nizam's real food log: shake and eggs, Greek yogurt and granola, a mountain of rice, three office fruits, 'I should say three litres but I might lie' (he needs ~2.2 L), and chicken with roti for dinner.",
     "keep": [
         ("A", "00:05", "Nizam how much do you weigh?", "00:13", "74 kilos.", "cold start: Carrie names Nizam, his 74 kg is the number every later calculation uses"),
         ("A", "01:12", "So thanks for sharing your food record", "02:51", "what's going into your muscles.", "breakfast + timing; first warning: a protein shake alone never recovers you"),
         ("A", "03:10", "Then your lunch is eaten around what time?", "04:01", "how much I typically take.", "lunch: 200-300 g rice + ~150 g chicken"),
         ("A", "04:18", "Now this is a very tiny rice,", "04:37", "you're getting lots of carbs.", "'Rice is huge, I take a lot of rice' (portion reveal)"),
         ("A", "04:38", "Okay, and then you might have a bit of veggies", "06:02", "during my training session.", "veg gap, the 1 pm -> 9 pm question, banana/apple/orange every day"),
         ("A", "06:04", "And how much water do you think you're drinking", "06:13", "That's okay.", "'I should tell three, but I might lie'"),
         ("A", "06:36", "And so based on your body weight,", "07:10", "put it that way okay", "2.2 L for his body weight, more on heavy-sweat days"),
         ("A", "07:17", "okay so then when you have when you make this dinner", "07:37", "like that. Yeah.", "dinner: chicken + roti - closes the day"),
     ]},
    {"title": "CHATGPT WAS MY DIETITIAN", "kicker": "old habits, pills and the vitamin D rule",
     "summary": "The switch to HYROX (strength + running), how he ate last time (holiday in India, no plan), and the supplements ChatGPT suggested: omega-3, a Costco multivitamin, whey. Carrie's one must-have: vitamin D every day October to April, 1,000 IU, never more than 4,000 IU a day.",
     "keep": [
         ("A", "07:40", "So you're going to be switching", "08:43", "stay the constant everywhere.", "the new goal: HYROX = strength + running; last HYROX: untrained, eating everything on holiday in India"),
         ("A", "08:56", "And then, do you take any supplements at all?", "10:12", "Whey protein powder by own nutrition.", "ChatGPT as dietitian, omega-3 after the shake, multivitamin, whey"),
         ("A", "10:22", "I'm just going to start filling in some advice", "10:37", "No. Okay. I should.", "the vitamin D question"),
         ("A", "10:52", "So one thing I would say is", "12:16", "and things like that, okay?", "Oct-Apr, 1,000 IU/day, weekly 3,000 IU option, max 4,000 IU; bones, immunity, inflammation"),
     ]},
    {"title": "IF I FALL, TAKE ME OUT", "kicker": "salty sweat, calf cramps and only 2 gels",
     "summary": "Salt crust on his face after every 10K, cramps on the sandbag lunges at HYROX and in a 70.3, and a race fuelled by just two gels. Is it sodium, or is it the muscle?",
     "keep": [
         ("A", "12:30", "how do you know that you sweat a lot of salt?", "13:41", "you said you were a cramper.", "the salt-on-my-face test, Gatorade after, 'is that why I cramp?'"),
         ("A", "13:44", "So this happened like the one of the reason", "14:07", "when I did my high rocks.", "why he came: 'I cramp a lot'"),
         ("A", "14:14", "So after my six kilometers of run", "16:12", "and see if it helps", "HYROX lunges, 'if I fall, just take me out', the 70.3 cramps; muscle vs sodium debate"),
         ("A", "16:13", "So I guess I might then ask like", "18:02", "not allowing me to do that.", "electrolytes in Ironman vs none in HYROX: 2 gels in 1:42; 'I had the energy, my legs didn't'"),
     ]},
    {"title": "THE 1 KG = 1 LITRE RULE", "kicker": "the two-scale sweat test anyone can do",
     "summary": "One gulp of water every 12 minutes - is that enough? Carrie's sweat test: weigh before and after, every kilo lost is a litre to replace plus 250-500 ml, then swap water for an electrolyte drink or sodium capsules.",
     "keep": [
         ("A", "18:12", "So how about your water intake", "19:47", "That's not bad. That's not bad.", "arrive hydrated; one gulp per km, every ~12 min"),
         ("A", "19:48", "I mean, I don't know if I'm keeping pace", "20:36", "workout gear. Okay. Yeah.", "weigh before and after, same clothes"),
         ("A", "20:50", "But if you weigh yourself before", "22:00", "So it's water and sodium, okay?", "74 -> 73 kg = 1 L; drink it back + 250-500 ml"),
         ("A", "22:01", "So what I would suggest is when you're hydrating", "23:34", "I shall look into that.", "sports drink instead of water; learn its sodium; or sodium capsules with each gel"),
     ]},
    {"title": "SALT PILLS, CAFFEINE OR CARBS?", "kicker": "why my last 1K took twice as long",
     "summary": "Cramps fading in training points to muscle adaptation. Then race fuel decoded: 1,000 mg of sodium in one LMNT packet, caffeine only lowers perceived effort (save it for the end), and carbs keep the last 1K as fast as the first.",
     "keep": [
         ("A", "23:38", "You don't ever seem to cramp in training.", "24:06", "investigate a little bit myself.", "cramps with swim fins"),
         ("A", "24:26", "but right now, because I have done it like multiple times,", "24:58", "Okay, good.", "cramping less = muscle adaptation"),
         ("A", "24:59", "Okay, so I guess what I'm wondering,", "26:06", "have a curious question", "LMNT: 1,000 mg sodium per packet, for salty sweaters; train with it first"),
         ("A", "26:08", "what difference that would make", "27:11", "an extra push", "carb gel vs caffeine gel: caffeine = lower perceived effort, use it late"),
         ("A", "27:15", "I mean, I realize in the high rocks training,", "28:20", "work on do you know what I mean", "carbs during HYROX keep the last 1K = first 1K; 'my last one took twice the time'"),
     ]},
    {"title": "STRONGER WITHOUT GETTING SLOWER", "kicker": "the 4-month plan: strength plus speed",
     "summary": "Nizam's goal for the next four months: get stronger and faster. Carrie: training drives muscle, food lets it happen, and the trick is not gaining so much you slow down. Plus the cramp verdict: try electrolytes on lunge days.",
     "keep": [
         ("A", "28:22", "and I guess we could say like what are your goals", "28:38", "one of the key pieces in this.", "the goal question"),
         ("A", "28:54", "So mostly my focus will be into like running,", "28:59", "with my strength training,", "running + strength"),
         ("A", "29:09", "My body adapts to the food that I eat", "30:24", "a fine balance. Right.", "70-80 kg swings; gain muscle, strength shrinking; eat enough but don't get slower"),
         ("A", "30:26", "I don't know where I might put in my gym session.", "31:29", "to do the gym, right?", "his ideal day; HYROX doesn't need volume - drop some for the gym"),
         ("A", "31:42", "let's just gear in on this for a minute.", "32:48", "Just see. Yeah. Okay.", "cramps only in competition; 2 km + lunges = legs gone; test electrolytes on lunge days"),
     ]},
    {"title": "IS THE 30-MIN WINDOW REAL?", "kicker": "eat before, refuel after a morning lift",
     "summary": "A sample gym morning: you wake up dehydrated, so drink between every set; don't lift fasted (banana + peanut butter); then refuel within 2 hours - or within 30 minutes if you train again that day.",
     "keep": [
         ("A", "32:49", "Okay. So what I might do here", "33:26", "just drink it to your content.", "sample day 1: gym first thing, water every set change"),
         ("A", "33:30", "Yeah, just make sure it's regular.", "36:09", "this is just a starting point.", "1 L bottle, you wake up dry, don't train fasted: banana + PB or PB toast"),
         ("A", "36:10", "Yeah. Okay. So then you're drinking water during your training.", "36:31", "probably rush to work.", "post-workout reality: rushing to work"),
         ("A", "36:46", "So gym is in my same apartment,", "37:00", "So it's not that far.", "shower, change, 10 minutes to work"),
         ("A", "37:09", "So typically we are seeing somewhere between 35 to 40 minutes", "39:11", "keep the recipe the same for now.", "carbs + protein while showering; the 30-min vs 2-hour window"),
         ("B", "00:00", "It's pretty high carb.", "00:29", "do your homemade protein shape.", "his homemade shake passes; blood work 'looks amazing'"),
     ]},
    {"title": "WILL OMEGA-3 BURN FAT?", "kicker": "the omega myth and what creatine does",
     "summary": "No - omega-3 is just a different kind of fat. Then creatine: it regenerates ATP faster so you can produce more power, it takes longer than a week to work, 5 g a scoop, and it's fine to wait.",
     "keep": [
         ("B", "00:29", "And if I have that omega, will that burn the fat?", "00:51", "different style of fat,", "myth: omega-3 burns fat (clause 'which is less anti-inflammatory' dropped: likely mis-heard)"),
         ("B", "00:56", "The problem is, is that,", "01:23", "end of the world.", "the shake's fat is mostly saturated; carbs + protein matter more than the omega"),
         ("B", "01:30", "I guess I might ask you, have you ever taken creatine?", "03:41", "Based on your body weight, you could do that.", "his plateau theory, ATP explanation, one-week 'placebo', 5-7 g"),
         ("B", "03:49", "It's just that some people will put it", "04:05", "no problem at all with that.", "put it in the shake - or wait, no problem"),
     ]},
    {"title": "50 G OF PROTEIN IS PLENTY", "kicker": "second breakfast, rice and the veg gap",
     "summary": "His 1,000-calorie shake already has 45-50 g of protein - plenty. Next meal within 2 hours, yogurt + two handfuls of granola, then lunch: less rice, a cup of veg, ~2 cooked cups of rice (2 fists).",
     "keep": [
         ("B", "04:08", "So then you're gonna bike or walk to work", "04:51", "not just about protein intake, right?", "1,000 kcal shake, 45-50 g protein = plenty"),
         ("B", "05:01", "And then I would say maybe within this two hour timeframe", "05:19", "I have been just habited to it.", "next meal within 2 h: Greek yogurt + granola, his go-to"),
         ("B", "05:30", "So the Greek yogurt, is it plain?", "05:34", "Plain. Plain. Okay.", "plain yogurt"),
         ("B", "06:05", "And then your granola,", "06:32", "getting more carbs and protein", "two handfuls of granola"),
         ("B", "06:32", "and then your lunch is about three hours or two hours later", "06:51", "chicken or rice and the veggies", "lunch check"),
         ("B", "07:11", "so you don't have to change anything", "07:23", "I think we'll be okay.", "more veg, a bit less rice"),
         ("B", "08:19", "So one thing you could do, you know that gravy", "09:55", "around where it was at.", "veg into the gravy; less training volume = fewer carbs; keep the chicken"),
         ("B", "09:56", "Is it okay? for example I was just wondering", "10:36", "something you just throw it in", "raw baby carrots, frozen veg"),
         ("B", "10:47", "for sure so I'll just put a cup of veggies in there", "12:08", "how much you need.", "a cup of veg; fists -> ~2 cups cooked rice; needs are individual"),
     ]},
    {"title": "DON'T TRAIN ON EMPTY", "kicker": "the 5-hour gap before evening training",
     "summary": "Eat every 3-5 hours. Lunch at 1, training at 6 is a 5-hour gap, so the office fruit stays (2 or 3 - no one gets fat on fruit). Before the session: a small carb primer (fruit snacks, a wafer, a gel) - 'I loaded up on protein and forgot carbs.'",
     "keep": [
         ("B", "12:21", "And then your afternoon snacks,", "13:16", "you've had enough in your day.", "eat every 3-5 hours; long gaps don't refill muscle energy"),
         ("B", "13:58", "Is your evening always going to include some form of activity?", "14:37", "So I'll put your fruit in there.", "1 pm lunch -> 6 pm training = 5 hours"),
         ("B", "14:40", "Do you need three pieces of fruit?", "15:10", "then you have it.", "'no one's getting overweight from eating fruit'"),
         ("B", "17:06", "And then you're going to have this dinner apparently.", "17:17", "a little concerned with, right?", "the dinner worry (pays off in ch 11-13)"),
         ("B", "17:57", "Okay, so a couple of things I'll just pose to you", "19:23", "what kind of protein bar is it though?", "pre-session primer; 'I forgot about carbs'"),
         ("B", "19:28", "It's from pure protein.", "19:47", "it's not bad for carbs.", "20 g protein bar, OK on carbs - also a morning pre-gym option"),
         ("B", "22:00", "i think we just need to give you a couple of recommendations", "22:28", "that's exactly right", "the diagnosis: the later part of the day is the problem"),
         ("B", "22:45", "but with this later day stuff,", "24:10", "hard workout. Okay.", "move a fruit or a gel to just before a hard session; a gel won't upset a swim"),
     ]},
    {"title": "TOO TIRED TO COOK?", "kicker": "no-cook dinners after a night session",
     "summary": "No energy after an evening session? Overnight oats made the night before (eat them at the gym), food between cardio and weights, a tuna sandwich, and hard-boiled eggs that keep a week in the shell.",
     "keep": [
         ("B", "24:11", "And then I would say as soon as you are done,", "24:37", "veggies in there too, I would admit.", "the default: a balanced dinner"),
         ("B", "25:12", "but if you can't make that meal", "25:15", "make that meal", "the fallback"),
         ("B", "25:20", "could you do like overnight oats", "26:14", "it's basically eaten cold.", "overnight oats, made the night before"),
         ("B", "26:17", "do you think you'd even like that idea?", "27:07", "between my sleep and my dinner.", "'you come home with no energy'; time + a gap before sleep"),
         ("B", "27:18", "Cause you need to have something.", "27:47", "right there after my workout.", "eat it from the backpack at the gym"),
         ("B", "28:10", "let's say you're now doing a double workout", "29:34", "depending how intense it is.", "cardio then gym: eat in between; people eat at the gym"),
         ("B", "29:55", "Okay. Now another idea that you could easily take with you", "30:50", "can tuna, spread it, yeah.", "tuna sandwich = protein + carbs"),
         ("B", "30:51", "Now, another idea that you could do in the evening,", "31:46", "some roti", "hard-boiled eggs keep a week in the shell"),
     ]},
    {"title": "A PROTEIN SHAKE IS NOT DINNER", "kicker": "why the shake alone isn't enough",
     "summary": "'Your protein shake is not enough for you.' Carrie's real-food swaps: a Greek-yogurt or cottage-cheese smoothie with frozen fruit, and - after Nizam's no-fish-with-dairy rule - simply two tuna sandwiches.",
     "keep": [
         ("B", "32:15", "The other thing is you could say, well, I like those Alani shakes.", "32:59", "Is that what it is? Yeah. Okay.", "an Alani shake still needs carbs; shake + sandwich? 'No.'"),
         ("B", "34:04", "Really at the end of the day,", "35:04", "is what I was saying. that's all.", "'your protein shake is not enough for you'; real food vs accessibility"),
         ("B", "35:08", "Do you like smoothies?", "36:36", "I can try, but certainly not.", "yogurt/cottage cheese + frozen fruit smoothie; 'no fish with dairy'"),
         ("B", "37:51", "So one of them was the smoothie,", "38:17", "say two sandwiches.", "make it simple: two sandwiches"),
         ("B", "38:19", "So, but it will be like my probably post workout meal", "38:36", "it's your post workout.", "when to eat them"),
     ]},
    {"title": "CAN I GAIN MUSCLE BY RACE DAY?", "kicker": "why the evening is the real problem",
     "summary": "The verdict: anyone can gain muscle - the training drives it, but he doesn't always eat at night, and that's the one thing to fix. Meal prep 2-3 hours on a weekend, quick hacks, and why skipping dinner after a night session kills the next morning's gains.",
     "keep": [
         ("B", "41:02", "Cause I think really overall after working through all of this,", "41:28", "can be optimized.", "the diagnosis: it's the evening"),
         ("B", "41:40", "do you think realistically", "41:56", "like more muscle mass", "the big question"),
         ("B", "42:05", "i honestly think like can you gain muscle mass", "42:38", "have a huge response.", "'anyone can gain muscle mass'"),
         ("B", "42:50", "I didn't change a lot.", "43:02", "Do you know what I mean?", "only change: optimise the evening"),
         ("B", "43:11", "But I'm gathering from our discussion", "44:37", "perfectly enough time", "'you don't always eat at night'; meal prep 2-3 h at the weekend"),
         ("B", "44:37", "okay because even i will tell you", "45:38", "you just need some quick hacks", "sloppy joes, protein oatmeal pancakes, hash browns + eggs"),
         ("B", "45:41", "so what are we trying to optimize", "47:04", "Gotcha. Yeah.", "carbs + protein + colour; no dinner after a night session = no muscle from the morning lift"),
     ]},
    {"title": "MULTIVITAMIN OR REAL FOOD?", "kicker": "what you can't get in a bottle",
     "summary": "Three fruits a day cover vitamin C, but no greens or orange veg means low vitamins A and K. Spinach or kale in the shake, a salad at dinner - or a multivitamin on no-veg days. Real food wins: fibre and phytochemicals. And no, supplements aren't prescribed - they're cheap.",
     "keep": [
         ("B", "47:05", "And like taking, for example, you suggested creatine", "47:20", "It's a good point.", "Nizam asks about micronutrients"),
         ("B", "47:31", "So if you're eating three pieces of fruit a day,", "49:19", "more into your meals.", "vit C covered, A + K missing; spinach/kale/salad or a multivitamin; phytochemicals"),
         ("B", "49:22", "If you just at the end of the day are", "49:51", "your workouts and everything", "offer: a follow-up just on veggies; today was about the training"),
         ("B", "51:22", "Do they come under prescribed medicines?", "52:05", "they're really not expensive", "OTC, no prescription; creatine and vitamin D can wait, they're cheap"),
     ]},
]

OUTRO = [
    ("B", "50:16", "So what I'm going to do is I'm going to print this", "50:57", "getting veggies in your diet.",
     "the plan in one line (focus on evening eating) + 'we meet again in a month'"),
]

# hero lines: (file, approx, exact phrase, on-screen text, style)
HERO = [
    ("A", "00:06", "Nizam how much do you weigh?", "74 KG", "number"),
    ("A", "02:45", "that's never going to recover you enough.", "A SHAKE WON'T RECOVER YOU", "punch"),
    ("A", "04:29", "Rice is huge, I take a lot of rice.", "RICE IS HUGE", "quote"),
    ("A", "05:34", "one banana, one apple and one orange.", "1 BANANA · 1 APPLE · 1 ORANGE", "number"),
    ("A", "06:10", "I should tell three, but I might lie,", "I SHOULD SAY 3 LITRES...", "quote"),
    ("A", "06:45", "you would only need about 2 .2", "2.2 L A DAY", "number"),
    ("A", "09:15", "before I started iron one chat, GPD was kind of my dietitian.", "CHATGPT WAS MY DIETITIAN", "quote"),
    ("A", "11:03", "October to April,", "OCTOBER -> APRIL", "punch"),
    ("A", "11:08", "So I've listed 1 ,000 IUs a day.", "1,000 IU A DAY", "number"),
    ("A", "11:55", "maximum amount you should take in a day is 4 ,000.", "MAX 4,000 IU", "number"),
    ("A", "12:58", "I can see salt on my eyes,", "SALT ON MY FACE", "quote"),
    ("A", "13:51", "I cramp a", "I CRAMP. A LOT.", "quote"),
    ("A", "14:37", "If I fall, just take me out", "IF I FALL, TAKE ME OUT", "quote"),
    ("A", "16:01", "Is it more of a muscular thing", "MUSCLE OR SODIUM?", "myth"),
    ("A", "16:57", "So I had just two gels.", "2 GELS IN 1:42", "number"),
    ("A", "17:28", "it's not about the carb loading.", "IT'S NOT THE CARBS", "myth"),
    ("A", "17:59", "I had the energy, it's just like my legs are not allowing me", "I HAD THE ENERGY", "quote"),
    ("A", "19:41", "six minutes of run plus four minutes of station", "1 GULP / 12 MIN", "number"),
    ("A", "21:00", "So if you went in at 74 kilos and you came out at 73,", "74 KG -> 73 KG", "number"),
    ("A", "21:05", "you've lost a liter of water", "1 KG = 1 LITRE", "number"),
    ("A", "21:29", "like about 250 mils more, 500 mils more.", "+250-500 ML", "number"),
    ("A", "21:58", "So it's water and sodium, okay?", "WATER + SODIUM", "punch"),
    ("A", "24:34", "that's showing me a muscle adaptation", "MUSCLE ADAPTATION", "punch"),
    ("A", "25:36", "is a thousand milligrams of sodium.", "1,000 MG SODIUM", "number"),
    ("A", "26:42", "It's making you believe that you can work harder,", "CAFFEINE = BELIEF", "myth"),
    ("A", "27:52", "the last one I took twice the time", "LAST 1K: 2x SLOWER", "number"),
    ("A", "29:43", "the pretty much goal will be like get strength and get faster.", "STRONGER + FASTER", "punch"),
    ("A", "30:13", "not gaining too much that you become slower.", "DON'T GET SLOWER", "punch"),
    ("A", "34:09", "you're waking up a little bit drier", "YOU WAKE UP DRY", "punch"),
    ("A", "35:33", "You're gonna be using yesterday's energy stores", "YESTERDAY'S ENERGY", "punch"),
    ("A", "38:30", "Isn't it 30 minutes?", "30 MIN? OR 2 HOURS?", "myth"),
    ("B", "00:47", "It's not going to burn anything.", "OMEGA-3 DOESN'T BURN FAT", "myth"),
    ("B", "02:44", "it helps to regenerate ATP quicker.", "CREATINE = FASTER ATP", "punch"),
    ("B", "04:35", "And that's plenty of protein.", "50 G = PLENTY", "number"),
    ("B", "04:47", "gaining muscle is not just about protein intake,", "MUSCLE ≠ JUST PROTEIN", "myth"),
    ("B", "11:52", "two cups of rice cooked.", "2 FISTS = 2 CUPS RICE", "number"),
    ("B", "12:37", "need to eat every three to five hours.", "EAT EVERY 3-5 HOURS", "number"),
    ("B", "14:25", "that's five hours.", "1 PM -> 6 PM = 5 HOURS", "number"),
    ("B", "14:56", "no one's getting overweight", "NO ONE GETS FAT ON FRUIT", "punch"),
    ("B", "19:08", "Because that's the muscle building block,", "I FORGOT ABOUT CARBS", "quote"),
    ("B", "22:19", "it's this later part of", "THE EVENING IS THE PROBLEM", "punch"),
    ("B", "26:44", "I'm hearing that you come home and you have no energy", "NO ENERGY TO COOK", "quote"),
    ("B", "31:16", "They stay good in the fridge for a week,", "EGGS: 1 WEEK IN THE SHELL", "number"),
    ("B", "34:23", "Because I just think your protein shake is not enough for you.", "A SHAKE IS NOT ENOUGH", "punch"),
    ("B", "38:14", "Let's make this simple and say two sandwiches.", "JUST EAT 2 SANDWICHES", "quote"),
    ("B", "42:07", "anyone can gain muscle mass", "ANYONE CAN GAIN MUSCLE", "punch"),
    ("B", "43:11", "you don't always eat at night.", "YOU DON'T EAT AT NIGHT", "punch"),
    ("B", "46:37", "you might not be able to build mass after that.", "NO DINNER = NO GAINS", "myth"),
    ("B", "49:09", "You can't get that in a bottle.", "CAN'T GET THAT IN A BOTTLE", "punch"),
]

# key facts: (file, approx, exact phrase, fact)
FACTS = [
    ("A", "00:12", "74 kilos.", "Nizam's body weight: 74 kg (basis for every number below)"),
    ("A", "02:05", "roughly around 100 to 150 grams.", "Office breakfast: 100-150 g granola into 150 g plain Greek yogurt + a little honey"),
    ("A", "02:42", "in the event you just do a protein shake,", "A protein shake alone after an evening workout is never enough to recover"),
    ("A", "03:50", "200 to 300 grams of rice along with 150 ish gram of chicken.", "His lunch: 200-300 g rice + ~150 g chicken"),
    ("A", "05:00", "so definitely probably need more veggies in your diet", "Needs more vegetables (nutrient standpoint)"),
    ("A", "05:34", "one banana, one apple and one orange.", "Afternoon snack: 1 banana + 1 apple + 1 orange, every day"),
    ("A", "06:45", "you would only need about 2 .2", "Daily water at 74 kg: ~2.2 L (more on heavy-sweat days)"),
    ("A", "11:03", "October to April,", "Vitamin D supplement every day, October to April"),
    ("A", "11:08", "So I've listed 1 ,000 IUs a day.", "Vitamin D dose: 1,000 IU per day (can't get enough from diet)"),
    ("A", "11:49", "a couple of times a week and take three at one time.", "Alternative: 3,000 IU a couple of times a week (fat-soluble, stored)"),
    ("A", "11:55", "maximum amount you should take in a day is 4 ,000.", "Upper limit: 4,000 IU vitamin D per day"),
    ("A", "12:09", "it will help with your bone strength,", "Vitamin D: bone strength, may help immunity and inflammation"),
    ("A", "16:01", "Is it more of a muscular thing", "Cramping cause is debated (muscular vs sodium/hydration) - optimise hydration + sodium anyway"),
    ("A", "16:57", "So I had just two gels.", "His HYROX fuel: 2 gels in 1 h 42 min (at ~40 min and ~1:15-1:20), no sodium"),
    ("A", "19:41", "six minutes of run plus four minutes of station", "HYROX drinking: one cup/gulp of water per km, roughly every 12 minutes"),
    ("A", "20:25", "You have to be the same, how you do the pre -weight and the post -weight,", "Sweat test: weigh before and after in the same clothing (ideally none)"),
    ("A", "21:00", "So if you went in at 74 kilos and you came out at 73,", "74 kg -> 73 kg = 1 kg lost = 1 L of sweat not replaced"),
    ("A", "21:29", "like about 250 mils more, 500 mils more.", "Rehydrate the loss + 250-500 ml extra (1.2-1.5 L per kg) because some is urinated out"),
    ("A", "22:16", "could you do a sports drink instead of the little water?", "In races: swap the water cups for a sports/electrolyte drink"),
    ("A", "22:52", "find out what kind of electrolyte drink they're doing", "Find out the event's electrolyte drink and its sodium content"),
    ("A", "23:19", "when you did your gel, I would do your sodium capsules then.", "If no electrolyte drink: take sodium capsules at the same time as each gel"),
    ("A", "25:36", "is a thousand milligrams of sodium.", "LMNT: 1,000 mg sodium per packet, little/no carbohydrate - for salty sweaters"),
    ("A", "25:49", "but you'd almost to train with it", "Trial any electrolyte drink in training before race day"),
    ("A", "26:45", "like it's kind of decreasing your perceived effort", "Caffeine = stimulant that lowers perceived effort"),
    ("A", "27:04", "Normally when people use caffeine they might use it more towards the end", "Caffeine: use it late in a long race; all race long upsets the gut"),
    ("A", "27:27", "if you want your first repeat,", "Carbs during interval-type racing keep the last 1K as good as the first"),
    ("A", "32:41", "you might want to try all the electrolyte drink", "Test the electrolyte drink on run + lunge training days"),
    ("A", "33:58", "drink you know almost between every set", "Morning gym: drink almost between every set (heavy sweater, 1 L bottle)"),
    ("A", "34:09", "you're waking up a little", "You start a morning session not fully hydrated"),
    ("A", "35:41", "So let's say something like a banana. You could even put some peanut butter on it", "Before a morning lift: banana (+ peanut butter) or peanut butter on toast"),
    ("A", "37:28", "could you even be drinking something that has carbs and protein in it?", "Start refuelling with carbs + protein while you shower and get ready"),
    ("A", "38:33", "as far as we know it occurs in the first two hours.", "Recovery window: within the first 2 hours"),
    ("A", "38:49", "Okay, so in that case, I would say do it within 30 minutes.", "Training twice that day: refuel within 30 minutes"),
    ("B", "02:44", "it helps to regenerate ATP quicker.", "Creatine regenerates ATP faster -> more power -> muscle develops faster"),
    ("B", "03:11", "It takes longer than", "Creatine takes longer than a week to work; some people don't respond"),
    ("B", "03:34", "Yeah, five.", "Creatine: one 5 g scoop (5-7 g OK at his body weight)"),
    ("B", "04:23", "It has like roughly around 1000 calories.", "His homemade shake: ~1,000 kcal"),
    ("B", "04:30", "roughly 45 to 50 grams of protein in it.", "45-50 g protein per shake = plenty, no need for more"),
    ("B", "05:01", "And then I would say maybe within this two hour timeframe", "Next meal (second breakfast) within 2 hours of the post-workout shake"),
    ("B", "06:13", "Yeah, two handfuls.", "Granola: two handfuls"),
    ("B", "08:27", "you could just add some veggies while that's cooking,", "Add vegetables to the curry/gravy while it cooks"),
    ("B", "09:06", "you won't need quite as much rice.", "HYROX = less training volume than Ironman -> slightly less rice, keep the chicken"),
    ("B", "10:14", "Yeah just get some raw baby carrots", "Easy veg: raw baby carrots in a container, or a bag of frozen veg"),
    ("B", "10:47", "for sure so I'll just put a cup of veggies in there", "Lunch: 1 cup of vegetables, cooked or raw"),
    ("B", "11:50", "So that's about two cups of rice cooked.", "Rice: ~2 cups cooked (about 2 fists)"),
    ("B", "12:36", "Typically people need to eat every three to five hours.", "Eat every 3-5 hours"),
    ("B", "14:25", "If you're eating that at one and you're not working out till six, that's five hours.", "Lunch 1 pm -> training 6 pm = 5-hour gap: needs a snack"),
    ("B", "14:43", "You might only need two.", "2-3 pieces of fruit in the afternoon (flexible)"),
    ("B", "18:30", "some Welch's fruit snacks or a little honey stinger wafer", "Pre-session primer: fruit snacks, a Honey Stinger wafer, a small bar or a gel"),
    ("B", "19:34", "20 grams of protein in it.", "Pure Protein bar: 20 g protein, OK carbs - pre-workout option instead of banana + PB"),
    ("B", "23:12", "you could move one of your two or three pieces of fruit to just before you do the exercise", "Hard evening session: move a fruit (or a gel) to just before it"),
    ("B", "23:50", "Well, if it's a gel, it won't.", "A gel before a swim won't upset the stomach"),
    ("B", "25:22", "could you do like overnight oats", "No-cook dinner: overnight oats made the night before, eaten cold"),
    ("B", "28:31", "Because most times when people do weight kind of resistance training,", "Weights jostle the stomach less - you can eat between cardio and gym"),
    ("B", "30:23", "Okay, because tuna's got your protein. You've got your carbs with the bread", "Tuna sandwich = protein + carbs"),
    ("B", "31:16", "They stay good in the fridge for a week, provided you keep them in their shell.", "Hard-boiled eggs keep 1 week in the fridge in their shell"),
    ("B", "32:22", "You could, but you'd still need the carbs with it.", "An Alani/protein shake still needs carbs with it"),
    ("B", "35:33", "just use some Greek yogurt or even cottage cheese with some frozen fruit", "Dinner smoothie: Greek yogurt or cottage cheese + frozen fruit (+ berries, banana)"),
    ("B", "38:14", "Let's make this simple and say two sandwiches.", "Fallback dinner: two tuna sandwiches"),
    ("B", "42:07", "anyone can gain muscle mass", "Anyone can gain muscle - training drives it, fuel enables it"),
    ("B", "44:30", "I think I can spare that maybe two hours", "Meal prep: 2-3 hours one weekend day (chicken, rice, veg)"),
    ("B", "45:57", "Ideally, you've got some color in there too.", "Dinner goal: carbs + protein + colour (veg)"),
    ("B", "46:37", "You might not get, you might not be able to build mass after that.", "No dinner after a night workout -> morning lift builds little muscle"),
    ("B", "47:31", "So if you're eating three pieces of fruit a day,", "3 fruits a day ~ covers vitamin C"),
    ("B", "47:41", "and they're more like vitamin A and vitamin", "Likely low: vitamin A and K (no greens, no orange veg)"),
    ("B", "48:00", "a bag of spinach or a of kale that you keep in the freezer", "Frozen spinach/kale into the morning shake, or a salad at lunch/dinner"),
    ("B", "48:47", "Why don't we put the days that you're not eating veggies, that you do multivitamin mineral supplement.", "Multivitamin-mineral only on no-veg days"),
    ("B", "49:05", "There's things called phytochemicals", "Real food adds fibre + phytochemicals a pill can't"),
    ("B", "51:48", "They're available without prescription.", "Supplements are OTC (no prescription) and inexpensive"),
    ("B", "50:28", "And then I'd say in a month,", "Follow-up in a month, 30 min, can be virtual"),
]

# why each dropped span went (matched to the gap that contains the time)
REASONS = [
    ("A", "00:30", "pre-roll: mic check, moving the camera, 'can we start from here', typing set-up"),
    ("A", "01:00", "pre-roll: silence before Carrie starts"),
    ("A", "02:56", "dead end: 'I don't know the exact grams of carbs' / 'another recovery'"),
    ("A", "04:08", "minor: chicken portion '180' back-and-forth"),
    ("A", "06:20", "back-and-forth: 'two ish, two to three, I refill twice or thrice' (kept the joke + the 2.2 L answer)"),
    ("A", "07:12", "garbled filler ('just once I don't sure')"),
    ("A", "08:48", "filler: 'just looking this over'"),
    ("A", "10:18", "filler: 'so I guess a couple of things'"),
    ("A", "10:45", "garbled ASR ('after post-sex') - unusable caption"),
    ("A", "12:20", "repeat of the 2.2 L water advice + garbled 'are you okay / you sold'"),
    ("A", "13:43", "false start ('So as you saw in the')"),
    ("A", "14:10", "confusing aside about a similar event in India"),
    ("A", "18:06", "logistics: Carrie looking for a document"),
    ("A", "20:40", "repetition: clothing makes the weigh-in imperfect (kept the clearer take)"),
    ("A", "24:15", "ramble: biking uphill 35 min to the pool (kept the adaptation point)"),
    ("A", "26:07", "garbled ASR ('on the auto flu is that')"),
    ("A", "27:13", "filler"),
    ("A", "28:45", "aside: no sprint/swim races planned"),
    ("A", "29:02", "false start: 'let me ask this question, is it possible...'"),
    ("A", "31:33", "unclear phrase ('achieve as much mass rate') + filler"),
    ("A", "33:28", "repetition: 'just make sure it's regular' (kept one take)"),
    ("A", "36:35", "logistics: 'how long will it take you to get to work'"),
    ("A", "37:03", "commute detail (5 min bike / 10 min walk)"),
    ("B", "00:53", "likely mis-heard clause ('less anti-inflammatory') - avoided a wrong claim on screen"),
    ("B", "01:26", "garbled ASR ('naturally getting a little bit of a loss')"),
    ("B", "03:43", "repetition: 'if you want to wait... no problem' (kept the closing take)"),
    ("B", "04:53", "dead air: Carrie doing maths ('74, sorry')"),
    ("B", "05:22", "filler: 'would you recommend something / we could put that as an option'"),
    ("B", "05:45", "detail: the 750 g tub maths (150 g a day) - the 150 g yogurt portion is already stated in chapter 1"),
    ("B", "07:00", "rambling set-up of the veggie point (kept the sharp version)"),
    ("B", "07:50", "tangent: his home breakfast alternatives (mixed veg + eggs)"),
    ("B", "10:40", "garbled ASR ('salami with raw carrots')"),
    ("B", "12:15", "minor: water with meals"),
    ("B", "13:30", "repeated question ('I heard the question wrong, can you repeat')"),
    ("B", "15:20", "evening-session length + intervals aside (an hour of sweat)"),
    ("B", "16:30", "logistics: commute to Mount Royal, bus vs bike"),
    ("B", "17:30", "logistics: no car, bus vs bike, energy-expenditure ramble"),
    ("B", "19:25", "garbled ASR + label check"),
    ("B", "20:40", "dead-end scenarios: lunch-hour office gym, backup plans, double day"),
    ("B", "22:38", "filler: 'I can always add more ideas later'"),
    ("B", "24:40", "repetition of the balanced-dinner idea + 'because you have the energy' (mis-heard, meaning flips)"),
    ("B", "27:10", "filler: 'if I start working again in the morning... does this make sense'"),
    ("B", "27:52", "recap of the day before the double-workout scenario"),
    ("B", "29:40", "filler: 'I'll just give you this as an idea'"),
    ("B", "31:55", "unresolved question + 24 s silence"),
    ("B", "33:30", "rambling re-explanation: 'I'm just giving you different scenarios'"),
    ("B", "37:00", "brand tangent: RX bars"),
    ("B", "39:30", "wrap-up chatter: 'is that giving you something to work with', meal-idea list logistics"),
    ("B", "41:58", "Nizam's add-on ('we might touch bases') before Carrie's answer"),
    ("B", "42:45", "trailing unfinished sentence"),
    ("B", "43:06", "filler"),
    ("B", "47:25", "garbled ASR ('magnesium on the knife')"),
    ("B", "49:55", "wrap-up: 'have I gone over time', 'we should end it'"),
    ("B", "51:10", "logistics: printing downstairs"),
    ("B", "50:59", "end of outro (used separately)"),
    ("B", "52:10", "walk-out logistics: picking up the print"),
]


def build():
    plan = {"est_minutes": 0, "title": TITLE, "subtitle": SUBTITLE, "cold_open": [], "chapters": [], "outro": [],
            "hero_lines": [], "key_facts": [], "dropped": []}
    kept = []  # (f, s, e, i, j, chapter_n)
    total = 0.0
    co_t = 0.0
    for (f, t1, p1, t2, p2, who, why) in COLD:
        s, e, i, j = resolve(f, t1, p1, t2, p2)
        d = est_idx(f, i, j); co_t += d
        plan["cold_open"].append({"f": f, "start": s, "end": e, "who": who, "text": text_idx(f, i, j), "why": why,
                                  "est_s": round(d, 1)})
    total += co_t
    out_t = total
    for n, ch in enumerate(CHAPTERS, 1):
        keeps, ct = [], 0.0
        for (f, t1, p1, t2, p2, note) in ch["keep"]:
            s, e, i, j = resolve(f, t1, p1, t2, p2)
            d = est_idx(f, i, j); ct += d
            keeps.append({"f": f, "start": s, "end": e, "note": note, "est_s": round(d, 1),
                          "first": " ".join(RAW[f][i:i + 6]), "last": " ".join(RAW[f][max(i, j - 5):j + 1]),
                          "_i": i, "_j": j})
            kept.append((f, s, e, i, j, n))
        plan["chapters"].append({"n": n, "title": ch["title"], "kicker": ch["kicker"], "summary": ch["summary"],
                                 "out_start_s": round(out_t, 1), "est_minutes": round(ct / 60, 2), "keep": keeps})
        assert len(ch["title"]) <= 34, ch["title"]
        assert len(ch["kicker"]) <= 40, ch["kicker"]
        out_t += ct
        total += ct
    # adjacent ranges whose boundary words touch (no gap): split exactly between the two words
    allk = [k for ch in plan["chapters"] for k in ch["keep"]]
    for a, b in zip(allk, allk[1:]):
        if a["f"] == b["f"] and b["start"] < a["end"]:
            if b["_i"] <= a["_j"]:
                raise SystemExit(f"overlapping keep ranges: {a} / {b}")
            w = L2.WS[a["f"]]
            mid = round((w[a["_j"]][1] + w[b["_i"]][0]) / 2, 3)
            CLAMPS.append((a["f"], mmss(mid), "touching ranges split at", mid))
            a["end"] = b["start"] = mid
    for k in allk:
        k.pop("_i"); k.pop("_j")
    ot = 0.0
    for (f, t1, p1, t2, p2, note) in OUTRO:
        s, e, i, j = resolve(f, t1, p1, t2, p2)
        d = est_idx(f, i, j); ot += d
        plan["outro"].append({"f": f, "start": s, "end": e, "text": text_idx(f, i, j), "note": note, "est_s": round(d, 1)})
        kept.append((f, s, e, i, j, 0))
    total += ot
    plan["outro_out_start_s"] = round(out_t, 1)
    plan["est_minutes"] = round(total / 60, 2)
    plan["est_breakdown_s"] = {"cold_open": round(co_t, 1), "chapters": round(total - co_t - ot, 1), "outro": round(ot, 1)}

    # chronology check across chapters (A then B)
    order = {"A": 0, "B": 1}
    seq = [(order[k[0]], k[1], k[2], k[5]) for k in kept if k[5]]
    for a, b in zip(seq, seq[1:]):
        if (b[0], b[1]) < (a[0], a[2] - 0.05):
            raise SystemExit(f"chapters not chronological: {a} -> {b}")

    def inside(f, i, n):
        for (kf, s, e, ki, kj, cn) in kept:
            if kf == f and ki <= i and i + n - 1 <= kj:
                return cn
        return None

    for (f, t, phrase, screen, style) in HERO:
        i, n = L2.find(f, t, phrase)
        cn = inside(f, i, n)
        if cn is None:
            raise SystemExit(f"hero line outside kept ranges: {f} {t} '{phrase}'")
        assert len(screen.split()) <= 6 or style == "number", screen
        plan["hero_lines"].append({"f": f, "t": round(L2.WS[f][i][0], 3), "phrase": " ".join(RAW[f][i:i + n]),
                                   "screen": screen, "style": style, "chapter": cn or "outro"})
    for (f, t, phrase, fact) in FACTS:
        i, n = L2.find(f, t, phrase)
        cn = inside(f, i, n)
        if cn is None:
            raise SystemExit(f"key fact outside kept ranges: {f} {t} '{phrase}'")
        plan["key_facts"].append({"f": f, "t": round(L2.WS[f][i][0], 3), "phrase": " ".join(RAW[f][i:i + n]),
                                  "fact": fact, "chapter": cn or "outro"})

    # dropped = every uncovered source span (cold-open reuse does not count as coverage)
    ends = {"A": L2.WS["A"][-1][1] + 0.3, "B": L2.WS["B"][-1][1] + 0.3}
    for f in ("A", "B"):
        cov = sorted((s, e) for (kf, s, e, *_r) in kept if kf == f)
        cur = 0.0
        gaps = []
        for s, e in cov:
            if s - cur > 0.6:
                gaps.append((cur, s))
            cur = max(cur, e)
        if ends[f] - cur > 0.6:
            gaps.append((cur, ends[f]))
        for a, b in gaps:
            words = [x for x in L2.WS[f] if a <= x[0] < b]
            if not words:
                continue
            rs = [r for (rf, rt, r) in REASONS if rf == f and a <= B.sec(rt) < b]
            reason = "; ".join(rs) if rs else ("tightening: false start / filler / repeat" if b - a < 15 else "UNEXPLAINED")
            tt = est_idx(f, L2.WS[f].index(words[0]), L2.WS[f].index(words[-1]))
            plan["dropped"].append({"f": f, "start": round(a, 2), "end": round(b, 2), "reason": reason,
                                    "words": len(words), "est_s": round(tt, 1),
                                    "text": " ".join(RAW[f][L2.WS[f].index(words[0]):L2.WS[f].index(words[0]) + 14]) + (" ..." if len(words) > 14 else "")})
    return plan


def md(plan):
    L = []
    a = L.append
    tot = plan["est_minutes"]
    a(f"# Carrie ep01 v4 - edit plan: *{plan['title']}*\n")
    a(f"{plan['subtitle']}\n")
    bd = plan["est_breakdown_s"]
    a(f"**Estimated runtime: {tot:.1f} min** (cold open {bd['cold_open']:.0f} s + chapters {bd['chapters'] / 60:.1f} min + outro {bd['outro']:.0f} s). "
      "Estimate = word durations + inter-word gaps capped at 0.35 s, i.e. after the engine's pause/um removal. "
      "Not included: the title sting after the cold open and any chapter cards that do not run over speech.\n")
    a("Source: A = `IMG_4342-001` (0-2351 s), B = `IMG_4343-002` (0-3151 s). Times below are source seconds (mm:ss).\n")
    a("## Cold open\n")
    a("| # | Src | In - out | Who | Line | Est s | Why |")
    a("|---|---|---|---|---|---|---|")
    for k, c in enumerate(plan["cold_open"], 1):
        a(f"| {k} | {c['f']} | {mmss(c['start'])} - {mmss(c['end'])} | {c['who']} | \"{c['text']}\" | {c['est_s']} | {c['why']} |")
    a(f"\nCold open total ~{bd['cold_open']:.0f} s.\n")
    a("## Chapters\n")
    a("| # | Out at | Min | Title | Kicker | Source span |")
    a("|---|---|---|---|---|---|")
    for ch in plan["chapters"]:
        k0, k1 = ch["keep"][0], ch["keep"][-1]
        a(f"| {ch['n']} | {mmss(ch['out_start_s'])} | {ch['est_minutes']:.1f} | **{ch['title']}** | {ch['kicker']} | "
          f"{k0['f']} {mmss(k0['start'])} - {k1['f']} {mmss(k1['end'])} |")
    a(f"| - | {mmss(plan['outro_out_start_s'])} | {bd['outro'] / 60:.1f} | OUTRO | | |")
    a("")
    for ch in plan["chapters"]:
        a(f"### {ch['n']:02d} / {len(plan['chapters'])}  {ch['title']}  ({ch['est_minutes']:.1f} min, out {mmss(ch['out_start_s'])})")
        a(f"*{ch['kicker']}* - {ch['summary']}\n")
        a("| Src | In - out | Est s | Starts | Ends | Note |")
        a("|---|---|---|---|---|---|")
        for k in ch["keep"]:
            a(f"| {k['f']} | {mmss(k['start'])} - {mmss(k['end'])} | {k['est_s']} | \"{k['first']}...\" | \"...{k['last']}\" | {k['note']} |")
        a("")
    a("## Outro\n")
    for o in plan["outro"]:
        a(f"- {o['f']} {mmss(o['start'])} - {mmss(o['end'])} (~{o['est_s']} s): \"{o['text']}\"")
    a("")
    a(f"## Hero lines ({len(plan['hero_lines'])})\n")
    a("| Src | t | Ch | Spoken | On screen | Style |")
    a("|---|---|---|---|---|---|")
    for h in plan["hero_lines"]:
        a(f"| {h['f']} | {mmss(h['t'])} | {h['chapter']} | \"{h['phrase']}\" | **{h['screen']}** | {h['style']} |")
    a("")
    a(f"## Key facts ({len(plan['key_facts'])})\n")
    a("| Src | t | Ch | Anchor phrase | Fact |")
    a("|---|---|---|---|---|")
    for x in plan["key_facts"]:
        a(f"| {x['f']} | {mmss(x['t'])} | {x['chapter']} | \"{x['phrase']}\" | {x['fact']} |")
    a("")
    dr = plan["dropped"]
    big = [d for d in dr if d["est_s"] >= 8]
    small = [d for d in dr if d["est_s"] < 8]
    a(f"## Dropped ({len(dr)} spans, ~{sum(d['est_s'] for d in dr) / 60:.1f} min of tightened speech)\n")
    a("| Src | In - out | Est s | Reason | Starts with |")
    a("|---|---|---|---|---|")
    for d in big:
        a(f"| {d['f']} | {mmss(d['start'])} - {mmss(d['end'])} | {d['est_s']} | {d['reason']} | \"{d['text']}\" |")
    a(f"\nPlus {len(small)} micro-trims under 8 s each (~{sum(d['est_s'] for d in small):.0f} s total: false starts, garbled ASR, repeats, filler) - full list in `edit_plan.json`.\n")
    return "\n".join(L)


if __name__ == "__main__":
    plan = build()
    for c in CLAMPS:
        print("clamp", c)
    print(f"cold open {plan['est_breakdown_s']['cold_open']:.1f} s, outro {plan['est_breakdown_s']['outro']:.1f} s")
    for ch in plan["chapters"]:
        print(f"{ch['n']:2d} {mmss(ch['out_start_s'])} {ch['est_minutes']:5.2f}  {ch['title']}")
    print(f"TOTAL {plan['est_minutes']:.2f} min; hero {len(plan['hero_lines'])}, facts {len(plan['key_facts'])}, dropped {len(plan['dropped'])}")
    unexpl = [d for d in plan["dropped"] if d["reason"] == "UNEXPLAINED"]
    for d in unexpl:
        print("UNEXPLAINED", d["f"], mmss(d["start"]), mmss(d["end"]), d["est_s"], d["text"])
    if not CHECK:
        for name, body in (("edit_plan.json", json.dumps(plan, indent=1, ensure_ascii=False)), ("edit_plan.md", md(plan))):
            tmp = os.path.join(V4, name + ".tmp")
            open(tmp, "w", encoding="utf-8").write(body)
            os.replace(tmp, os.path.join(V4, name))  # atomic swap
        print("wrote v4/edit_plan.json + v4/edit_plan.md")
