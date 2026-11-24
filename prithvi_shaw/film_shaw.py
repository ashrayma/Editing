# ============================================================================ the film
# Every beat of the creator's script, in order. b(beat, t) = t seconds into a beat; until(beat, t) = from there to
# the next beat's start. Each photo / clip / AI still / screen grab is used once (use() enforces it).

P, C, A, BR, CO = "assets/photos/", "footage/clips/", "assets/ai/", "assets/broll/", "assets/cutouts/"


def C_(beat, text, off=0.0, end=None):
    s = b(beat, off)
    e = b(end[0], end[1]) if end else BEAT[beat][1]
    cap(text, s, round(max(0.6, e - s), 2))


def span(b0, b1):
    """From b0's start to b1's next-beat start."""
    return round(until(b1) + BEAT[b1][0] - BEAT[b0][0], 2)


# ---------------------------------------------------------------- OPENING (hook, fast)
full(C + "nz_bat_00.mp4", 0.0, until("o_546"), dim=0.5)
glow("546", b("o_546", 0.1), 2.6, "left", 260, label="RUNS · AGE 14", y=250)
glow("18", b("o_546", 2.8), 1.8, "right", 260, label="TEST DEBUT AGE", y=250)
chips([("FIRST INNINGS: CENTURY", "yellow")], b("o_546", 4.6), until("o_546", 4.6), "center", y=640)
C_("o_546", "*546* runs at 14 · Test debut at *18* · a *century*")
full(A + "ai_crowd_night.jpg", b("o_superstar"), until("o_superstar"), dim=0.45, ai=True)
head(["INDIA'S NEXT", "SUPERSTAR"], b("o_superstar", 0.1), 3.3, "left", 130, accent=(1,))
head(["“THE NEXT SACHIN”", "“FUTURE CAPTAIN”"], b("o_superstar", 3.5), until("o_superstar", 3.5), "left", 110, accent=(0,))
C_("o_superstar", "Compared to *Sachin*. Talked of as a *future captain*.")
full(C + "cummins_bowled.mp4", b("o_fewyears"), until("o_fewyears"))
C_("o_fewyears", "But within a few *years*…")
space(b("o_door"), until("o_door") + blen("o_status") + 0.2)
card(C + "shaw_walks.mp4", b("o_door"), until("o_door"), "right", maxw=900)
head(["AWAY FROM", "INTERNATIONAL", "CRICKET"], b("o_door", 0.1), until("o_door", 0.1), "left", 100, accent=(1, 2))
C_("o_door", "…away from international cricket")
chips([("INDIA JERSEY ✕", "red"), ("IPL BUYERS ✕", "red"), ("SUPERSTAR STATUS ✕", "red")], b("o_status", -4.3) if False else b("o_status"),
      until("o_status"), "center", gap=0.9, y=380)
C_("o_status", "No India jersey. No IPL buyers. No *superstar* status.")
roadmap(len(CURVE) - 1, b("o_what"), 2.4, title="WHAT HAPPENED?")
C_("o_what", "So what *happened* to Prithvi Shaw?")
yearcard("PRITHVI SHAW", b("o_what", 2.4), round(BEAT["c1_nov2013"][0] - b("o_what", 2.4), 2),
         sub="India's next Sachin… what happened to him?", kicker="UNTOLD STORIES · #6")

# ---------------------------------------------------------------- 01 THE PRODIGY
yearcard("2013", b("c1_nov2013"), until("c1_nov2013"), sub="November · Harris Shield, Mumbai", kicker="CHAPTER 01 · THE PRODIGY")
C_("c1_nov2013", "November 2013 · Mumbai's *Harris Shield*")
full(A + "ai_school_ground.jpg", b("c1_boy"), until("c1_boy"), dim=0.3, ai=True)
head(["A 14-YEAR-OLD", "WALKS OUT TO BAT"], b("c1_boy", 0.1), 3.0, "left", 110, accent=(1,), y=520)
head(["SCHOOL CRICKET", "HISTORY"], b("c1_boy", 3.2), until("c1_boy", 3.2), "left", 110, accent=(1,), y=520)
C_("c1_boy", "A 14-year-old walks out… and makes *history*")
browser(BR + "rec_shaw_546.webm", b("c1_546"), until("c1_546"), "right", maxw=1000, media_start=2.0)
glow("546", b("c1_546", 0.4), until("c1_546", 0.4), "left", 230, label="IN ONE INNINGS · 330 BALLS", y=300)
C_("c1_546", "*546* runs. In *one* innings.")
full(A + "ai_scorebook.jpg", b("c1_confidence"), until("c1_confidence"), dim=0.45, ai=True)
head(["A DIFFERENT", "CONFIDENCE"], b("c1_confidence", 0.1), until("c1_confidence", 0.1), "left", 130, accent=(1,))
C_("c1_confidence", "A different kind of *confidence*")
full(C + "nz_bat_01.mp4", b("c1_frontfoot"), until("c1_frontfoot"), dim=0.35)
chips(["FRONT-FOOT SHOTS", "ATTACKS THE BOWLERS", ("READS THE GAME AT 14", "yellow")], b("c1_frontfoot", 0.3),
      until("c1_frontfoot", 0.3), "left", gap=1.6, y=360)
C_("c1_frontfoot", "Front foot · attacking · reading the game *that young*")
head(["AN EXTRAORDINARY", "TALENT"], b("c1_talent", 0.1), until("c1_talent", 0.1), "center", 140, accent=(1,))
C_("c1_talent", "Indian cricket had found an *extraordinary talent*")
phoneimg(P + "u19_gill_shaw_insta.jpg", b("c1_u19"), until("c1_u19") + blen("c1_gill") + 0.1, "right")
head(["2018", "U19 WORLD CUP", "CHAMPIONS"], b("c1_u19", 0.2), until("c1_u19", 0.2), "left", 110, accent=(0,), kicker="CAPTAIN: PRITHVI SHAW", kcolor=CYAN)
C_("c1_u19", "2018: Shaw leads India to the *U19 World Cup*")
head(["IN THAT TEAM:", "SHUBMAN GILL"], b("c1_gill", 0.1), until("c1_gill", 0.1), "left", 110, accent=(1,))
C_("c1_gill", "In that team: another young batter — *Shubman Gill*")
vs("SHAW", "GILL", b("c1_expect"), until("c1_expect"), ltag="YOUNG STAR", rtag="YOUNG STAR", lcol=Y, rcol=CYAN, t2=b("c1_expect", 0.6))
C_("c1_expect", "Two young stars. *Huge* expectations.")
head(["THE DEBUT CAME", "BEFORE GILL'S"], b("c1_before_gill"), 2.6, "center", 120, accent=(1,))
datecard("4 OCT 2018", "RAJKOT", b("c1_before_gill", 2.6), until("c1_before_gill", 2.6), sub="India vs West Indies")
C_("c1_before_gill", "His debut came *before* Gill's · Rajkot, *4 Oct 2018*")
card(P + "debut_raise.jpg", b("c1_makes"), until("c1_makes"), "right", maxw=700, maxh=680, label="RAJKOT", sub="Test debut", focus="50% 25%")
head(["TEST", "DEBUT"], b("c1_makes", 0.1), until("c1_makes", 0.1), "left", 160, accent=(1,))
C_("c1_makes", "Prithvi Shaw makes his *Test debut*")
cutword(CO + "debut_100.png", "134", b("c1_134"), until("c1_134"), "right", tone="navy", sub="FIRST INNINGS · FIRST TEST")
C_("c1_134", "And a *century* in his first innings: *134*")
head(["ONE OF THE YOUNGEST", "INDIANS WITH A", "DEBUT CENTURY"], b("c1_youngest"), until("c1_youngest"), "center", 110, accent=(2,))
C_("c1_youngest", "One of the *youngest* Indians to score a debut ton")
head(["LIKE SCHOOL CRICKET,", "HE'LL DOMINATE", "THE WORLD?"], b("c1_dominate"), until("c1_dominate"), "center", 110, accent=(1,))
C_("c1_dominate", "He'd dominate internationals like he did at school?")
full(A + "ai_newspapers.jpg", b("c1_nextsachin"), until("c1_nextsachin"), dim=0.45, ai=True)
head(["“INDIA'S", "NEXT SACHIN”"], b("c1_nextsachin", 0.2), until("c1_nextsachin", 0.2), "left", 150, accent=(1,), kicker="THE MEDIA", kcolor=CYAN)
C_("c1_nextsachin", "The media: *India's next Sachin*")
vs("A DEBUT<br>CENTURY", "STAYING<br>THERE", b("c1_staying"), until("c1_staying"), ltag="NOT THE HARDEST PART", rtag="THE REAL CHALLENGE",
   lcol="#fff", rcol=CYAN, t2=b("c1_staying", 3.6))
C_("c1_staying", "The real challenge is *staying there*")
head(["THE FIRST SETBACK", "WAS COMING"], b("c1_setback"), until("c1_setback") - 0.2, "center", 130, accent={1: "#ff5a5f"})
C_("c1_setback", "His first big *setback* was coming")

# ---------------------------------------------------------------- 02 THE SETBACK
roadmap(3, round(BEAT["c1_setback"][1] + 0.05, 2), 2.6, title="02 · THE SETBACK")
full(C + "inj_chase.mp4", b("c2_nov2018", 1.5), 3.0)
datecard("NOV 2018", "AUSTRALIA", b("c2_nov2018", 1.6), until("c2_nov2018", 1.6), sub="his first overseas Test series, next")
C_("c2_nov2018", "Nov 2018 · his *first overseas* Test series awaited")
full(C + "inj_fall.mp4", b("c2_ankle"), 2.2)
full(C + "inj_lying.mp4", b("c2_ankle", 2.2), 2.2)
full(C + "inj_physio.mp4", b("c2_ankle", 4.4), until("c2_ankle", 4.4))
stamp("OUT OF THE SERIES", b("c2_ankle", 4.6), until("c2_ankle", 4.6), 1080, 120, rot=-6, size=56)
C_("c2_ankle", "A warm-up game: his *ankle* gives way · out of the series")
card(C + "inj_carried.mp4", b("c2_history"), until("c2_history"), "right", maxw=920)
head(["INDIA: MAKING", "HISTORY", "SHAW: REHAB"], b("c2_history", 0.2), until("c2_history", 0.2), "left", 100, accent={1: CYAN, 2: "#ff5a5f"})
C_("c2_history", "India chased *history*. Shaw chased *fitness*.")
full(C + "inj_replay.mp4", b("c2_timing"), 3.2, dim=0.3)
head(["INJURIES ARE", "PART OF THE GAME"], b("c2_timing", 0.1), 3.0, "left", 110)
full(C + "inj_helped.mp4", b("c2_timing", 3.2), 4.5, dim=0.6)
full(C + "inj_carried2.mp4", b("c2_timing", 7.7), 4.0, dim=0.6)
space(b("c2_timing", 11.7), until("c2_timing", 11.7))
depthlist(["EXPERIENCE", "CONFIDENCE", "A PLACE IN THE TEAM"], b("c2_timing", 3.2), until("c2_timing", 3.2),
          [b("c2_timing", 3.4), b("c2_timing", 8.2), b("c2_timing", 10.2)])
C_("c2_timing", "For a young player, *timing* is everything")
full(C + "inj_stairs.mp4", b("c2_momentum"), until("c2_momentum"), dim=0.35)
head(["MOMENTUM:", "INTERRUPTED"], b("c2_momentum", 0.1), 2.4, "left", 120, accent={1: "#ff5a5f"})
chips([("THE NEXT ONE WASN'T AN INJURY", "red")], b("c2_momentum", 2.5), until("c2_momentum", 2.5) - 0.2, "left", y=620)
C_("c2_momentum", "Momentum *interrupted*. The next setback wasn't an injury.")

# ---------------------------------------------------------------- 03 THE SUSPENSION
roadmap(4, round(BEAT["c2_momentum"][1] + 0.05, 2), 2.4, title="03 · THE SUSPENSION")
datecard("JULY 2019", "BCCI", b("c3_july", 1.2), until("c3_july", 1.2) + 0.5, sub="an announcement")
C_("c3_july", "July *2019*")
space(b("c3_bcci"), until("c3_bcci") + blen("c3_terbutaline") + 0.2)
glass("ANTI-DOPING · BCCI", ["Player: <b>Prithvi Shaw</b>", "Dope test: <b style='color:#ff5a5f'>POSITIVE</b>"], b("c3_bcci", 0.5),
      until("c3_bcci", 0.5), "center", badge="ANNOUNCEMENT", w=900)
C_("c3_bcci", "BCCI: Shaw's dope test came back *positive*")
head(["TERBUTALINE"], b("c3_terbutaline", 0.1), until("c3_terbutaline", 0.1), "center", 170, accent=(0,), kicker="A BANNED SUBSTANCE", kcolor="#ff5a5f")
C_("c3_terbutaline", "Banned substance in his sample: *terbutaline*")
full(A + "ai_medicine.jpg", b("c3_cough"), until("c3_cough"), dim=0.35, ai=True)
head(["COUGH SYRUP.", "ACCIDENTAL."], b("c3_cough", 0.2), until("c3_cough", 0.2), "left", 130, accent=(1,), kicker="SHAW'S EXPLANATION", kcolor=CYAN)
C_("c3_cough", "His explanation: *cough medicine*, taken by accident")
space(b("c3_backdated"), until("c3_backdated"))
glass("BCCI DECISION", ["Inadvertent ingestion: <b>accepted</b>", "Suspension: <b>8 months</b>", "Backdated"],
      b("c3_backdated", 0.3), 5.6, "center", w=900)
head(["THE IMPACT WAS", "BIGGER THAN", "A FEW MATCHES"], b("c3_backdated", 6.0), until("c3_backdated", 6.0), "center", 110, accent=(2,))
C_("c3_backdated", "BCCI accepted it was accidental: *8-month* backdated ban")
full(A + "ai_empty_nets.jpg", b("c3_stage"), until("c3_stage"), dim=0.35, ai=True)
head(["THE MOMENT TO", "ESTABLISH HIMSELF…", "SPENT AWAY"], b("c3_stage", 0.2), until("c3_stage", 0.2), "left", 100, accent={2: "#ff5a5f"})
C_("c3_stage", "The time to establish himself — spent *away from cricket*")
head(["HIS U19 TEAMMATES", "WERE MOVING AHEAD"], b("c3_u19mates"), until("c3_u19mates"), "center", 120, accent=(1,))
C_("c3_u19mates", "Meanwhile, his U19 teammates *moved ahead*")
cutword(CO + "gill_testcap.png", "GILL", b("c3_gill"), round(until("c3_gill") + 3.2, 2), "right", tone="navy", wcolor=CYAN)
C_("c3_gill", "Look at *Shubman Gill*")
space(b("c3_journeys", 3.2), until("c3_journeys", 3.2))
diverge(b("c3_journeys", 3.2), until("c3_journeys", 3.2), b("c3_journeys", 5.0))
C_("c3_journeys", "Same generation. Same start. *Very different journeys.*")
yearcard("DEC 2020", b("c3_dec2020"), round(until("c3_dec2020") + blen("c3_direction"), 2), sub="the match that changed his Test career")
C_("c3_dec2020", "December 2020 — the match that changed *everything*", end=("c3_direction", -0.01))

# ---------------------------------------------------------------- 04 ADELAIDE
roadmap(5, round(BEAT["c3_direction"][1] + 0.05, 2), 2.6, title="04 · ADELAIDE")
full(A + "ai_pinkball.jpg", b("c4_adelaide"), until("c4_adelaide"), dim=0.3, ai=True)
datecard("DEC 2020", "ADELAIDE", b("c4_adelaide", 1.4), until("c4_adelaide", 1.4), sub="the pink-ball Test")
C_("c4_adelaide", "Adelaide · the *pink-ball* Test")
card(C + "cummins_wide.mp4", b("c4_xi"), until("c4_xi"), "right", maxw=900)
head(["IN THE", "PLAYING XI"], b("c4_xi", 0.1), until("c4_xi", 0.1), "left", 130, accent=(1,))
C_("c4_xi", "Shaw was in the *playing XI*")
full(C + "ball_replay.mp4", b("c4_confidence"), 2.0, dim=0.4)
head(["THE CONFIDENCE", "WASN'T THERE"], b("c4_confidence", 0.1), until("c4_confidence", 0.1), "left", 120, accent={1: "#ff5a5f"}, z=40)
C_("c4_confidence", "But the *confidence* that got him here was missing")
full(C + "starc_bowled.mp4", b("c4_scores"), 1.3)
full(C + "cummins_cele.mp4", b("c4_scores", 1.3), until("c4_scores", 1.3) + 0.1)
tickets([("1ST INNINGS", "SHAW 0"), ("2ND INNINGS", "SHAW 4")], b("c4_scores", 0.1), until("c4_scores", 0.1) + 2.4, "left", gap=1.2, y=300,
        stamps=["BOWLED", "BOWLED"])
C_("c4_scores", "First innings: *0*. Second innings: *4*.")
full(C + "stumps_slowmo.mp4", b("c4_36"), 1.4)
full(C + "bat_stumps.mp4", b("c4_36", 1.4), 1.1)
space(b("c4_36", 2.5), until("c4_36", 2.5))
bars([4, 9, 2, 0, 4, 0, 8, 4, 0, 4, 1], b("c4_36", 2.6), until("c4_36", 2.6),
     ["SHAW", "AGARWAL", "BUMRAH", "PUJARA", "KOHLI", "RAHANE", "VIHARI", "SAHA", "ASHWIN", "UMESH", "SHAMI"], hi=0,
     title="INDIA, 2ND INNINGS · ADELAIDE 2020")
glow("36", b("c4_36", 6.6), until("c4_36", 6.6), "right", 200, label="ALL OUT", y=120)
C_("c4_36", "Bowled both times. Then: India *all out for 36*.")
browser(BR + "rec_adelaide_36.webm", b("c4_lowest"), until("c4_lowest"), "right", maxw=1000, media_start=2.4)
head(["INDIA'S", "LOWEST-EVER", "TEST TOTAL"], b("c4_lowest", 0.1), until("c4_lowest", 0.1), "left", 100, accent={1: "#ff5a5f"})
C_("c4_lowest", "India's *lowest-ever* Test total")
full(C + "starc_huddle.mp4", b("c4_changes"), until("c4_changes"), dim=0.3)
chips([("CHANGES WERE MADE", "")], b("c4_changes", 0.4), until("c4_changes", 0.4), "left", y=700)
C_("c4_changes", "After the defeat, *changes* were made")
full(C + "shaw_walks.mp4" if False else C + "starc_highfive.mp4", b("c4_never"), 1.6, dim=0.2)
head(["HE NEVER PLAYED", "ANOTHER TEST", "FOR INDIA"], b("c4_never", 1.6), until("c4_never", 1.6), "center", 120, accent={2: "#ff5a5f"})
C_("c4_never", "Dropped. He *never played another Test* for India.")
num("134", b("c4_134"), until("c4_134"), "left", 260, label="ON DEBUT", y=300)
card(C + "starc_roar.mp4", b("c4_134"), until("c4_134"), "right", maxw=900)
C_("c4_socho", "Think about it…")
C_("c4_134", "134 on debut — called *India's next Sachin*")
full(C + "cummins_roar.mp4", b("c4_career"), until("c4_career") + blen("c4_stopped"), dim=0.55)
num("5", b("c4_career"), until("c4_career") + blen("c4_stopped"), "center", 340, label="TESTS. THEN IT STOPPED.", color="#ff5a5f", z=40)
C_("c4_career", "…and his Test career stopped after *5* Tests", end=("c4_stopped", -0.01))
head(["OVER?"], b("c4_notover"), 2.4, "center", 220)
head(["NOT AT ALL."], b("c4_notover", 2.4), until("c4_notover", 2.4) - 0.2, "center", 180, accent=(0,))
C_("c4_notover", "Was it over? *Not at all.* He proved it in domestic cricket.")

# ---------------------------------------------------------------- 05 THE COMEBACKS
subscribe_card(b("mid_sub", 0.2), until("mid_sub", 0.2) - 0.3)
C_("mid_sub", "Enjoy untold cricket stories? *Subscribe* to TheCricketLounge")
roadmap(6, round(BEAT["mid_sub"][1] + 0.05, 2), 2.4, title="05 · THE COMEBACKS")
card(P + "mumbai_blue_a.jpg", b("c5_vht"), until("c5_vht"), "right", maxw=720, maxh=680, label="MUMBAI", focus="50% 25%")
head(["VIJAY HAZARE", "TROPHY", "2020-21"], b("c5_vht", 0.1), until("c5_vht", 0.1), "left", 110, accent=(2,))
C_("c5_vht", "Vijay Hazare 2020-21, for *Mumbai*")
space(b("c5_827"), until("c5_827"))
glow("827", b("c5_827"), until("c5_827"), "center", 320, label="RUNS · ONE TOURNAMENT")
C_("c5_827", "*827* runs in one tournament")
cutword(CO + "vht_227.png", "227*", b("c5_227"), until("c5_227"), "left", wside="right", tone="gold", sub="AN UNFORGETTABLE INNINGS")
C_("c5_227", "Including an unforgettable *227 not out*")
browser(BR + "ss_shaw_227.png", b("c5_title"), until("c5_title"), "right", maxw=980)
head(["MUMBAI", "WIN THE TITLE"], b("c5_title", 0.1), until("c5_title", 0.1), "left", 120, accent=(1,))
C_("c5_title", "He drove Mumbai to the *title*")
card(P + "mumbai_blue_sweep.jpg", b("c5_notfinished"), until("c5_notfinished"), "right", maxw=760, focus="50% 25%")
head(["NOT FINISHED", "YET."], b("c5_notfinished"), until("c5_notfinished"), "left", 120, accent=(1,))
C_("c5_notfinished", "Prithvi was *not finished*")
cutword(CO + "northants_helmet.png", "244", b("c5_northants"), 4.4, "right", tone="navy", sub="NORTHAMPTONSHIRE · 2023")
space(b("c5_northants", 4.4), until("c5_northants", 4.4))
glow("244", b("c5_northants", 4.4), until("c5_northants", 4.4), "left", 260, label="RUNS", y=300)
chips(["OFF 153 BALLS", ("COUNTY CRICKET, ENGLAND", "yellow")], b("c5_northants", 4.8), until("c5_northants", 4.8), "right", gap=0.8)
C_("c5_northants", "2023, Northamptonshire: *244* off *153* balls")
card(P + "northants_244.jpg", b("c5_remember"), until("c5_remember"), "center", maxw=1100, maxh=680, focus="50% 25%")
C_("c5_remember", "The world *remembered* his talent")
card(P + "mumbai_blue_pull.jpg", b("c5_unstoppable"), until("c5_unstoppable"), "right", maxw=760, focus="50% 25%")
head(["WHEN SHAW", "GOT GOING…"], b("c5_unstoppable", 0.1), 2.6, "left", 120)
head(["FLASHES OF", "BRILLIANCE"], b("c5_unstoppable", 2.8), until("c5_unstoppable", 2.8), "left", 120, accent=(1,))
C_("c5_unstoppable", "When he got going, he looked *unstoppable* — in flashes")
head(["NOT CONVERTED INTO", "CONSISTENT SUCCESS"], b("c5_convert"), until("c5_convert"), "center", 110, accent={1: "#ff5a5f"})
C_("c5_convert", "Never turned into *consistent* international success")
space(b("c5_controversy"), until("c5_controversy") - 0.1, tone="red")
head(["AND THEN:", "CONTROVERSIES"], b("c5_controversy"), until("c5_controversy") - 0.2, "center", 140, accent={1: "#ff8a8d"})
C_("c5_controversy", "And *controversies* began to gather around him")

# ---------------------------------------------------------------- 06 THE CONTROVERSY
# Every line has a picture behind it. AI scenes show places/objects only (no people), and are tagged AI-GENERATED;
# allegations are labelled as allegations.
roadmap(8, round(BEAT["c5_controversy"][1] + 0.05, 2), 2.4, title="06 · THE CONTROVERSY")
full(A + "ai_hotel_night.jpg", b("c6_feb2023"), until("c6_feb2023"), dim=0.3, ai=True)
datecard("FEB 2023", "MUMBAI", b("c6_feb2023", 1.2), until("c6_feb2023", 1.2), sub="dinner with friends at a hotel")
card(P + "shaw_bmw.jpg", b("c6_feb2023", 0.4), until("c6_feb2023", 0.4), "right", maxw=520, maxh=640, label="PRITHVI SHAW", focus="50% 30%")
C_("c6_feb2023", "Feb 2023, Mumbai · dinner with friends")
browser(BR + "rec_incident.webm", b("c6_selfies"), until("c6_selfies") + blen("c6_refused"), "right", maxw=980, media_start=0.6)
head(["SELFIES.", "VIDEOS."], b("c6_selfies", 0.1), until("c6_selfies", 0.1), "left", 150, accent=(1,), kicker="SOME PEOPLE WANTED", kcolor=CYAN)
C_("c6_selfies", "Some people wanted *selfies* and videos")
chips([("SELFIES: GIVEN ✓", ""), ("REPEATED REQUESTS → SAID NO", "red")], b("c6_refused", 0.3), until("c6_refused", 0.3), "left", gap=2.2, y=380)
C_("c6_refused", "Per his friend's complaint: he obliged, then *said no*")
full(A + "ai_bat_road.jpg", b("c6_argument"), until("c6_argument"), dim=0.45, ai=True)
chips(["AN ARGUMENT", ("THE HOTEL ASKED THEM TO LEAVE", "yellow")], b("c6_argument"), until("c6_argument"), "left", gap=1.4, y=380)
C_("c6_argument", "An argument. The hotel asked them to *leave*.")
card(P + "viral_split.jpg", b("c6_notover"), until("c6_notover") + 0.3, "right", maxw=1000, label="VIRAL VIDEO", sub="that night")
head(["IT DIDN'T", "END THERE"], b("c6_notover", 0.1), until("c6_notover", 0.1), "left", 120, accent=(1,))
C_("c6_notover", "It didn't *end* there")
full(A + "ai_windshield.jpg", b("c6_attack"), until("c6_attack"), dim=0.35, ai=True, push=(1.0, 1.12))
glass("POLICE COMPLAINT · ALLEGATIONS", ["Car <b>attacked with a baseball bat</b>", "Friend's car <b>windshield damaged</b>",
                                         "<b>Extortion & threats</b> alleged"], b("c6_attack", 0.2), until("c6_attack", 0.2), "left", badge="ALLEGED", w=900)
C_("c6_attack", "Per the police complaint: the car was *attacked*; extortion alleged")
full(A + "ai_police_station.jpg", b("c6_arrest"), until("c6_arrest"), dim=0.4, ai=True)
chips([("SAPNA GILL & OTHERS: ARRESTED", ""), ("GILL: COUNTER-ALLEGATIONS", "red")], b("c6_arrest", 0.2), until("c6_arrest", 0.2),
      "left", gap=2.6, y=400)
card(P + "viral_bat.jpg", b("c6_arrest"), until("c6_arrest"), "right", maxw=600, maxh=640, label="VIRAL VIDEO", sub="Feb 2023")
C_("c6_arrest", "Arrests followed — and *counter-allegations*")
full(A + "ai_courtroom.jpg", b("c6_june"), until("c6_june"), dim=0.4, ai=True)
datecard("JUNE 2023", "POLICE TO COURT", b("c6_june"), 2.6)
head(["MOLESTATION", "ALLEGATIONS:", "FOUND FALSE"], b("c6_june", 2.6), until("c6_june", 2.6), "left", 100, accent=(2,), y=300)
card(P + "ndtv_false.jpg", b("c6_june", 2.4), until("c6_june", 2.4) + 2.0, "right", maxw=560, maxh=560, focus="50% 0%")
C_("c6_june", "June 2023: police told the court the allegations were *false*")
full(A + "ai_cctv.jpg", b("c6_cctv"), until("c6_cctv"), dim=0.4, ai=True)
chips(["CCTV FOOTAGE", "WITNESS STATEMENTS"], b("c6_cctv", 2.0), 2.2, "left", gap=0.6, y=420)
head(["SAYING NO TO SELFIES", "WAS NOT A MISTAKE ✓"], b("c6_cctv", 4.4), until("c6_cctv", 4.4), "left", 110, accent={1: "#3ddc84"}, y=360)
C_("c6_cctv", "Saying no to selfies was *not a mistake*")
quote("He had every right to say no.", "THE CRICKET LOUNGE", b("c6_sayno"), until("c6_sayno"), size=96, maxw=1300)
C_("c6_sayno", "He had every *right* to say no")
head(["ANOTHER", "CONTROVERSY", "AROUND HIS NAME"], b("c6_struggle"), until("c6_struggle"), "center", 110, accent=(1,))
C_("c6_struggle", "But it added another *distraction* while he was fighting for his place")
head(["THE BIGGEST QUESTION:", "PERFORMANCE &", "PROFESSIONALISM"], b("c6_distraction"), until("c6_distraction") - 0.2, "center", 110, accent=(1, 2))
C_("c6_distraction", "The real question: *performance* and *professionalism*")

# ---------------------------------------------------------------- 07 THE FALL
roadmap(9, round(BEAT["c6_distraction"][1] + 0.05, 2), 2.4, title="07 · THE FALL")
card(P + "mumbai_ranji_ton.jpg", b("c7_oct2024"), until("c7_oct2024"), "right", maxw=860, focus="50% 25%")
head(["OCT 2024", "DROPPED FROM", "MUMBAI'S RANJI SQUAD"], b("c7_oct2024", 0.1), until("c7_oct2024", 0.1), "left", 88, accent={0: CYAN, 2: "#ff5a5f"})
C_("c7_oct2024", "Oct 2024: dropped from Mumbai's *Ranji* squad")
chips([("OFFICIALLY: A BREAK", ""), ("REPORTS: FITNESS & DISCIPLINE CONCERNS", "red")], b("c7_break", 0.2), until("c7_break", 0.2), "center", gap=2.0)
C_("c7_break", "Officially a *break* — reports cited fitness and discipline")
full(A + "ai_gavel.jpg", b("c7_auction"), until("c7_auction"), dim=0.35, ai=True)
datecard("NOV 2024", "IPL MEGA AUCTION", b("c7_auction", 0.2), 3.6)
head(["ONCE, TEAMS", "BID FOR HIM"], b("c7_auction", 3.9), until("c7_auction", 3.9), "left", 120, accent=(1,), y=420)
C_("c7_auction", "Once, franchises *bid* for him. This time…")
card(P + "auction_unsold_crop.jpg", b("c7_nobody"), until("c7_nobody") + 0.4, "center", maxw=700, maxh=700)
C_("c7_nobody", "*Unsold*. No franchise picked him.")
space(b("c7_mca"), until("c7_mca") + blen("c7_10fielders") + blen("c7_harsh") + blen("c7_enough") + 0.5)
glass("MCA OFFICIAL TO PTI · DEC 2024", ["Concerns over <b>fitness</b>", "Concerns over <b>fielding standards</b>"], b("c7_mca", 0.4),
      until("c7_mca", 0.4), "center", w=980)
C_("c7_mca", "Dec 2024: an MCA official raised *fitness* and *fielding* concerns")
quote("10 fielders ke saath cricket nahi khela ja sakta.", "MCA OFFICIAL, TO PTI", b("c7_10fielders"), until("c7_10fielders"), size=72, maxw=1300)
C_("c7_10fielders", "“You can't play cricket with *10 fielders*”")
head(["A HARSH", "STATEMENT"], b("c7_harsh"), until("c7_harsh"), "center", 150, accent=(1,))
C_("c7_harsh", "A *harsh* statement")
head(["IS BATTING TALENT", "ENOUGH?"], b("c7_enough"), until("c7_enough"), "center", 130, accent=(1,))
C_("c7_enough", "Is batting talent *enough*?")
full(A + "ai_fitness.jpg", b("c7_modern"), until("c7_modern"), dim=0.55, ai=True)
depthlist(["RUNS", "FITNESS", "FIELDING", "DISCIPLINE", "CONSISTENCY"], b("c7_modern"), until("c7_modern"),
          [b("c7_modern", 0.2), b("c7_modern", 2.6), b("c7_modern", 3.6), b("c7_modern", 4.6), b("c7_modern", 5.8)])
C_("c7_modern", "Modern cricket wants runs *and* fitness, fielding, discipline, consistency")
space(b("c7_halffacts"), until("c7_halffacts"))
quote("Full opinions, with half facts.", "PRITHVI SHAW · ON SOCIAL MEDIA", b("c7_halffacts"), until("c7_halffacts"), size=90, maxw=1300)
C_("c7_halffacts", "Shaw's reply: “Full opinions, with *half facts*”")
head(["ANSWERS COME FROM", "PERFORMANCE"], b("c7_performance"), until("c7_performance"), "center", 120, accent=(1,))
C_("c7_performance", "In cricket, the answer has to come from *performance*")
head(["WAS HIS CAREER", "OVER?"], b("c7_over"), until("c7_over") - 0.2, "center", 140, accent={1: "#ff5a5f"})
C_("c7_over", "So was his career *over*?")

# ---------------------------------------------------------------- 08 THE ROAD BACK
roadmap(10, round(BEAT["c7_over"][1] + 0.05, 2), 2.4, title="08 · THE ROAD BACK")
vs("MUMBAI", "MAHARASHTRA", b("c8_maharashtra"), 3.6, ltag="LEFT", rtag="JOINED · 2025", lcol="#fff", rcol=CYAN, t2=b("c8_maharashtra", 1.2))
card(P + "maharashtra_bat.jpg", b("c8_maharashtra", 3.6), until("c8_maharashtra", 3.6), "right", maxw=860, focus="50% 30%")
chips(["A NEW TEAM", "A NEW ENVIRONMENT", ("ANOTHER CHANCE", "yellow")], b("c8_maharashtra", 3.9), until("c8_maharashtra", 3.9), "left", gap=1.2)
C_("c8_maharashtra", "2025: Mumbai → *Maharashtra*. A fresh start.")
browser(BR + "rec_shaw_maharashtra.webm", b("c8_simple"), until("c8_simple"), "right", maxw=980, media_start=1.0)
head(["A COMEBACK", "ISN'T SIMPLE"], b("c8_simple", 0.1), until("c8_simple", 0.1), "left", 120, accent=(1,))
C_("c8_simple", "But a comeback in India isn't *simple*")
head(["ONE GOOD INNINGS", "ISN'T ENOUGH"], b("c8_national"), until("c8_national") + blen("c8_runs"), "center", 120, accent={1: "#ff5a5f"})
C_("c8_national", "One good innings *isn't enough*", end=("c8_runs", -0.01))
space(b("c8_fitness"), until("c8_fitness"))
depthlist(["REGULAR RUNS", "PROVE THE FITNESS", "LONG-TERM COMMITMENT"], b("c8_fitness"), until("c8_fitness"),
          [b("c8_fitness", 0.1), b("c8_fitness", 1.4), b("c8_fitness", 3.6)])
C_("c8_fitness", "Regular runs. *Fitness*. Long-term *commitment*.")
full(A + "ai_road.jpg", b("c8_dream"), until("c8_dream") - 0.1, dim=0.35, ai=True)
head(["THE DREAM", "IS ALIVE"], b("c8_dream", 0.2), 3.0, "left", 140, accent=(1,), y=420)
head(["PERFORMANCE", "COVERS THE DISTANCE"], b("c8_dream", 3.3), until("c8_dream", 3.3) - 0.3, "left", 110, accent=(0,), y=420)
C_("c8_dream", "The dream is alive — only *performance* closes the gap")

# ---------------------------------------------------------------- FINAL
roadmap(10, round(BEAT["c8_dream"][1] + 0.05, 2), round(until("f_what") + 1.2, 2), title="WHAT REALLY HAPPENED?")
space(b("f_questions"), until("f_questions") + blen("f_fitness") + 0.2)
depthlist(["INJURIES?", "THE SUSPENSION?", "ADELAIDE?", "FITNESS · DISCIPLINE · CONSISTENCY?"], b("f_questions"),
          round(until("f_questions") + blen("f_fitness"), 2),
          [b("f_questions", 0.1), b("f_questions", 2.0), b("f_questions", 4.2), b("f_fitness", 0.3)])
C_("f_questions", "Injuries? The suspension? *Adelaide*?")
C_("f_fitness", "Or questions over fitness, discipline and *consistency*?")
head(["NOT JUST A", "STORY OF FAILURE"], b("f_failure", 2.4), until("f_failure", 2.4), "center", 130, accent=(1,), kicker="MAYBE ALL OF IT", kcolor=CYAN)
C_("f_failure", "Maybe all of it. But it's *not just a story of failure*.")
space(b("f_control"), until("f_control") + blen("f_missed") + blen("f_expect") + 0.3)
chips(["SOME SETBACKS: OUT OF HIS CONTROL", ("SOME CHANCES: MISSED", "red"), ("SOME EXPECTATIONS: TOO EARLY", "yellow")],
      b("f_control"), round(until("f_control") + blen("f_missed") + blen("f_expect"), 2), "center", gap=2.3)
C_("f_control", "Some setbacks were beyond his *control*…")
C_("f_missed", "…some chances he *missed*…")
C_("f_expect", "…some expectations came *too early*")
glow("18", b("f_at18"), until("f_at18"), "left", 300, label="“THE NEXT SACHIN”", y=260)
head(["THAT'S A LOT", "TO CARRY"], b("f_at18", 2.4), until("f_at18", 2.4), "right", 120, accent=(1,))
C_("f_at18", "At *18*, called the next Sachin. That's a lot to carry.")
space(b("f_talent"), until("f_talent"))
depthlist(["PATIENCE", "DISCIPLINE", "CONSISTENCY"], b("f_talent"), until("f_talent"),
          [b("f_talent", 3.6), b("f_talent", 4.6), b("f_talent", 5.6)])
C_("f_talent", "Now: *patience*, *discipline*, *consistency*")
full(A + "ai_door.jpg", b("f_door"), until("f_door"), dim=0.35, ai=True)
head(["TALENT OPENS", "THE DOOR."], b("f_door", 0.1), 1.9, "left", 120, accent=(1,), y=420)
head(["CONSISTENCY", "KEEPS YOU INSIDE."], b("f_door", 2.0), until("f_door", 2.0), "left", 120, accent=(0,), y=420)
C_("f_door", "Talent opens the door. *Consistency* keeps you inside.")
browser(BR + "ss_shaw_infobox.png", b("f_young"), until("f_young"), "right", maxw=720, maxh=560, box=True)
head(["STILL YOUNG", "ENOUGH"], b("f_young", 0.1), until("f_young", 0.1), "left", 140, accent=(1,))
C_("f_young", "He's still *young enough* for a comeback")
head(["BACK TO THE", "INDIA JERSEY?"], b("f_sawaal"), until("f_sawaal"), "center", 130, accent=(1,))
C_("f_sawaal", "Can he take his talent back to the *India jersey*?")
head(["OR THE SUPERSTAR", "WHO NEVER WAS?"], b("f_history"), round(until("f_history") + blen("f_superstar"), 2), "center", 130, accent={1: "#ff5a5f"})
C_("f_history", "Or will history remember the superstar *who never was*?", end=("f_superstar", -0.01))
cutword(CO + "redball_14.png", "ONE MORE?", b("f_think"), round(until("f_think") + 1.0, 2), "center", tone="navy", sub="DOES HE DESERVE ONE MORE CHANCE?")
C_("f_think", "Does Prithvi Shaw deserve *one more chance* in Team India?")
C_("f_comment", "*Comment* karke zaroor batao")
head(["EVERY CRICKETER", "HAS A STORY"], b("f_story", 0.1), until("f_story", 0.1) - 0.2, "center", 130, accent=(1,), sub="And some stories deserve to be told.")
C_("f_story", "Every cricketer has a *story*")
endcard(round(BEAT["f_story"][1] + 0.2, 2), round(TOTAL - BEAT["f_story"][1] - 0.2, 2))

# ---------------------------------------------------------------- Shaw batting behind text about his batting
BG_OK = ["o_status", "c1_talent", "c1_youngest", "c1_dominate", "c1_staying", "c4_xi", "c4_confidence", "c4_notover",
         "c5_convert", "c7_enough", "c7_performance", "f_sawaal", "f_history", "f_superstar", "c1_setback", "c3_u19mates"]
POOL = [{"file": C + f"nz_bat_{k:02d}.mp4", "dur": d} for k, d in
        [(2, 5.6), (3, 6.0), (4, 3.8), (5, 3.8), (6, 5.6), (7, 3.8), (8, 4.6), (9, 3.8), (10, 5.6), (11, 5.6), (12, 5.6), (13, 5.6), (14, 7.0)]]


def gaps_in(t0, t1):
    pieces = [(t0, t1)]
    for c0, c1 in COVER:
        nxt = []
        for p0, p1 in pieces:
            if c1 <= p0 or c0 >= p1:
                nxt.append((p0, p1))
                continue
            if c0 > p0:
                nxt.append((p0, c0))
            if c1 < p1:
                nxt.append((c1, p1))
        pieces = nxt
    return [(round(a, 2), round(e, 2)) for a, e in pieces if e - a >= 0.9]


_pk = [0]
for beat in sorted(BG_OK, key=lambda k: BEAT[k][0]):
    k = ORDER.index(beat)
    t1 = BEAT[ORDER[k + 1]][0] if k + 1 < len(ORDER) else TOTAL
    for g0, g1 in gaps_in(BEAT[beat][0], t1):
        t = g0
        while g1 - t >= 0.9 and _pk[0] < len(POOL):
            shot = POOL[_pk[0]]
            _pk[0] += 1
            d = round(min(shot["dur"], g1 - t), 2)
            full(shot["file"], round(t, 2), d, dim=0.6, z=3, quiet=True, push=(1.06, 1.0))
            t += d
print(f"batting background shots used: {_pk[0]} of {len(POOL)}")

# everything else that is still bare gets the navy space stage (never flat black)
for g0, g1 in gaps_in(0.0, TOTAL):
    space(g0, round(g1 - g0, 2), z=2)
