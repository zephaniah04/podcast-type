#!/usr/bin/env python3
"""Carrie ep01 long-form v3: the dense edit. Something new on screen every few seconds.

Devices (all pinned to the exact words, searched near an approximate timecode):
  br    full-frame B-roll photo (slow push-in) over the voice
  card  animated side card (numbers, lists, comparisons) next to whoever is talking
  sbs   split screen: Nizam | Carrie
  pip   floating photo card between the two of them (the shot goes wide underneath it)
  wd    kinetic keyword: big type on an accent bar
  st    Fluent 3D emoji floating in the empty side of the frame
plus two automatic passes: 3D emoji on spoken keywords (gap filler) and split screens on quick back-and-forths.

One render chunk per chapter (+ cold open) keeps every final pass to a few dozen overlays.
  python projects/carrie-ep01/build_long3.py          -> long3/*.json, cards_long3.json, fx.json (+ renders fx)
  bash projects/carrie-ep01/render_long3.sh           -> exports/carrie/ep01/L01v3_full-episode.mp4
"""
import json, os, subprocess, sys
NO_RENDER = "--no-render" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_shorts as B  # noqa: E402
import build_long as L  # noqa: E402
import build_long2 as L2  # noqa: E402
P = B.P
EP = B.EP
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(EP, "long3"); os.makedirs(OUT, exist_ok=True)
PY = sys.executable
AF = {"zoom": 1.8, "zoom_right": 1.5, "punch": 1.12, "wide_every": 5, "cy": 0.38, "min_turn": 1.6}
GAP = 0.6
WS = L2.WS
FX, CARDS = {}, []

SHORT = ["What I eat in a day", "How much water", "Supplements + vitamin D", "Salt + cramps", "The sweat test",
         "Sodium, caffeine, gels", "Muscle without slowing down", "Training fasted", "The 30-minute window",
         "Creatine", "50 g of protein", "The 5-hour gap", "I forgot carbs", "No-cook dinners",
         "Muscle before race day", "Meal prep", "Real food vs pills"]

# ------------------------------------------------------------------------------------------- curated beats (v3)
NEW = [
 # ---- A: what I eat in a day
 ("A", "01:46", "sandwich of guacamole", "pip", ("guacamole-toast", "eggs + guac sandwich")),
 ("A", "02:01", "with my granola", "pip", ("granola", "100-150 g granola")),
 ("A", "02:45", "never going to recover you enough", "wd", ("A SHAKE WON'T RECOVER YOU", "not on its own")),
 ("A", "03:47", "chicken breast completely", "pip", ("chicken-breast", "~150 g chicken")),
 ("A", "04:31", "rice is huge", "pip", ("cooked-rice", "a lot of rice")),
 ("A", "04:37", "so you're getting lots of carbs", "wd", ("LOTS OF CARBS", "")),
 ("A", "04:53", "chicken gravy", "pip", ("chicken-curry", "chicken gravy")),
 ("A", "05:15", "between one and nine", "wd", ("1 PM - 9 PM", "what fuels that gap?")),
 ("A", "05:31", "we have like fruits", "pip", ("three-fruits", "office fruit")),
 ("A", "05:55", "i should take something before and after", "wd", ("FUEL BEFORE + AFTER", "still working on it")),
 # ---- water
 ("A", "06:23", "my water bottle in my office", "pip", ("office-bottle", "refilled 2-3x a day")),
 ("A", "07:55", "training more strength", "pip", ("deadlift", "strength + running")),
 ("A", "08:31", "mix of all different indian", "pip", ("india-family-food", "no structured diet")),
 ("A", "08:41", "milkshake used to stay the constant", "st", [("Glass of milk", "the one constant")]),
 # ---- supplements + vitamin D
 ("A", "09:18", "kind of my dietitian", "wd", ("CHATGPT WAS MY DIETITIAN", "before Ironman")),
 ("A", "09:44", "supplement from costco", "pip", ("warehouse-store", "the Costco multi")),
 ("A", "10:34", "vitamin d deficient", "wd", ("VITAMIN D", "deficient?")),
 ("A", "11:18", "just chewable", "pip", ("vitamin-gummies", "a chewable is fine")),
 ("A", "11:39", "it's a stored vitamin", "wd", ("A STORED VITAMIN", "so weekly doses work too")),
 ("A", "11:55", "maximum amount you should take", "wd", ("MAX 4,000 IU", "per day")),
 # ---- salt + cramps
 ("A", "12:57", "salt on my eyes", "pip", ("sweat-drops", "salt on my face")),
 ("A", "13:56", "one location where it does", "pip", ("calf-anatomy", "always the calves")),
 ("A", "14:33", "looking for the medic", "pip", ("race-medic", "medics on standby")),
 ("A", "14:38", "if i fall just take me out", "wd", ("IF I FALL, TAKE ME OUT", "I'm not going to quit")),
 ("A", "14:48", "i pushed through the pain", "wd", ("PUSHED THROUGH THE PAIN", "")),
 ("A", "15:03", "pain relief spray", "st", [("Adhesive bandage", "pain-relief spray")]),
 ("A", "15:44", "hamstring because of the biking", "pip", ("hamstring", "hamstrings on the bike")),
 ("A", "16:20", "sodium or electrolyte drinks", "pip", ("electrolyte-powder", "sodium drinks")),
 ("A", "17:37", "nothing to do with the cramping", "wd", ("CARBS WON'T FIX CRAMPS", "")),
 ("A", "17:52", "do the wall balls", "pip", ("wall-ball", "wall balls")),
 ("A", "17:56", "sprinting my last couple", "pip", ("finish-line", "sprint finish")),
 # ---- sweat test
 ("A", "18:21", "arrive at the starting line", "wd", ("START HYDRATED", "the day before counts")),
 ("A", "19:41", "six minutes of run", "st", [("Stopwatch", "6 min run + 4 min station")]),
 ("A", "19:54", "a wait before", "pip", ("digital-scale", "weigh before + after")),
 ("A", "21:57", "so it's water and sodium", "wd", ("WATER + SODIUM", "")),
 ("A", "22:25", "water coke and red", "pip", ("energy-drink-cans", "aid-station drinks")),
 ("A", "23:24", "do your sodium capsules", "st", [("Pill", "sodium capsules")]),
 # ---- sodium, caffeine, gels
 ("A", "24:36", "muscle adaptation", "wd", ("MUSCLE ADAPTATION", "the cramps come later now")),
 ("A", "25:46", "really salty sweater", "wd", ("SALTY SWEATER", "")),
 ("A", "26:34", "basically a stimulant", "wd", ("STIMULANT", "it lowers perceived effort")),
 ("A", "27:52", "the last one i took twice the time", "wd", ("LAST 1K: 2X SLOWER", "because I cramped")),
 # ---- muscle without slowing down
 ("A", "29:18", "put on weight a little easily", "wd", ("70-80 KG", "my weight swings fast")),
 ("A", "29:41", "my strength is shrinking", "wd", ("MY STRENGTH IS SHRINKING", "")),
 ("A", "29:48", "get strength and get faster", "st", [("Rocket", "stronger + faster")]),
 ("A", "30:01", "the training is the first part", "wd", ("TRAINING FIRST", "then eat enough")),
 ("A", "30:17", "that you become slower", "st", [("Snail", "too heavy = slower")]),
 ("A", "30:43", "go to the gym right away", "pip", ("empty-gym", "6 am gym")),
 ("A", "31:21", "you don't need volume", "wd", ("LESS VOLUME", "more time for the gym")),
 ("A", "32:14", "when i hit the lunges", "pip", ("lunges", "lunges = cramps")),
 # ---- training fasted
 ("A", "33:16", "every set change", "st", [("Droplet", "sip every set")]),
 ("A", "35:08", "peanut butter sandwich", "pip", ("peanut-butter", "PB sandwich")),
 ("A", "35:31", "bring your blood sugar level up", "wd", ("BLOOD SUGAR UP", "that's the whole job")),
 # ---- 30-minute window
 ("A", "36:52", "take shower change", "st", [("Shower", "shower + go")]),
 ("A", "37:01", "i just bike or walk", "pip", ("cyclist-commute", "bike to work")),
 ("A", "38:03", "this milkshake", "pip", ("milkshake", "shake on the go")),
 ("A", "38:30", "isn't it 30 minutes", "wd", ("30 MINUTES?", "the anabolic window")),
 ("A", "38:52", "do it within 30 minutes", "wd", ("2 WORKOUTS = 30 MIN", "1 workout = 2 hours")),
 # ---- B: creatine
 ("B", "01:33", "ever taken creatine", "pip", ("supplement-powder", "creatine")),
 ("B", "02:00", "there will be a plateau", "wd", ("PLATEAU?", "")),
 ("B", "03:16", "just a placebo", "wd", ("PLACEBO?", "1 week is too soon to tell")),
 ("B", "03:33", "just taking the one little scoop", "st", [("Spoon", "5-7 g scoop")]),
 # ---- 50 g protein
 ("B", "04:47", "not just about protein intake", "wd", ("NOT JUST PROTEIN", "muscle needs more than that")),
 ("B", "05:14", "greek yogurt with the granola", "pip", ("plain-yogurt", "the go-to breakfast")),
 ("B", "05:49", "divided by four", "st", [("Bowl with spoon", "~150 g a day")]),
 ("B", "06:24", "banana and dates", "pip", ("dates-fruit", "banana + dates")),
 ("B", "08:00", "add some eggs", "pip", ("veg-omelette", "veg + 3-4 eggs")),
 ("B", "08:16", "no fibers at all", "wd", ("NO FIBRE AT ALL", "")),
 ("B", "09:11", "won't need quite as much rice", "st", [("Cooked rice", "a bit less rice")]),
 ("B", "10:51", "put a cup of veggies in there", "wd", ("1 CUP OF VEGGIES", "raw or cooked")),
 # ---- 5-hour gap
 ("B", "12:37", "every three to five hours", "wd", ("EAT EVERY 3-5 HOURS", "")),
 ("B", "12:52", "muscle energy stores", "st", [("Battery", "muscle energy stores")]),
 ("B", "14:40", "three pieces of fruit", "pip", ("office-fruit", "2-3 pieces of fruit")),
 ("B", "16:40", "bike to mount royal", "pip", ("mount-royal", "35 min bike, each way")),
 ("B", "17:51", "overall energy expenditure", "wd", ("ENERGY OUT", "bike + run + gym")),
 # ---- forgot carbs
 ("B", "19:11", "forgot about calves", "wd", ("I FORGOT ABOUT CARBS", "loaded up on protein")),
 ("B", "19:35", "20 grams of protein", "st", [("Chocolate bar", "20 g protein bar")]),
 ("B", "21:00", "gym in our office", "pip", ("empty-gym", "office gym")),
 ("B", "23:37", "just priming yourself", "wd", ("PRIME YOURSELF", "before a hard session")),
 ("B", "23:55", "if it's a gel", "st", [("Battery", "a gel won't upset you")]),
 # ---- no-cook dinners
 ("B", "25:01", "chicken tomatoes onions", "st", [("Tomato", "tomatoes"), ("Onion", "onions")]),
 ("B", "26:10", "basically eaten cold", "st", [("Ice", "eaten cold")]),
 ("B", "26:47", "no energy to make anything", "wd", ("NO ENERGY TO COOK", "")),
 ("B", "26:56", "meal prep on a weekend", "pip", ("lunch-boxes", "weekend meal prep")),
 ("B", "30:46", "can just can tuna", "pip", ("canned-tuna", "canned tuna")),
 ("B", "34:12", "more than just that protein shake", "wd", ("MORE THAN A SHAKE", "")),
 ("B", "34:41", "some actual real", "wd", ("REAL FOOD", "over shakes")),
 ("B", "35:34", "even cottage cheese", "st", [("Cheese wedge", "cottage cheese")]),
 ("B", "35:38", "some frozen fruit", "pip", ("frozen-berries", "frozen fruit")),
 ("B", "36:57", "do you like rx bars", "pip", ("date-bar", "dates, egg whites, nuts")),
 ("B", "38:15", "say two sandwiches", "st", [("Sandwich", "x2")]),
 # ---- muscle before race day
 ("B", "39:52", "quick and easy meal ideas", "st", [("Memo", "quick meal ideas")]),
 ("B", "40:06", "into your workouts versus the kitchen", "wd", ("WORKOUTS > KITCHEN", "")),
 ("B", "41:12", "and really i'm thinking is the issue", "wd", ("THE FIX: YOUR EVENINGS", "")),
 ("B", "42:10", "anyone can gain muscle mass", "wd", ("ANYONE CAN GAIN MUSCLE", "")),
 ("B", "42:30", "your body composition", "pip", ("dexa", "body composition")),
 ("B", "43:14", "always eat at night", "st", [("Crescent moon", "skipping dinner")]),
 # ---- meal prep
 ("B", "44:28", "two hours or three", "st", [("Stopwatch", "2-3 h on a weekend")]),
 ("B", "45:08", "put them in the toaster", "pip", ("toaster", "toast them")),
 ("B", "46:51", "no energy to actually push", "wd", ("NO ENERGY TO PUSH", "")),
 # ---- real food vs pills
 ("B", "47:12", "vitamin d b12", "st", [("Pill", "D + B12")]),
 ("B", "47:50", "the orange colors", "pip", ("sweet-potato", "orange = vitamin A")),
 ("B", "48:16", "making a salad", "pip", ("chicken-salad", "chicken salad")),
 ("B", "49:07", "things called", "wd", ("PHYTOCHEMICALS", "you can't get that in a bottle")),
 ("B", "49:38", "plant based foods", "pip", ("veg-market", "more plants")),
 ("B", "50:27", "main focus being your evening", "wd", ("FOCUS: EVENING EATING", "check in a month")),
 ("B", "50:44", "can even be virtual", "st", [("Laptop", "virtual check-in")]),
 ("A", "01:19", "up around 637", "pip", ("alarm-clock", "6:37 am wake-up")),
 ("A", "27:33", "interval type work", "pip", ("running-track", "interval work")),
 ("B", "00:22", "my blood reports yesterday", "pip", ("blood-test", "blood work: all good")),
 ("B", "07:50", "mixed veggies", "pip", ("mixed-veg", "broccoli, corn, carrots")),
 ("B", "09:20", "carb needs are maybe going to go down", "pip", ("pasta-carbs", "carb needs drop a bit")),
 ("B", "35:05", "would you make your own smoothie", "pip", ("blender-smoothie", "homemade smoothie")),
 ("B", "16:20", "to get to the second workout", "pip", ("bike-hill", "bike to workout #2")),
 # ---- gap fillers (v3b)
 ("A", "03:50", "200 to 300 grams of rice", "wd", ("200-300 G OF RICE", "+ ~150 g chicken")),
 ("A", "04:19", "very tiny rice", "st", [("Cooked rice", "portion check")]),
 ("A", "16:32", "in my ironman i did use it", "pip", ("bike-hill", "Ironman: used sodium")),
 ("A", "16:45", "the hyrox i didn't use sodium", "wd", ("HYROX: NO SODIUM", "just 1-2 gels")),
 ("A", "20:16", "is there a scale there", "st", [("Balance scale", "bring a scale")]),
 ("A", "20:28", "you want to be the same", "wd", ("SAME CLOTHES, BEFORE + AFTER", "or none at all")),
 ("A", "20:43", "clothing is going to absorb", "st", [("T-shirt", "clothes soak up sweat")]),
 ("A", "21:46", "allowed to be a little bit of dehydrated", "wd", ("A LITTLE DEHYDRATED IS OK", "after a workout")),
 ("A", "26:55", "out there for hours", "st", [("Person biking", "hours out there")]),
 ("A", "27:02", "upset your gut", "st", [("Nauseated face", "upset gut")]),
 ("A", "28:05", "should have taken little bit more", "wd", ("MORE CARBS ON RACE DAY", "")),
 ("A", "28:17", "just even your day", "wd", ("DAILY FUELING FIRST", "race fueling later")),
 ("A", "31:04", "do my strength in the morning", "st", [("Sunrise", "AM strength")]),
 ("A", "31:48", "start practice like training with that", "pip", ("sports-drink", "practise with it in training")),
 ("A", "33:37", "mine are a liter", "pip", ("office-bottle", "1 L per session")),
 ("A", "33:55", "you're a heavy sweater", "wd", ("HEAVY SWEATER", "drink between every set")),
 ("A", "36:05", "just a starting point", "wd", ("JUST A STARTING POINT", "we'll tinker with it")),
 ("A", "36:28", "rush to work", "st", [("Office building", "rush to work")]),
 ("A", "37:10", "35 to 40 minutes of window", "wd", ("35-40 MIN GAP", "gym to first meal")),
 ("B", "02:30", "push a little bit further", "st", [("Flexed biceps", "push further")]),
 ("B", "02:40", "don't even respond to creatine", "wd", ("NON-RESPONDERS", "creatine doesn't work for everyone")),
 ("B", "05:03", "within this two hour timeframe", "wd", ("NEXT MEAL WITHIN 2 H", "the second breakfast")),
 ("B", "05:32", "is it plain", "st", [("Bowl with spoon", "plain, ~150 g")]),
 ("B", "07:20", "decrease your rice a little", "wd", ("MORE VEG, A BIT LESS RICE", "")),
 ("B", "09:33", "your training in the gym uses carbs", "wd", ("GYM USES LESS CARB PER MINUTE", "than running or cycling")),
 ("B", "13:02", "till my training", "st", [("Hourglass not done", "1 pm to 6 pm")]),
 ("B", "13:43", "i heard the question wrong", "st", [("Thinking face", "say that again?")]),
 ("B", "13:59", "always going to include some form of activity", "wd", ("ACTIVE EVERY EVENING", "so fuel the afternoon")),
 ("B", "15:25", "a run or a bike", "st", [("Person running", "run or bike?")]),
 ("B", "16:59", "30 minutes to come back", "wd", ("+30 MIN EACH WAY", "on the bike")),
 ("B", "17:16", "getting a little concerned", "wd", ("THE PROBLEM: DINNER", "")),
 ("B", "18:13", "when life happens", "wd", ("LIFE HAPPENS", "")),
 ("B", "19:47", "not bad for carbs", "st", [("Bread", "decent carbs")]),
 ("B", "21:14", "come back home and workout", "st", [("House", "plan B: home")]),
 ("B", "22:10", "later part of the day", "wd", ("FIX THE LATE AFTERNOON", "")),
 ("B", "22:37", "add more ideas later", "st", [("Light bulb", "more ideas later")]),
 ("B", "22:59", "you did the gym in the morning", "st", [("Sunrise", "gym in the morning")]),
 ("B", "24:03", "just an easy swim", "st", [("Goggles", "easy swim: skip it")]),
 ("B", "24:21", "and you bike home", "st", [("Bicycle", "bike home")]),
 ("B", "24:45", "so i'll say balanced meal", "wd", ("BALANCED MEAL", "chicken + roti + veg")),
 ("B", "25:42", "made it the night before", "st", [("Crescent moon", "make it the night before")]),
 ("B", "25:48", "you sound too busy", "wd", ("TOO BUSY TO COOK?", "")),
 ("B", "26:22", "my friends do that", "st", [("Busts in silhouette", "my friends do it")]),
 ("B", "26:37", "one of your breakfasts", "st", [("Sunrise", "or at breakfast")]),
 ("B", "27:31", "talking to people", "st", [("Speech balloon", "eat while you chat")]),
 ("B", "28:37", "tolerate a bit more food", "wd", ("LIFTING IS EASIER ON THE GUT", "")),
 ("B", "29:01", "start to fade", "st", [("Low battery", "energy fades")]),
 ("B", "29:22", "eating while they're at the gym", "st", [("Sandwich", "eating at the gym")]),
 ("B", "31:45", "some roti with something", "st", [("Flatbread", "eggs + roti")]),
 ("B", "32:20", "i like those alani shakes", "st", [("Cup with straw", "Alani shake")]),
 ("B", "32:34", "protein shake with the tuna", "wd", ("TUNA SANDWICH + SHAKE?", "")),
 ("B", "32:56", "don't like the combination", "st", [("Thinking face", "not a fan")]),
 ("B", "33:28", "did your cardio", "wd", ("CARDIO, SANDWICH, GYM", "")),
 ("B", "33:57", "not trying to complicate things", "st", [("Thumbs up", "keep it simple")]),
 ("B", "34:51", "it's quick and it's easy", "wd", ("QUICK + EASY", "the one upside of shakes")),
 ("B", "36:44", "can't be dairy based", "wd", ("NO DAIRY", "not with fish, for him")),
 ("B", "37:29", "they sound really weird", "wd", ("THEY SOUND WEIRD", "but they're good")),
 ("B", "37:40", "still a convenience food", "st", [("Convenience store", "convenience food")]),
 ("B", "38:24", "post workout meal or during", "st", [("Fork and knife with plate", "post-workout meal")]),
 ("B", "39:04", "how much energy you were", "st", [("Fire", "energy out")]),
 ("B", "39:18", "didn't completely change your eating", "wd", ("I DIDN'T CHANGE MUCH", "just the evenings")),
 ("B", "39:43", "more harder than making dinner", "st", [("Face with tears of joy", "harder than dinner!")]),
 ("B", "45:52", "carbs more protein altogether", "wd", ("DINNER = CARBS + PROTEIN", "+ some colour")),
 ("B", "48:43", "whichever is easier", "st", [("Pill", "or the easy way")]),
 ("B", "48:55", "not eating veggies", "wd", ("NO VEGGIES? TAKE THE MULTI", "")),
 ("B", "50:17", "going to print this", "st", [("Printer", "printing the plan")]),
 ("B", "50:42", "still struggling with that nighttime", "st", [("Crescent moon", "still struggling at night?")]),
]

# auto 3D emoji on spoken keywords (gap filler): tokens -> (emoji, label), each used at most `n` times, 2+ min apart
KEYS = {
 ("banana",): ("Banana", "banana"), ("apple",): ("Red apple", "apple"), ("eggs",): ("Egg", "eggs"),
 ("chicken",): ("Poultry leg", "chicken"), ("rice",): ("Cooked rice", "rice"), ("veggies",): ("Broccoli", "veggies"),
 ("water",): ("Droplet", "water"), ("sweat",): ("Sweat droplets", "sweat"), ("salt",): ("Salt", "salt"),
 ("sodium",): ("Salt", "sodium"), ("cramp",): ("Collision", "cramp"), ("cramping",): ("Collision", "cramping"),
 ("cramps",): ("Collision", "cramps"), ("gel",): ("Battery", "gel"), ("gels",): ("Battery", "gels"),
 ("caffeine",): ("Hot beverage", "caffeine"), ("carbs",): ("Bread", "carbs"), ("protein",): ("Cut of meat", "protein"),
 ("muscle",): ("Flexed biceps", "muscle"), ("gym",): ("Person lifting weights", "gym"),
 ("running",): ("Running shoe", "running"), ("run",): ("Running shoe", "run"), ("bike",): ("Bicycle", "bike"),
 ("biking",): ("Bicycle", "biking"), ("swim",): ("Goggles", "swim"), ("sleep",): ("Zzz", "sleep"),
 ("sleeping",): ("Zzz", "sleep"), ("morning",): ("Sunrise", "morning"), ("night",): ("Crescent moon", "night"),
 ("dinner",): ("Fork and knife with plate", "dinner"), ("lunch",): ("Fork and knife with plate", "lunch"),
 ("breakfast",): ("Pancakes", "breakfast"), ("fruit",): ("Grapes", "fruit"), ("smoothie",): ("Cup with straw", "smoothie"),
 ("shake",): ("Cup with straw", "shake"), ("milkshake",): ("Glass of milk", "milkshake"), ("yogurt",): ("Bowl with spoon", "yogurt"),
 ("granola",): ("Bowl with spoon", "granola"), ("sandwich",): ("Sandwich", "sandwich"), ("tuna",): ("Fish", "tuna"),
 ("salad",): ("Green salad", "salad"), ("spinach",): ("Leafy green", "spinach"), ("carrots",): ("Carrot", "carrots"),
 ("carrot",): ("Carrot", "carrot"), ("oats",): ("Bowl with spoon", "oats"), ("bus",): ("Bus", "bus"),
 ("vitamin",): ("Pill", "vitamin"), ("supplement",): ("Pill", "supplement"), ("creatine",): ("Test tube", "creatine"),
 ("strength",): ("Flexed biceps", "strength"), ("energy",): ("High voltage", "energy"), ("recovery",): ("Battery", "recovery"),
 ("recover",): ("Battery", "recover"), ("hydration",): ("Droplet", "hydration"), ("electrolyte",): ("Salt", "electrolytes"),
 ("electrolytes",): ("Salt", "electrolytes"), ("ironman",): ("Person biking", "Ironman"), ("calories",): ("Fire", "calories"),
 ("winter",): ("Snowflake", "winter"), ("fridge",): ("Ice", "fridge"), ("bread",): ("Bread", "bread"),
 ("pancakes",): ("Pancakes", "pancakes"), ("kitchen",): ("Cooking", "kitchen"), ("cooking",): ("Cooking", "cooking"),
 ("cook",): ("Cooking", "cook"), ("recipes",): ("Spiral notepad", "recipes"), ("blood",): ("Drop of blood", "blood"),
 ("fat",): ("Peanuts", "fat"), ("walnuts",): ("Chestnut", "walnuts"), ("honey",): ("Honey pot", "honey"),
 ("intervals",): ("Stopwatch", "intervals"), ("race",): ("Chequered flag", "race"), ("bone",): ("Bone", "bones"),
}
KEY_MAX, KEY_SPACING = 7, 70.0

PAD = 0.7  # seconds of air around every device


def emo(emoji, label):
    fid = "e_" + "".join(ch if ch.isalnum() else "-" for ch in (emoji + "_" + label).lower()).strip("-")[:48]
    FX[fid] = {"id": fid, "kind": "emoji", "emoji": emoji, "label": label, "size": 330, "dur": 2.9 if label else 2.4}
    return fid


def photo(slug, label):
    fid = "p_" + slug + ("-" + "".join(ch if ch.isalnum() else "-" for ch in label.lower())[:20] if label else "")
    FX[fid] = {"id": fid, "kind": "photo", "file": f"projects/carrie-ep01/broll/{slug}.jpg", "label": label, "w": 480,
               "dur": 3.8, "tilt": -2.5 if len(FX) % 2 else 2.0}
    return fid


def word(text, kicker):
    fid = "w_" + "".join(ch if ch.isalnum() else "-" for ch in text.lower())[:40]
    FX[fid] = {"id": fid, "kind": "word", "text": text, "kicker": kicker, "size": 96 if len(text) > 16 else 112, "dur": 2.8}
    return fid


def has_photo(slug):
    return os.path.exists(os.path.join(EP, "broll", slug + ".jpg"))


def locate(ev):
    try:
        return L2.find(ev[0], ev[1], ev[2])
    except SystemExit as e:
        print("  skip (phrase):", e)
        return None


def collect():
    """every candidate device on the source timelines: (file, start, end, kind, payload, priority)"""
    cands = []
    for ev in L2.EV + NEW:
        f, kind = ev[0], ev[3]
        loc = locate(ev)
        if not loc:
            continue
        i, n = loc
        t = WS[f][i][0]
        if kind == "br":
            if not has_photo(ev[4]):
                continue
            s, e = L2.span(f, i, max(float(ev[5]), 4.2)); cands.append((f, s, e, "br", ev[4], 2))  # long enough to register
        elif kind == "card":
            s, e = L2.span(f, i, ev[5]); cands.append((f, s, e, "card", ev[4], 1))
        elif kind == "sbs":
            s, e = L2.span(f, i, ev[5]); cands.append((f, s, e, "sbs", None, 3))
        elif kind == "pip":
            if not has_photo(ev[4][0]):
                continue
            s, e = L2.span(f, i, 3.6); cands.append((f, s, max(e, s + 3.0), "pip", photo(*ev[4]), 4))
        elif kind == "wd":
            cands.append((f, t, t + 2.8, "wd", word(*ev[4]), 5))
        elif kind == "st":
            ids = [emo(e_, l_) for e_, l_ in ev[4]]
            cands.append((f, t, t + 2.9 + 0.25 * (len(ids) - 1), "st", ids, 6))
    # auto keywords
    used = {}
    for f, ws in WS.items():
        for i, w in enumerate(ws):
            for k, (e_, l_) in KEYS.items():
                if tuple(x[2] for x in ws[i:i + len(k)]) != k:
                    continue
                last = used.setdefault((e_, l_), [])
                if len(last) >= KEY_MAX or any(lf == f and abs(lt - w[0]) < KEY_SPACING for lf, lt in last):
                    continue
                last.append((f, w[0]))
                cands.append((f, w[0], w[0] + 2.4, "st", [emo(e_, l_)], 7))
    # auto split screens on quick back-and-forths: >= 3 turns inside 4-11 s, both talk >= 1.2 s
    for f, ws in WS.items():
        turns = [i for i in range(1, len(ws)) if ws[i][3] in "LR" and ws[i - 1][3] in "LR" and ws[i][3] != ws[i - 1][3]]
        last = -99
        for a in range(len(turns)):
            i0 = turns[a] - 1
            while i0 > 0 and ws[i0 - 1][3] == ws[i0][3] and ws[turns[a] - 1][1] - ws[i0 - 1][0] < 2.5:
                i0 -= 1
            s = ws[i0][0]
            if s - last < 22:
                continue
            for b in range(a + 2, len(turns)):
                e = ws[turns[b] - 1][1]
                if e - s > 11:
                    break
                if e - s >= 4:
                    talk = {"L": 0.0, "R": 0.0}
                    for w in ws:
                        if s <= w[0] < e and w[3] in talk:
                            talk[w[3]] += w[1] - w[0]
                    if min(talk.values()) >= 1.2:
                        cands.append((f, round(s - 0.05, 3), round(e + 0.1, 3), "sbs", None, 8)); last = s
                        break
    return cands


def choose(cands):
    """greedy by priority: layout devices never overlap anything; overlays never overlap each other or a
    layout device (except split screens, which can carry an overlay)"""
    taken, c_ok = [], []  # (f, s, e, kind)
    for c in sorted(cands, key=lambda c: (c[5], c[1])):
        f, s, e, kind = c[0], c[1], c[2], c[3]
        ok = True
        for (tf, ts, te, tk) in taken:
            if tf != f or e + PAD <= ts or s >= te + PAD:
                continue
            if {kind, tk} <= {"sbs", "st", "wd"} and "sbs" in (kind, tk) and kind != tk:
                inner = (kind != "sbs" and ts + 0.3 <= s and e <= te + 1.5) or (tk != "sbs" and s + 0.3 <= ts and te <= e + 1.5)
                if inner:
                    continue
            ok = False; break
        if ok:
            taken.append((f, s, e, kind)); c_ok.append(c)
    return c_ok



def chapter_spec(ci, chosen):
    f, st, title = L.CH[ci]
    nxt = L.CH[ci + 1] if ci + 1 < len(L.CH) else None
    en = B.sec(nxt[1]) if nxt and nxt[0] == f else B.sec(L.END[f])
    st = B.sec(st)
    s0, s1 = B.snap(f, st, st + 3.0)
    segs = [{"clip": B.FILES[f], "start": s0, "end": s1, "chapter": title, "tighten": 0, "nocaps": True,
             "broll": {"file": f"projects/carrie-ep01/cards/T{ci + 1:02d}.mp4", "push": 0}}]
    cur = s1
    mine = sorted([c for c in chosen if c[0] == f and s1 + 0.3 <= c[1] < en - 1.0], key=lambda c: c[1])
    layout = [c for c in mine if c[3] in ("br", "card", "sbs", "pip")]
    overl = [c for c in mine if c[3] in ("st", "wd")] + [c for c in layout if c[3] == "pip"]
    for c in layout:
        s, e = c[1], min(c[2], en - 0.2)
        if s < cur + 0.3 or e - s < 1.5:
            continue
        if s - cur > 0.3:
            segs.append({"clip": B.FILES[f], "start": cur, "end": s})
        seg = {"clip": B.FILES[f], "start": s, "end": e, "tighten": 0}
        if c[3] == "br":
            seg["broll"] = {"file": f"projects/carrie-ep01/broll/{c[4]}.jpg", "push": 0.07}
        elif c[3] == "card":
            who = L2.talker(f, s, e)
            cid = f"L3_{ci + 1:02d}_c{len(CARDS)}"
            CARDS.append({"id": cid, **c[4], "w": 806, "h": 1080, "dur": round(e - s + 0.8, 2)})
            seg.update(cx="right" if who == "R" else "left", zoom=L2.ZC if who == "R" else L2.ZN, cy=0.38,
                       broll={"file": f"projects/carrie-ep01/cards/{cid}.mp4", "panel": "left" if who == "R" else "right", "push": 0})
        elif c[3] == "sbs":
            seg.update(layout="sbs", zoom=1.6, zoom_r=1.4, cy=0.36)
        elif c[3] == "pip":
            seg.update(cx=0.5, zoom=1.0)  # wide two-shot under the floating photo
        segs.append(seg)
        cur = e
    if en - cur > 0.3:
        segs.append({"clip": B.FILES[f], "start": cur, "end": round(en, 3)})
    # output timeline (replicates the engine's tightening) to place overlays exactly
    t, pos = 0.0, []
    for sg in segs:
        g = sg.get("tighten", GAP)
        pieces = P.tighten(sg, B.TX, float(g), True) if g else [sg]
        for p in pieces:
            d = round((p["end"] - p["start"]) * 30) / 30
            kind = "title" if sg.get("chapter") else "br" if (sg.get("broll") and not sg["broll"].get("panel")) else \
                "card" if sg.get("broll") else "sbs" if sg.get("layout") == "sbs" else "pip" if sg.get("cx") == 0.5 else "talk"
            pos.append((sg["clip"], p["start"], p["end"], t, kind))
            t += d
    stickers, sfx = [], []
    for c in sorted(overl, key=lambda c: c[1]):
        ts = c[1] + (0.15 if c[3] == "pip" else 0)
        hit = next((p for p in pos if p[0] == B.FILES[f] and p[1] - 0.05 <= ts < p[2]), None) or \
            next((p for p in pos if p[0] == B.FILES[f] and p[1] >= ts), None)
        if not hit or hit[4] in ("title", "br", "card") or (c[3] != "pip" and hit[4] == "pip"):
            continue
        at = round(hit[3] + max(ts - hit[1], 0), 3)
        if c[3] == "st":
            for k, fid in enumerate(c[4]):
                stickers.append({"at": round(at + 0.25 * k, 3), "file": f"projects/carrie-ep01/fx/{fid}.mov", "x": "auto",
                                 "y": 0.30, "group": f"g{at}", "_fid": fid})
            sfx.append({"at": at, "file": "pop.mp3", "vol": 0.16})
        elif c[3] == "wd":
            stickers.append({"at": at, "file": f"projects/carrie-ep01/fx/{c[4]}.mov", "x": "auto", "y": 0.72,
                             "group": f"w{at}", "_fid": c[4]})
            sfx.append({"at": at, "file": "whoosh_fast.mp3", "vol": 0.2})
        else:  # pip
            stickers.append({"at": at, "file": f"projects/carrie-ep01/fx/{c[4]}.mov", "x": 0.595, "y": 0.37,
                             "group": f"p{at}", "_fid": c[4]})
            sfx.append({"at": at, "file": "whoosh_soft.mp3", "vol": 0.24})
    for k, p in enumerate(pos):  # a soft whoosh into every B-roll / card / split screen
        if p[4] in ("br", "card", "sbs") and (k == 0 or pos[k - 1][4] != p[4]):
            sfx.append({"at": round(p[3], 2), "file": "whoosh_soft.mp3", "vol": 0.2})
    tag_at = pos[1][3] if len(pos) > 1 else 3.0
    spec = {"_piece": True, "id": f"L3_{ci + 1:02d}", "slug": "chapter", "format": "long", "title": f"v3 chapter {ci + 1}",
            "topic": "long-form part", "auto_frame": AF, "tighten": GAP, "captions": "pod", "cap_y": 0.935, "cap_size": 66,
            "fixes": B.FIX, "accent": B.ACCENT, "segments": segs, "stickers": stickers, "sfx": sfx,
            "tags": [{"at": round(tag_at + 0.3, 2), "num": f"{ci + 1:02d}", "text": SHORT[ci]}]}
    if ci == 0:
        spec["names"] = [{"at": 3.5, "dur": 4.0, "name": "Carrie Mullin Innes", "role": B.NAMES["C"][1], "x": 0.55, "y": 0.72},
                         {"at": 8.0, "dur": 4.0, "name": "Nizam", "role": B.NAMES["N"][1], "x": 0.06, "y": 0.72}]
        spec["stickers"] = [s for s in spec["stickers"] if not (2.5 < s["at"] < 13)]  # names own the screen there
    n = lambda k: sum(1 for p in pos if p[4] == k and True)
    return spec, t, {"br": len([s for s in segs if (s.get("broll") or {}).get("file", "").endswith(".jpg")]),
                     "card": len([s for s in segs if (s.get("broll") or {}).get("panel")]),
                     "sbs": len([s for s in segs if s.get("layout") == "sbs"]),
                     "pip": len([s for s in stickers if "/p_" in s["file"]]),
                     "word": len([s for s in stickers if "/w_" in s["file"]]),
                     "emoji": len([s for s in stickers if "/e_" in s["file"]])}


CO_ST = {"salt": ("Salt", "salty sweater"), "kilo": ("Balance scale", "1 kg = 1 L"), "caffeine": ("Hot beverage", "caffeine"),
         "gels": ("Stopwatch", "2 gels / 1:42"), "chatgpt": ("Robot", "ChatGPT"), "shake": ("Cup with straw", "not enough"),
         "carbs": ("Bread", "forgot carbs"), "fruit": ("Red apple", "eat the fruit")}


def cold_open():
    sp = L.cold_open("CO1")
    sp.update(id="L3_00", slug="open", captions="pod", cap_y=0.935, cap_size=66, keywords=[])
    keys, _ = L.OPENS["CO1"]
    t, st, sfx = 0.0, [], []
    for k, sg in zip(keys + ["_title"], sp["segments"]):
        if k in CO_ST:
            fid = emo(*CO_ST[k])
            st.append({"at": round(t + 0.4, 2), "file": f"projects/carrie-ep01/fx/{fid}.mov", "x": "auto", "y": 0.30,
                       "group": f"co{k}", "_fid": fid})
            sfx.append({"at": round(t + 0.4, 2), "file": "pop.mp3", "vol": 0.16})
        g = sg.get("tighten", sp.get("tighten"))
        pieces = P.tighten(sg, B.TX, float(g), True) if g else [sg]
        t += sum(round((p["end"] - p["start"]) * 30) / 30 for p in pieces)
    sp["stickers"] = st
    sp["sfx"] = sp.get("sfx", []) + sfx
    return sp


def widths(specs):
    """element width as a fraction of the frame, measured from the rendered clips (placement keeps it off faces)"""
    for sp in specs:
        sp["stickers"] = [s for s in sp["stickers"] if os.path.exists(os.path.join(ROOT, s["file"]))]
        for s in sp["stickers"]:
            fid = s.pop("_fid")
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width",
                                "-of", "csv=p=0", os.path.join(ROOT, s["file"])], capture_output=True, text=True).stdout.strip()
            w = int(r) if r.isdigit() else 400
            s["w"] = round(w / 1920 * (1.0 if fid.startswith("w_") else 0.85), 3)  # visible part of the clip


if __name__ == "__main__":
    chosen = choose(collect())
    specs, tot, allc = [], 0.0, {}
    for ci in range(len(L.CH)):
        sp, t, cnt = chapter_spec(ci, chosen)
        specs.append(sp); tot += t
        for k, v in cnt.items():
            allc[k] = allc.get(k, 0) + v
        print(f"ch{ci + 1:02d} {t / 60:5.1f} min", cnt)
    co = cold_open(); specs.append(co)
    if "--gaps" in os.environ.get("L3_FLAGS", ""):
        for f, ws in WS.items():
            ts = sorted([c[1] for c in chosen if c[0] == f] + [c[2] for c in chosen if c[0] == f and c[3] in ("br", "card", "sbs", "pip")])
            for a_, b_ in zip(ts, ts[1:]):
                if b_ - a_ > 22:
                    txt = " ".join(w[2] for w in ws if a_ + 3 < w[0] < b_)
                    print(f"GAP {f} {int(a_ // 60):02d}:{a_ % 60:04.1f} +{b_ - a_:.0f}s | {txt[:260]}")
    json.dump({"accent": B.ACCENT, "cards": CARDS}, open(os.path.join(EP, "cards_long3.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    json.dump({"accent": B.ACCENT, "fx": list(FX.values())}, open(os.path.join(EP, "fx.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    if not NO_RENDER:
        subprocess.run([PY, os.path.join(ROOT, "scripts", "fx.py"), os.path.join(EP, "fx.json"), "--out", os.path.join(EP, "fx"), "-j", "6"], check=True)
        subprocess.run([PY, os.path.join(ROOT, "scripts", "cards.py"), os.path.join(EP, "cards_long3.json"), "--out", os.path.join(EP, "cards")], check=True)
        widths(specs)
        for sp in specs:
            json.dump(sp, open(os.path.join(OUT, sp["id"] + ".json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"total {tot / 60:.1f} min + cold open;", allc, f"{len(FX)} fx clips, {len(CARDS)} cards")
    ev = sum(allc.values())
    print(f"~{ev / (tot / 60):.1f} devices per minute (one every {tot / max(ev, 1):.0f} s)")
