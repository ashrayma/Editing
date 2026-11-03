"""Edit decision list for the voice note: which stretches of the raw take make the final narration.

Times are seconds in the raw file. Fumbles and false starts left out: 26.4-35.0 (first try at the 2010
line), 49.4-53.7 (two false starts on 2014), 57.6-60.5 (first "he smashed..." stopped mid-line),
70.4-72.4 (false start on 5000), 87.0-88.7 (false start on the ending).
"""
RAW = "vo_raw/voice_261103_195425.m4a"

PIECES = [
    {"id": "hook", "src": (2.20, 7.45), "say": "twenty five balls eighty seven runs and the guy who did it never even won an orange cap"},
    {"id": "not", "src": (8.12, 9.10), "say": "he's not"},
    {"id": "why", "src": (9.45, 14.35), "say": "ipl's top run scorer either so why does everyone call suresh raina mister ipl"},
    {"id": "simple", "src": (15.22, 17.58), "say": "simple the bigger the match the better he got"},
    {"id": "playoffs", "src": (18.02, 25.80), "say": "in the playoffs alone he scored seven hundred fourteen runs in just twenty four innings with seven fifties and nobody has gone past that"},
    {"id": "final", "src": (35.58, 43.80), "say": "go back to the twenty ten final against mumbai csk were in trouble and raina walked in and made fifty seven not out off thirty five balls"},
    {"id": "title", "src": (44.58, 49.05), "say": "that gave chennai their first ever title and he was player of the match"},
    {"id": "q2", "src": (54.80, 57.58), "say": "then came twenty fourteen qualifier two against punjab"},
    {"id": "smash", "src": (61.85, 70.25), "say": "he smashed eighty seven off thirty five balls at a strike rate of three hundred forty eight and took thirty three runs off a single over"},
    {"id": "fivek", "src": (73.42, 77.55), "say": "he was also the first player in ipl history to reach five thousand runs"},
    {"id": "thala", "src": (77.55, 82.55), "say": "and if dhoni was thala raina was chinna thala together they were the heartbeat of chennai"},
    {"id": "cap", "src": (82.90, 86.45), "say": "he never needed the orange cap he just needed a big match"},
    {"id": "end", "src": (89.90, 95.00), "say": "so who's the real mister ipl raina or kohli tell me in the comments and follow"},
]
