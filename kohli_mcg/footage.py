"""The real match footage this film needs, by id. Drop each clip in footage/user/<id>.mp4 (any resolution/length,
the useful moment first) and re-run make_film.sh. Until then a labelled placeholder slate stands in for it.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

FOOTAGE = {
    "F01": ("Rauf runs in, over 19 (Kohli at the non-striker/striker end)", "cold open, rauf_over"),
    "F02": ("Haris Rauf close-up (face / celebrating a wicket)", "open_rauf"),
    "F03": ("Kohli's 70th hundred celebration, Kolkata pink-ball Test, Nov 2019", "drought_70"),
    "F04": ("Pakistan beat India by 10 wickets, Dubai T20 WC 2021 (winning moment)", "drought_capt"),
    "F05": ("Kohli dismissed / walking back dejected, any match 2020-22", "drought_capt, drought_voices"),
    "F06": ("Kohli's 71st hundred, 122* vs Afghanistan, Dubai, 8 Sep 2022 (bat raised)", "comeback_71"),
    "F07": ("MCG crowd / national anthems, 23 Oct 2022", "mcg"),
    "F08": ("Arshdeep traps Babar lbw, first ball", "pak_innings"),
    "F09": ("Iftikhar / Shan Masood hitting (Pakistan innings)", "pak_innings"),
    "F10": ("KL Rahul out (b Naseem)", "collapse"),
    "F11": ("Rohit Sharma out (c Iftikhar b Rauf)", "collapse"),
    "F12": ("Suryakumar out (c Rizwan b Rauf)", "collapse"),
    "F13": ("Axar Patel run out", "collapse"),
    "F14": ("Kohli and Hardik batting together / mid-pitch chat", "silence, hardik, asking_rate"),
    "F15": ("Shaheen's 18th over, boundaries", "eighteen"),
    "F16": ("THE straight six off Rauf, 19.5, live + replay", "six_one, six_one_why"),
    "F17": ("The second six off Rauf, 19.6, over fine leg", "six_two"),
    "F18": ("Nawaz's last over: Hardik caught by Babar", "nawaz"),
    "F19": ("No-ball full toss hit for six, umpire signals no-ball", "no_ball"),
    "F20": ("Free hit: Kohli bowled, ball runs to third man, 3 byes", "free_hit"),
    "F21": ("Dinesh Karthik stumped", "dk_out"),
    "F22": ("Ashwin leaves the wide, then lifts it over mid-off: winning run", "ashwin"),
    "F23": ("Kohli punches the ground / roars", "punch, close"),
    "F24": ("Rohit lifts Kohli on his shoulders", "punch"),
    "F25": ("Kohli's post-match interview (Mohali comment)", "own_words"),
}


def clip(fid, secs=14):
    """Path (relative to HERE) of the clip to use: the user's footage, normalised, or a labelled slate."""
    user = os.path.join(HERE, "footage", "user", f"{fid}.mp4")
    if os.path.exists(user):
        out = os.path.join(HERE, "footage", "clips", f"{fid}.mp4")
        if not os.path.exists(out) or os.path.getmtime(user) > os.path.getmtime(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", user, "-an", "-vf",
                            "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=30",
                            "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", out], check=True)
        return os.path.relpath(out, HERE)
    out = os.path.join(HERE, "footage", "placeholders", f"{fid}.mp4")
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        desc = FOOTAGE[fid][0].replace(":", "\\:").replace("'", "")
        vf = (f"drawbox=x=0:y=0:w=iw:h=ih:color=0x16161a:t=fill,"
              f"drawbox=x='mod(t*120,1280)-200':y=0:w=200:h=720:color=0x1e1e23:t=fill,"
              f"drawtext=fontfile={FONT}:text='{fid}':fontcolor=0xFEDE5C:fontsize=120:x=(w-tw)/2:y=210,"
              f"drawtext=fontfile={FONT}:text='{desc}':fontcolor=white:fontsize=30:x=(w-tw)/2:y=380,"
              f"drawtext=fontfile={FONT}:text='MATCH FOOTAGE NEEDED':fontcolor=0x8e8e96:fontsize=24:x=(w-tw)/2:y=440")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1280x720:r=30:d={secs}",
                        "-vf", vf, "-c:v", "libx264", "-crf", "24", "-pix_fmt", "yuv420p", out], check=True)
    return os.path.relpath(out, HERE)


def ai(name):
    """AI image: the full-size file once downloaded to assets/ai/, else the small Canva preview."""
    full = os.path.join("assets", "ai", f"{name}.png")
    return full if os.path.exists(os.path.join(HERE, full)) else os.path.join("assets", "ai", "_preview", f"{name}.png")
