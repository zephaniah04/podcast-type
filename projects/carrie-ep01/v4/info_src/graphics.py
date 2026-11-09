"""FUEL LAB explainer graphics for Carrie ep01 v4: one dict per graphic.
(f, at, phrase) is the spoken anchor (validated with build_long2.find); data feeds engine.js renderers.
Numbers are Carrie's (or Nizam's own) unless the card is a research note, which names its source."""

G = []


def g(batch, id, f, at, phrase, mode, dur, kind, bg, tag, data, prio=2, variant_kind=None):
    G.append(dict(batch=batch, id=id, f=f, at_hint=at, phrase=phrase, mode=mode, dur=dur, kind=kind, bg=bg, tag=tag,
                  data=data, prio=prio))


SRC_ACSM_FLUID = "ACSM position stand: Exercise and Fluid Replacement (Sawka et al., Med Sci Sports Exerc, 2007)"

# =========================================================================================== batch 1 (the 10 key facts)
g(1, "i_sweat_1kg", "A", "20:57", "so if you went in at 74 kilos", "full", 6.0, "counter", "paper", "THE SWEAT TEST",
  {"variant": "scale", "l1": "−1 KG", "l2": "= 1 L", "sub": "74 in, 73 out: a [litre of sweat] not replaced."}, 1)
g(1, "i_vitd_max", "A", "11:55", "maximum amount you should take in a day", "full", 5.5, "counter", "ink", "VITAMIN D",
  {"kicker": "THE DAILY CEILING", "num": "4,000", "unit": "IU", "line2": "MAX IN A DAY",
   "sub": "Her plan: *1,000 IU a day*, or 3,000 IU twice a week.", "icon": "sun"}, 1)
g(1, "i_window_myth", "A", "38:30", "isn't it 30 minutes", "full", 6.5, "myth", "ink", "THE 30-MIN WINDOW",
  {"myth": "You must eat within *30 minutes* of training", "fact": "It happens over the first [2 hours]",
   "sub": "Training again later that day? *Then* refuel within 30 minutes."}, 1)
g(1, "i_gap_5h", "B", "14:24", "if you're eating that at one", "full", 6.5, "timeline", "paper", "THE 5-HOUR GAP",
  {"title": "1 PM TO 6 PM: THE *gap*",
   "events": [{"t": "7:30 AM", "title": "SHAKE", "icon": "shake"}, {"t": "~10:30", "title": "YOGURT + GRANOLA", "icon": "yogurt"},
              {"t": "1 PM", "title": "LUNCH", "icon": "rice"}, {"t": "6 PM", "title": "TRAINING", "icon": "run"},
              {"t": "AFTER", "title": "DINNER?", "icon": "fork"}],
   "gap": {"a": 2, "b": 3, "label": "5 HOURS", "note": "so he needs something: the afternoon fruit goes *here*"}}, 1)
g(1, "i_protein_meals", "B", "04:36", "that's plenty of protein", "full", 6.5, "bars", "paper", "THE SCIENCE · PROTEIN",
  {"title": "UP TO [~150 G] A DAY, *spread out*",
   "bars": [{"label": "MEAL 1", "v": 37, "disp": "~37 G"}, {"label": "MEAL 2", "v": 37, "disp": "~37 G"},
            {"label": "MEAL 3", "v": 37, "disp": "~37 G"}, {"label": "MEAL 4", "v": 37, "disp": "~37 G", "hl": True}],
   "max": 40, "side": {"t": "HIS SHAKE: 45-50 G. *Plenty*, says Carrie.",
                       "d": "Research: 1.4-2.0 g/kg a day, ~20-40 g per meal.", "at": 2.0},
   "illus": "SOURCE: ISSN position stand: protein and exercise (Jäger et al., JISSN, 2017). Ranges applied to 74 kg; 4 meals is an example split."}, 1)
g(1, "i_race_plan", "A", "16:57", "so i had just two gels", "full", 7.0, "timeline", "ink", "RACE-DAY FUEL",
  {"variant": "race", "title": "HIS HYROX: 1:42, TWO GELS, *no* SODIUM", "max": 102,
   "ticks": [0, 20, 40, 60, 80, 100], "tickLabels": ["0:00", "0:20", "0:40", "1:00", "1:20", "1:40"],
   "events": [{"m": 0, "title": "START", "align": "l", "w": 200, "icon": "run"},
              {"m": 40, "title": "GEL 1", "note": "40 min, after the row", "icon": "gel", "w": 320},
              {"m": 77, "title": "GEL 2", "note": "~1:15-1:20, before the run to lunges", "icon": "gel", "w": 320},
              {"m": 88, "title": "CRAMPS", "note": "at the lunges + last km", "icon": "bolt", "hot": True, "hgt": 270, "w": 330},
              {"m": 102, "title": "FINISH", "note": "1:42", "align": "r", "w": 220}],
   "cups": [12, 24, 36, 48, 60, 72, 84, 96], "cupLabel": "Water: one cup per km, roughly every 12 min",
   "chipsTitle": "CARRIE'S UPGRADES", "chips": ["electrolyte drink, not water", "sodium capsules with each gel", "a little more carbs"]}, 1)
g(1, "i_cramp_map", "A", "15:44", "hamstring because of the biking", "full", 6.5, "bodymap", "paper", "THE CRAMPS",
  {"title": "WHERE IT *locks up*", "fx": 760,
   "spots": [{"part": "calves", "label": "CALVES", "note": "HYROX sandbag lunges, then the last km", "mono": "ALSO 70.3: KM 18-19", "side": "l", "ly": 380, "at": 1.0},
             {"part": "hamstrings", "label": "HAMSTRINGS", "note": "Half Ironman 70.3, *because of the biking*", "side": "r", "ly": 150, "at": 1.8}]}, 1)
g(1, "i_carbs_type", "B", "09:33", "your training in the gym uses carbs", "panel", 5.5, "bars", "paper", "CARB NEEDS",
  {"title": "THE GYM BURNS *fewer* CARBS PER MINUTE",
   "bars": [{"label": "GYM", "v": 1, "disp": "LESS", "hl": True}, {"label": "RUN", "v": 2.2}, {"label": "BIKE", "v": 2.2}, {"label": "SWIM", "v": 2.2}],
   "max": 2.4, "illus": "RELATIVE, MINUTE FOR MINUTE · NOT MEASURED VALUES"}, 1)
g(1, "i_eat_3to5", "B", "12:37", "need to eat every three to five hours", "full", 6.0, "clock", "green", "MEAL TIMING",
  {"title": "EAT EVERY *3-5* HOURS", "max": 6, "ticks": 24, "majorEvery": 4,
   "nums": [{"v": 0, "l": "0"}, {"v": 1, "l": "1H"}, {"v": 2, "l": "2H"}, {"v": 3, "l": "3H"}, {"v": 4, "l": "4H"}, {"v": 5, "l": "5H"}],
   "arcs": [{"from": 3, "to": 5, "col": "a", "t": 1.0}, {"from": 5, "to": 6, "col": "a2", "w": 18, "op": 0.9, "t": 1.7, "d": 0.4}],
   "hand": 4, "handAt": 1.0, "handDur": 1.4, "center": "THE *window*", "centerAt": 2.0, "centerUp": True,
   "keys": [{"t": "3-5 H", "d": "between meals or snacks", "col": "a", "at": 1.2},
            {"t": "LONGER?", "d": "you're not topping up your [muscle energy stores]", "col": "a2", "at": 2.0}]}, 1)
g(1, "i_nocook_list", "B", "43:29", "kind of no cook", "full", 7.0, "list", "paper", "TOO TIRED TO COOK?",
  {"title": "QUICK DINNERS, *no real cooking*", "cols": 2,
   "items": [{"t": "Overnight oats", "d": "made the night before, eaten cold", "icon": "jar"},
             {"t": "Two tuna sandwiches", "d": "protein + carbs, no stove", "icon": "sandwich"},
             {"t": "Hard-boiled eggs + roti", "d": "a week in the fridge, in the shell", "icon": "egg"},
             {"t": "Homemade smoothie", "d": "Greek yogurt or cottage cheese + frozen fruit", "icon": "shake"},
             {"t": "Weekend pancakes", "d": "batch-made, reheated in the toaster", "icon": "toaster"},
             {"t": "Hash browns + eggs", "d": "from the freezer, one pan", "icon": "pan"}]}, 1)

# =========================================================================================== batch 2 (research notes)
g(2, "r_vitd", "A", "12:09", "help with your bone strength", "panel", 5.5, "research", "green", "THE SCIENCE",
  {"ref": "R-01", "icon": "sun", "stat": {"num": "4,000", "unit": "IU", "cap": "UPPER LIMIT PER DAY, ADULTS"},
   "claim": "Vitamin D helps you [absorb calcium], the raw material for strong bones.",
   "points": ["Most adults are advised 600 IU a day (800 IU over 70)."],
   "source": "NIH Office of Dietary Supplements, Vitamin D fact sheet · IOM Dietary Reference Intakes, 2011"}, 2)
g(2, "r_prehydrate", "A", "18:21", "arrive at the starting line well hydrated", "full", 6.0, "research", "green", "THE SCIENCE",
  {"ref": "R-02", "icon": "drop", "stat": {"num": "5-7", "unit": "ML/KG", "cap": "AT LEAST 4 H BEFORE EXERCISE"},
   "claim": "Start hydrated: drink about [5-7 ml per kg] of body weight at least 4 hours before.",
   "points": ["At 74 kg that's roughly 370-520 ml.", "Same idea as Carrie's question: did you drink well the day before?"],
   "source": SRC_ACSM_FLUID}, 2)
g(2, "r_sweat", "A", "21:46", "allowed to be a little bit of dehydrated", "full", 6.0, "research", "green", "THE SCIENCE",
  {"ref": "R-03", "icon": "scale", "stat": {"num": "1.5", "unit": "L", "cap": "TO DRINK PER KG LOST"},
   "claim": "Replace about [1.5 L for every 1 kg] lost in training.",
   "points": ["Carrie's 1.2-1.5 L per kilo sits right in that range.", "Keep losses under ~2% of body weight: about 1.5 kg at 74 kg."],
   "source": SRC_ACSM_FLUID}, 1)
g(2, "r_cramp", "A", "16:00", "is it more of a muscular thing", "panel", 6.0, "research", "green", "THE DEBATE",
  {"ref": "R-04", "label": "THE DEBATE", "icon": "bolt",
   "claim": "Why muscles cramp: [two competing theories]",
   "points": ["1 · Dehydration and electrolyte (sodium) loss.", "2 · Neuromuscular fatigue: tired muscles misfire.",
              "Reviews lean to fatigue, so Carrie's call stands: still optimise fluids + sodium."],
   "source": "Schwellnus MP, Br J Sports Med, 2009: cause of exercise-associated muscle cramps"}, 2)
g(2, "r_sodium", "A", "25:46", "really salty sweater", "full", 6.0, "research", "green", "THE SCIENCE",
  {"ref": "R-05", "icon": "salt", "stat": {"num": "~35", "unit": "MMOL/L", "cap": "AVERAGE SWEAT SODIUM · RANGE ~10-70"},
   "claim": "Sweat sodium varies [several-fold] between athletes: salty sweaters are real.",
   "points": ["35 mmol/L is about 800 mg of sodium in every litre of sweat.", "Heavy, salty sweaters lose far more: that's who a 1,000 mg packet is for."],
   "source": SRC_ACSM_FLUID}, 2)
g(2, "r_caffeine", "A", "26:45", "decreasing your perceived effort", "full", 6.0, "research", "green", "THE SCIENCE",
  {"ref": "R-06", "icon": "coffee", "stat": {"num": "3-6", "unit": "MG/KG", "cap": "DOSES THAT HELP IN STUDIES"},
   "claim": "Caffeine blocks adenosine in the brain, so the same effort [feels easier].",
   "points": ["At 74 kg that's about 220-440 mg: a research range, not a prescription.", "Too much can upset the gut: one reason to save it for the end."],
   "source": "ISSN position stand: caffeine and exercise performance (Guest et al., JISSN, 2021)"}, 2)
g(2, "r_carbs", "A", "28:01", "having carbs will allow that", "full", 6.0, "research", "green", "THE SCIENCE",
  {"ref": "R-07", "icon": "gel", "stat": {"num": "30-60", "unit": "G/H", "cap": "CARBS PER HOUR · EFFORTS OF 1-2.5 H"},
   "claim": "For efforts of 1 to 2.5 hours, guidelines suggest [30-60 g of carbs per hour].",
   "points": ["A 1:42 HYROX sits squarely in that window.", "Carbs keep the last repeat close to the first."],
   "source": "ACSM / Academy of Nutrition and Dietetics / Dietitians of Canada joint position: Nutrition and Athletic Performance (Thomas et al., 2016)"}, 1)
g(2, "r_window", "A", "38:49", "okay so in that case i would say do", "full", 6.0, "research", "green", "THE SCIENCE",
  {"ref": "R-08", "icon": "clock", "stat": {"num": "2", "unit": "HOURS", "cap": "POST-EXERCISE PROTEIN WINDOW"},
   "claim": "Protein in the [2 hours] after training strongly boosts muscle building.",
   "points": ["Next session in under ~4 h? Refuel fast: ~1.2 g of carbs per kg per hour.", "That is Carrie's double-day rule: eat within 30 minutes."],
   "source": "ISSN position stand: nutrient timing (Kerksick et al., JISSN, 2017)"}, 1)
g(2, "r_creatine", "B", "03:32", "just taking the one little scoop", "full", 6.0, "research", "green", "THE SCIENCE",
  {"ref": "R-09", "icon": "flask", "stat": {"num": "3-5", "unit": "G/DAY", "cap": "TYPICAL MAINTENANCE DOSE"},
   "claim": "Creatine monohydrate is the [most effective] supplement for high-intensity capacity and lean mass.",
   "points": ["It tops up phosphocreatine, which rebuilds ATP between hard efforts.", "Carrie's caveat stands: some people barely respond."],
   "source": "ISSN position stand: safety and efficacy of creatine supplementation (Kreider et al., JISSN, 2017)"}, 2)
g(2, "r_vitA", "B", "47:40", "vitamin a and vitamin k", "panel", 6.0, "research", "green", "THE SCIENCE",
  {"ref": "R-10", "icon": "leaf",
   "claim": "[Orange] and [green] foods fill the gaps Carrie spotted.",
   "points": ["Orange veg (carrots, sweet potato) carry beta-carotene, which your body turns into vitamin A.",
              "Leafy greens like spinach and kale are top sources of vitamin K."],
   "source": "NIH Office of Dietary Supplements: Vitamin A and Vitamin K fact sheets"}, 2)

# =========================================================================================== batch 3 (A: day, water, vitamin D, cramps)
g(3, "i_daylog", "A", "01:19", "up around 637", "full", 6.0, "timeline", "green", "THE FOOD LOG",
  {"title": "A DAY ON HIS *plate*",
   "events": [{"t": "6:37 AM", "title": "WAKE UP", "icon": "alarm", "note": "74 kg"},
              {"t": "7:30 AM", "title": "MILKSHAKE", "icon": "shake", "note": "his one constant"},
              {"t": "~10:30", "title": "YOGURT + GRANOLA", "icon": "yogurt", "note": "or eggs + guac sandwich"},
              {"t": "1 PM", "title": "CHICKEN + RICE", "icon": "rice", "note": "a little veg in the gravy"},
              {"t": "AFTERNOON", "title": "3 FRUITS", "icon": "apple", "note": "banana, apple, orange"},
              {"t": "EVENING", "title": "TRAINING", "icon": "run", "note": "a sip of water"}]}, 2)
g(3, "i_granola", "A", "02:06", "roughly around 100 to 150 grams", "panel", 5.0, "counter", "paper", "BREAKFAST #2",
  {"variant": "eq", "kicker": "THE OFFICE *bowl*",
   "terms": [{"v": "150", "u": "G", "l": "GREEK YOGURT"}, {"op": "+"}, {"v": "100-150", "u": "G", "l": "GRANOLA", "res": True}],
   "sub": "+ a little honey, around 10:30."}, 3)
g(3, "i_lunch_plate", "A", "03:50", "200 to 300 grams of rice", "full", 6.0, "plate", "paper", "HIS LUNCH",
  {"title": "LUNCH: *lots* OF CARBS",
   "plates": [{"name": "CHICKEN + RICE", "note": "eaten around 1 pm",
               "parts": [{"label": "RICE", "amt": "200-300 G", "f": 0.62, "type": "carbs"},
                         {"label": "CHICKEN", "amt": "~150 G", "f": 0.3, "type": "protein"},
                         {"label": "VEG", "amt": "A LITTLE, IN THE GRAVY", "f": 0.08, "type": "veg"}]}],
   "side": {"t": "CARRIE: *probably* NEEDS MORE VEG", "d": "from a nutrient standpoint", "at": 2.6}}, 2)
g(3, "i_fruit_abo", "A", "05:34", "one banana one apple and one orange", "panel", 5.0, "list", "ink", "AFTERNOON SNACK",
  {"title": "EVERY DAY: *A, B, O*",
   "items": [{"t": "1 banana", "icon": "banana"}, {"t": "1 apple", "icon": "apple"}, {"t": "1 orange", "icon": "orange"}],
   "sub": "Office fruit, after lunch."}, 3)
g(3, "i_water", "A", "06:45", "you would only need about", "full", 6.0, "chart", "paper", "WATER",
  {"variant": "fill", "title": "HOW MUCH *water*?", "value": 2.2, "max": 3, "big": "2.2", "bigUnit": "L / DAY",
   "bands": [{"from": 2.2, "to": 2.2, "t": "HIS NEED: 2.2 L", "d": "AT 74 KG, NORMAL SWEAT DAY", "at": 2.0, "dy": 70},
             {"from": 2.0, "to": 3.0, "t": "HE DRINKS 2-3 L", "d": "BOTTLE REFILLED 2-3x AT WORK", "col": "fg", "at": 2.6, "dy": -90}],
   "sub": "Heavy, sweaty session? *Then* a bit more."}, 2)
g(3, "i_supp_stack", "A", "09:45", "supplement from costco", "panel", 5.0, "list", "paper", "SUPPLEMENTS",
  {"title": "HIS CURRENT *stack*",
   "items": [{"t": "Omega-3", "d": "after breakfast, not consistent", "icon": "pill"},
             {"t": "Men's multivitamin", "d": "a warehouse-store multi", "icon": "pill"},
             {"t": "Whey protein", "d": "in the milkshake", "icon": "shake"}]}, 3)
g(3, "i_vitd_months", "A", "11:01", "october to april", "full", 5.5, "chart", "paper", "VITAMIN D",
  {"variant": "months", "title": "VITAMIN D: *October to April*", "on": [9, 10, 11, 0, 1, 2, 3],
   "order": [9, 10, 11, 0, 1, 2, 3, 4, 5, 6, 7, 8], "big": "1,000", "bigUnit": "IU EVERY DAY",
   "sub": "Food alone can't cover it: even a simple chewable works."}, 2)
g(3, "i_carbs_myth", "A", "17:34", "the carbs will have nothing to do", "full", 6.0, "myth", "ink", "CARBS vs CRAMPS",
  {"myth": "A gel will stop the *cramps*", "fact": "Carbs have [nothing to do] with cramping",
   "sub": "He had the energy. His legs just wouldn't go."}, 2)

# =========================================================================================== batch 4 (A: sweat test, race drinks)
g(4, "i_sweat_steps", "A", "19:52", "if you kind of did a wait before", "full", 6.5, "steps", "paper", "THE SWEAT TEST",
  {"title": "HOW TO MEASURE YOUR *sweat*",
   "steps": [{"title": "WEIGH IN", "body": "on a scale, in your kit or nothing", "icon": "scale"},
             {"title": "TRAIN", "body": "your normal session", "icon": "run"},
             {"title": "WEIGH OUT", "body": "*same* clothes as before", "icon": "scale"},
             {"title": "1 KG = 1 L", "body": "the difference is the [sweat you didn't replace]", "icon": "drop", "hot": True}]}, 1)
g(4, "i_same_clothes", "A", "20:25", "you have to be the same", "panel", 5.0, "dodont", "paper", "THE SWEAT TEST",
  {"do": {"h": "DO", "items": [{"t": "Same clothes, before and after", "d": "or none at all"}]},
   "dont": {"h": "DON'T", "items": [{"t": "Switch kit between weigh-ins", "d": "sweaty clothes soak up water and throw the weights off"}]}}, 2)
g(4, "i_rehydrate", "A", "21:28", "like about 250 mils more", "panel", 5.5, "bars", "paper", "REHYDRATE",
  {"title": "LOST 1 KG? DRINK *more* THAN 1 L",
   "bars": [{"label": "LOST", "v": 1.0, "disp": "1 L"}, {"label": "+250 ML", "v": 1.25, "disp": "1.25 L", "hl": True},
            {"label": "+500 ML", "v": 1.5, "disp": "1.5 L", "hl": True}],
   "max": 1.6, "illus": "SOME OF IT LEAVES AS URINE, SO OVERSHOOT A LITTLE"}, 2)
g(4, "i_station_steps", "A", "22:42", "find out what kind of electrolyte drink", "full", 6.5, "steps", "ink", "RACE DRINKS",
  {"title": "AT THE AID STATION",
   "steps": [{"title": "FIND OUT", "body": "which electrolyte drink the race serves, and its sodium", "icon": "doc"},
             {"title": "SWAP THE CUP", "body": "sports drink instead of plain water", "icon": "bottle"},
             {"title": "NOT ALLOWED?", "body": "sodium capsules [with each gel]", "icon": "pill", "hot": True}]}, 1)
g(4, "i_lmnt", "A", "25:36", "is a thousand milligrams of sodium", "full", 5.5, "counter", "paper", "SODIUM",
  {"kicker": "ONE PACKET", "num": "1,000", "unit": "MG", "line2": "OF SODIUM",
   "sub": "For a *really salty* sweater. Trial it in training first.",
   "photo": "sports-drink", "photoCap": "electrolyte drink", "tilt": 3}, 2)
g(4, "i_caffeine_gauge", "A", "26:34", "basically a stimulant", "full", 6.0, "chart", "ink", "CAFFEINE",
  {"variant": "gauge", "title": "CAFFEINE = *stimulant*", "from": 0.82, "to": 0.5, "dropAt": 2.0, "chip": "+ CAFFEINE",
   "readout": "PERCEIVED EFFORT",
   "keys": [{"t": "SAME WORK, FEELS *easier*", "d": "it makes you believe you can go harder", "at": 1.0},
            {"t": "SAVE IT FOR THE END", "d": "all race long can make you sick and upset your gut", "at": 2.6}]}, 2)
g(4, "i_intervals", "A", "27:52", "the last one i took twice the time", "full", 6.0, "bars", "paper", "CARBS IN RACES",
  {"title": "FIRST KM vs *last* KM",
   "bars": [{"label": "FIRST 1K", "v": 1, "disp": "1×"}, {"label": "LAST 1K", "v": 2, "disp": "2×", "hl": True, "note": "HE CRAMPED"},
            {"label": "THE GOAL", "v": 1, "disp": "1×", "ghost": True, "note": "WITH CARBS"}],
   "max": 2.2, "side": {"t": "CARBS KEEP THE LAST REPEAT AS GOOD AS THE *first*", "d": "Carrie: interval-type racing needs carbs to stay consistent.", "at": 1.9},
   "illus": "TIME PER KM, RELATIVE TO HIS FIRST"}, 2)

# =========================================================================================== batch 5 (A: muscle, gym, window)
g(5, "i_weight_range", "A", "29:21", "70 to 80", "panel", 5.0, "chart", "paper", "BODY WEIGHT",
  {"variant": "range", "title": "HIS WEIGHT *swings*", "min": 68, "max": 82, "step": 1, "major": 2,
   "bands": [{"from": 72, "to": 79, "label": "72-79 KG IN 2-3 MONTHS"}],
   "marks": [{"v": 74, "num": "74", "label": "TODAY, KG"}]}, 3)
g(5, "i_muscle_pyramid", "A", "30:01", "the training is the first part", "full", 6.0, "steps", "ink", "GAIN MUSCLE",
  {"variant": "pyramid", "title": "STRONGER *without* GETTING SLOWER",
   "steps": [{"title": "TRAINING", "body": "the biggest influence"}, {"title": "EAT ENOUGH", "body": "to fuel the gains"},
             {"title": "DON'T OVERSHOOT", "body": "gain too much and you get slower", "hot": True}],
   "sub": "It's a *fine balance.*"}, 2)
g(5, "i_set_drink", "A", "33:55", "drink you know almost between every set", "panel", 5.0, "counter", "paper", "HYDRATION",
  {"kicker": "HEAVY SWEATER?", "num": "1", "unit": "L", "line2": "PER GYM SESSION",
   "sub": "Carrie's bottle is a litre. Sip *almost between every set*, mornings especially.", "icon": "bottle"}, 3)
g(5, "i_preworkout", "A", "35:40", "so let's say something like a banana", "panel", 5.5, "list", "paper", "BEFORE THE GYM",
  {"title": "BEFORE A *morning* LIFT",
   "items": [{"t": "A banana", "icon": "banana"}, {"t": "Banana + peanut butter", "icon": "nut"}, {"t": "Peanut butter on toast", "icon": "toaster"}],
   "sub": "Small is fine: just bring your [blood sugar] up."}, 2)
g(5, "i_shower_map", "A", "37:10", "35 to 40 minutes", "full", 6.5, "map", "paper", "AFTER THE GYM",
  {"title": "GYM TO DESK: *35-40 MIN* WITHOUT FOOD",
   "stops": [{"u": 0.02, "v": 0.2, "t": "GYM", "d": "IN HIS BUILDING", "icon": "dumbbell"},
             {"u": 0.45, "v": -0.05, "t": "SHOWER + SHAKE", "d": "REFUEL WHILE YOU GET READY", "icon": "shake", "hot": True, "w": 360},
             {"u": 0.95, "v": 0.3, "t": "WORK", "d": "5 MIN BIKE / 10 MIN WALK", "icon": "office", "al": "r"}],
   "legs": [{"t": "HEAD BACK UP"}, {"t": "BIKE OR WALK"}]}, 2)

# =========================================================================================== batch 6 (B: creatine, protein, veg)
g(6, "i_omega_myth", "B", "00:39", "omega 3 is just simply giving you", "full", 6.0, "myth", "ink", "OMEGA-3",
  {"myth": "Omega-3 will *burn* fat", "fact": "It's just a [source of fat]", "sub": "A different style of fat. It won't burn anything."}, 2)
g(6, "i_creatine_loop", "B", "02:44", "it helps to regenerate atp quicker", "full", 6.5, "steps", "paper", "CREATINE",
  {"variant": "loop", "title": "HOW CREATINE *works*",
   "steps": [{"title": "ATP FASTER", "body": "energy rebuilt quicker"}, {"title": "MORE POWER", "body": "push a bit further"},
             {"title": "MUSCLE", "body": "develops faster", "hot": True}],
   "center": "A *training* TOOL", "sub": "Some people barely respond. Takes longer than a week to show."}, 2)
g(6, "i_creatine_myth", "B", "03:11", "it takes longer than", "panel", 5.5, "myth", "ink", "CREATINE",
  {"myth": "Bigger biceps after *one week*", "fact": "It takes [longer] than that", "sub": "Carrie: could be placebo, and some people don't respond at all.",
   "mfp": 40, "ffp": 40}, 3)
g(6, "i_shake_kcal", "B", "04:22", "roughly around 1000 calories", "panel", 5.0, "counter", "paper", "HIS SHAKE",
  {"kicker": "HOMEMADE MILKSHAKE", "num": "1,000", "unit": "KCAL", "line2": "45-50 G PROTEIN",
   "sub": "Banana, dates, whey, milk. *Plenty* of protein.", "photo": "milkshake", "tilt": -3}, 2)
g(6, "i_second_bfast", "B", "05:00", "within this two hour timeframe", "panel", 5.0, "clock", "green", "AFTER THE SHAKE",
  {"title": "NEXT MEAL WITHIN *2 H*", "max": 3, "ticks": 12, "majorEvery": 4,
   "nums": [{"v": 0, "l": "0"}, {"v": 1, "l": "1H"}, {"v": 2, "l": "2H"}],
   "arcs": [{"from": 0, "to": 2, "col": "a", "t": 0.9, "d": 1.0}], "hand": 2, "handAt": 0.9, "handDur": 1.0,
   "center": "2ND *breakfast*", "centerAt": 1.8}, 3)
g(6, "i_lunch_rebal", "B", "10:51", "a cup of veggies in there", "full", 6.5, "plate", "paper", "LUNCH, REBALANCED",
  {"title": "SAME CHICKEN, A BIT *less* RICE",
   "plates": [{"name": "BEFORE", "parts": [{"label": "RICE", "amt": "200-300 G", "f": 0.62, "type": "carbs"},
                                            {"label": "CHICKEN", "amt": "~150 G", "f": 0.3, "type": "protein"},
                                            {"label": "VEG", "amt": "A LITTLE", "f": 0.08, "type": "veg"}], "at": 0.5},
              {"name": "AFTER", "hot": True, "parts": [{"label": "RICE", "amt": "~2 CUPS COOKED", "f": 0.45, "type": "carbs"},
                                                       {"label": "CHICKEN", "amt": "KEEP IT", "f": 0.28, "type": "protein"},
                                                       {"label": "VEG", "amt": "1 CUP, RAW OR COOKED", "f": 0.27, "type": "veg"}], "at": 1.7}],
   "sub": "HYROX = less volume than Ironman, so a bit less rice."}, 1)
g(6, "i_carrots", "B", "10:15", "just get some raw baby carrots", "panel", 5.0, "list", "green", "EASY VEG",
  {"title": "VEG *without* COOKING",
   "items": [{"t": "Raw baby carrots", "d": "in a container at work", "icon": "carrot"},
             {"t": "A bag of frozen veg", "d": "just throw it in", "icon": "snow"},
             {"t": "A quick salad", "d": "some greens", "icon": "leaf"}]}, 3)
g(6, "i_fists", "B", "11:54", "two cups of rice cooked", "panel", 5.0, "counter", "ink", "PORTION GUIDE",
  {"kicker": "RICE, BY THE FIST", "num": "2", "unit": "FISTS", "line2": "≈ 2 CUPS COOKED",
   "sub": "Energy needs are individual: we'll *see* if it's around that.", "icon": "rice"}, 3)

# =========================================================================================== batch 7 (B: afternoon, primers, dinners)
g(7, "i_primer", "B", "18:32", "like something simple", "panel", 5.5, "list", "paper", "BEFORE 6 PM",
  {"title": "PRIME YOURSELF *first*",
   "items": [{"t": "Fruit snacks", "icon": "apple"}, {"t": "A small honey wafer", "icon": "bar"},
             {"t": "A small bar", "icon": "bar"}, {"t": "Or a gel", "icon": "gel"}],
   "sub": "Just before the session: bring your [blood sugar] up."}, 2)
g(7, "i_forgot_carbs", "B", "19:04", "just loaded protein in my home", "full", 6.5, "compare", "paper", "THE MISTAKE",
  {"variant": "balance", "title": "LOADED PROTEIN, *forgot* CARBS",
   "a": {"name": "PROTEIN", "blocks": ["SHAKE", "BARS", "CHICKEN"]}, "b": {"name": "CARBS", "blocks": ["FRUIT", "BREAD", "RICE"]},
   "sub": "Protein builds muscle. *Carbs* fuel the session that builds it."}, 1)
g(7, "i_protein_bar", "B", "19:33", "20 grams of protein in it", "panel", 5.0, "counter", "ink", "SNACK SWAP",
  {"kicker": "HIS PROTEIN BAR", "num": "20", "unit": "G", "line2": "PROTEIN, OK CARBS",
   "sub": "A pre-gym option instead of the banana + peanut butter.", "icon": "bar"}, 3)
g(7, "i_hard_easy", "B", "23:58", "particularly if it's a heavy workout", "panel", 5.5, "dodont", "ink", "EVENING SESSION",
  {"do": {"h": "HARD SESSION", "items": [{"t": "Move a fruit to just before it", "d": "or take a gel: no upset stomach"}]},
   "dont": {"h": "EASY SWIM", "items": [{"t": "Don't worry about it", "d": "no extra fuel needed"}]}}, 2)
g(7, "i_oats_steps", "B", "25:20", "overnight oats", "panel", 5.5, "steps", "paper", "NO-COOK DINNER",
  {"title": "OVERNIGHT *oats*",
   "steps": [{"title": "MAKE IT", "body": "the night before", "icon": "jar"},
             {"title": "FRIDGE", "body": "a full day", "icon": "fridge"},
             {"title": "EAT IT COLD", "body": "after training, or at the gym", "icon": "fork", "hot": True}]}, 2)
g(7, "i_lift_gut", "B", "28:31", "most times when people do weight", "panel", 5.5, "compare", "paper", "DOUBLE SESSIONS",
  {"title": "CARDIO, *then* GYM",
   "a": {"name": "CARDIO", "icon": "run", "rows": [{"ok": False, "t": "Jostles your stomach"}]},
   "b": {"name": "WEIGHTS", "icon": "dumbbell", "rows": [{"ok": True, "t": "Can handle more food: eat between the two"}]},
   "mid": "->", "win": "b"}, 3)
g(7, "i_tuna_eq", "B", "30:25", "because tuna's got your protein", "full", 5.5, "counter", "paper", "QUICK DINNER",
  {"variant": "eq", "kicker": "THE *tuna sandwich*",
   "terms": [{"v": "TUNA", "u": "PROTEIN", "l": "A CAN"}, {"op": "+"}, {"v": "BREAD", "u": "CARBS", "l": "TWO SLICES"},
             {"op": "="}, {"v": "×2", "u": "SANDWICHES", "l": "DINNER, NO STOVE", "res": True}],
   "sub": "Can't face cooking? What's wrong with a *sandwich*?"}, 2)

# =========================================================================================== batch 8 (B: shakes, dinner, micronutrients)
g(8, "i_shake_vs_food", "B", "34:23", "your protein shake is not enough", "full", 6.5, "compare", "paper", "SHAKE vs FOOD",
  {"title": "A SHAKE IS *not* DINNER",
   "a": {"name": "PROTEIN SHAKE", "kicker": "ON ITS OWN", "icon": "shake", "photo": "protein-powder",
         "rows": [{"ok": True, "t": "Quick, easy, accessible"}, {"ok": False, "t": "Not enough to recover on"}, {"ok": False, "t": "Still needs carbs with it"}]},
   "b": {"name": "REAL FOOD", "kicker": "THE FIX", "icon": "sandwich", "photo": "tuna-sandwich",
         "rows": [{"ok": True, "t": "Two tuna sandwiches"}, {"ok": True, "t": "Overnight oats"}, {"ok": True, "t": "A homemade smoothie"}]},
   "win": "b"}, 1)
g(8, "i_smoothie", "B", "35:34", "just use some greek yogurt or even cottage cheese", "panel", 5.5, "steps", "ink", "DINNER SMOOTHIE",
  {"title": "SWAP THE *powder*",
   "steps": [{"title": "GREEK YOGURT", "body": "or cottage cheese, instead of protein powder + milk", "icon": "yogurt"},
             {"title": "FROZEN FRUIT", "body": "berries work", "icon": "snow"},
             {"title": "+ A BANANA", "body": "blend: a bit of a shake", "icon": "banana", "hot": True}]}, 3)
g(8, "i_night_gap", "B", "46:24", "let's say you did a workout at night", "full", 6.5, "timeline", "ink", "SKIPPED DINNER",
  {"title": "NO DINNER, *no* GAINS",
   "events": [{"t": "NIGHT", "title": "WORKOUT", "icon": "run"}, {"t": "AFTER", "title": "SHAKE ONLY", "icon": "shake"},
              {"t": "OVERNIGHT", "title": "SLEEP", "icon": "bed"}, {"t": "MORNING", "title": "GYM ON A BANANA", "icon": "banana"},
              {"t": "RESULT", "title": "LITTLE MUSCLE BUILT", "icon": "arm"}],
   "gap": {"a": 1, "b": 3, "label": "NOTHING IN", "note": "no energy to actually push"}}, 2)
g(8, "i_dinner_plate", "B", "45:55", "you've got some color in there too", "panel", 5.5, "plate", "paper", "DINNER GOAL",
  {"title": "DINNER = CARBS + PROTEIN + *colour*",
   "plates": [{"name": "THE EVENING PLATE", "note": "recovery before you sleep",
               "parts": [{"label": "CARBS", "amt": "RICE, ROTI, BREAD", "f": 0.36, "type": "carbs"},
                         {"label": "PROTEIN", "amt": "CHICKEN, TUNA, EGGS", "f": 0.34, "type": "protein"},
                         {"label": "COLOUR", "amt": "VEG", "f": 0.30, "type": "veg"}]}]}, 2)
g(8, "i_micros", "B", "47:13", "if you're eating three pieces of fruit a day", "full", 6.0, "chart", "paper", "MICRONUTRIENTS",
  {"variant": "status", "title": "WHAT HIS DIET *covers*",
   "rows": [{"name": "VITAMIN C", "v": 0.9, "ok": True, "t": "Covered", "d": "three pieces of fruit a day"},
            {"name": "VITAMIN A", "v": 0.3, "ok": False, "t": "Likely low", "d": "no orange-coloured veg"},
            {"name": "VITAMIN K", "v": 0.25, "ok": False, "t": "Likely low", "d": "no greens"}],
   "sub": "Carrie's read of his food log, not a blood test."}, 2)
g(8, "i_greens", "B", "48:00", "a bag of spinach or a", "panel", 5.5, "list", "paper", "MORE GREENS",
  {"title": "THREE WAYS IN",
   "items": [{"t": "Frozen spinach or kale", "d": "into the morning shake", "icon": "shake"},
             {"t": "A salad at lunch", "icon": "leaf"},
             {"t": "Chicken salad at dinner", "d": "with a roti on the side", "icon": "chicken"}]}, 2)
g(8, "i_food_vs_pill", "B", "49:05", "there's things called", "full", 6.5, "compare", "green", "FOOD vs PILLS",
  {"title": "REAL FOOD *or* A MULTIVITAMIN?",
   "a": {"name": "MULTIVITAMIN", "kicker": "ON NO-VEG DAYS", "icon": "pill", "photo": "multivitamin",
         "rows": [{"ok": True, "t": "Vitamins + minerals"}, {"ok": False, "t": "No fibre"}, {"ok": False, "t": "No phytochemicals"}]},
   "b": {"name": "REAL FOOD", "kicker": "THE GOAL", "icon": "leaf", "photo": "veg-market",
         "rows": [{"ok": True, "t": "Fibre"}, {"ok": True, "t": "Natural nutrients"}, {"ok": True, "t": "[Phytochemicals]: you can't get that in a bottle"}]},
   "win": "b"}, 1)
