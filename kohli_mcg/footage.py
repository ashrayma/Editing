"""The real match footage this film needs, by id. Drop each clip in footage/user/<id>.mp4 (any resolution/length,
the useful moment first) and re-run make_film.sh. Until then a labelled placeholder slate stands in for it.
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

FOOTAGE = {
    # moments the highlights you sent don't cover (15-minute version)
    "N01": ("England 2014: Kohli edging Anderson / walking back", "line 8"),
    "N02": ("IPL 2016: Kohli hundred celebration for RCB", "line 10"),
    "N03": ("Mohali 2016 WT20: Kohli 82* vs Australia, finishing the chase", "line 11"),
    "N04": ("England 2018: Edgbaston hundred, Kohli kisses his ring", "line 12"),
    "N05": ("Adelaide Dec 2020: Kohli run out for 74 / India 36 all out scoreboard", "line 20"),
    "N06": ("Kohli captaincy press conference 2021-22", "lines 22, 26"),
    "N07": ("IPL 2022: Kohli out first ball (golden duck)", "line 28"),
    "N08": ("Kohli and MS Dhoni together", "line 31"),
    "N09": ("MCG 2022 national anthem, Rohit emotional", "line 48"),
    "N10": ("MCG 2022: KL Rahul b Naseem (inside edge)", "line 55"),
    "N11": ("MCG 2022: Rohit c Iftikhar b Rauf", "line 56"),
    "N12": ("MCG 2022: Suryakumar c Rizwan b Rauf", "line 57"),
    "N13": ("MCG 2022: Axar Patel run out", "line 58"),
    "N14": ("MCG 2022: Kohli and Hardik batting together (overs 7-17)", "lines 64-65"),
    "N15": ("MCG 2022: Rohit lifts Kohli on his shoulders", "line 94"),
    "N16": ("MCG 2022: Kohli post-match interview", "line 96"),
    "N17": ("Hobart 2012: Kohli vs Malinga (for the next-episode tease)", "line 100"),
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


# ----------------------------------------------------------------------------- the user's footage, cut by moment
# source files live in footage/user/src/ (not in git). (source, start, duration[, crop]) in seconds.
SRC = {"m": "mcg_recap.mp4", "d": "dubai2021.mp4", "p": "pak_innings_vertical.mp4", "b": "babar_lbw.mp4"}
VCROP = "crop=720:405:0:437"   # the 16:9 picture inside the vertical upload
LIB = {
    # MCG 2022: ICC recap of the last three overs
    "m_aerial": ("m", 0.0, 0.9), "m_kohli_hit18": ("m", 6.0, 2.0), "m_flags": ("m", 8.0, 4.0),
    "m_shaheen": ("m", 12.0, 3.0), "m_babar_clap": ("m", 15.0, 1.2), "m_kohli_bat16": ("m", 16.0, 2.0),
    "m_kohli_walk18": ("m", 18.0, 2.0), "m_rohit_dugout": ("m", 20.0, 1.2), "m_fan_pray": ("m", 21.0, 3.0),
    "m_six1_close": ("m", 24.0, 4.0), "m_six1_wide": ("m", 28.0, 2.0), "m_rauf_watch": ("m", 30.0, 2.0),
    "m_crowd_up": ("m", 32.0, 3.0), "m_six2": ("m", 35.0, 3.0), "m_lights": ("m", 38.0, 4.0),
    "m_kohli_close": ("m", 42.0, 3.0), "m_fans_flag": ("m", 47.0, 2.0), "m_kohli_close2": ("m", 49.0, 1.2),
    "m_crowd_flags2": ("m", 50.0, 3.0), "m_nawaz": ("m", 53.0, 2.0), "m_hardik_out": ("m", 58.0, 5.0),
    "m_babar_catch": ("m", 64.0, 3.0), "m_hardik_walk": ("m", 67.0, 3.0), "m_runs": ("m", 70.0, 12.0),
    "m_fan_pray2": ("m", 83.0, 1.2), "m_noball_six": ("m", 84.0, 6.0), "m_umpire_nb": ("m", 91.0, 2.2),
    "m_protest": ("m", 93.0, 3.0), "m_kohli_look": ("m", 96.0, 1.2), "m_crowd_nb": ("m", 97.0, 5.0),
    "m_wide1": ("m", 102.0, 3.0), "m_rohit_dugout2": ("m", 105.0, 1.2), "m_freehit": ("m", 110.0, 8.0),
    "m_kohli_umpire": ("m", 118.0, 2.0), "m_kohli_back": ("m", 120.0, 2.0), "m_pak_fans": ("m", 122.0, 3.0),
    "m_dk_stumped": ("m", 125.0, 3.0), "m_scoreboard_out": ("m", 129.0, 2.0), "m_dk_walk": ("m", 131.0, 4.0),
    "m_ashwin_in": ("m", 135.0, 3.0), "m_ashwin_wide": ("m", 141.0, 4.0), "m_nawaz_head": ("m", 145.0, 1.2),
    "m_fans_scream": ("m", 146.0, 7.0), "m_ashwin_ready": ("m", 155.0, 3.0), "m_win_shot": ("m", 158.0, 7.0),
    "m_fans_win": ("m", 165.0, 3.0), "m_celebrate": ("m", 168.0, 3.0), "m_kohli_knees": ("m", 171.0, 3.0),
    "m_india_win": ("m", 174.0, 3.0), "m_kohli_roar": ("m", 177.0, 2.9),
    # Dubai 2021
    "d_field": ("d", 15.0, 5.0), "d_rizwan": ("d", 55.0, 3.0), "d_babar": ("d", 65.0, 3.0),
    "d_pak_fans": ("d", 70.0, 3.0), "d_babar_shot": ("d", 145.0, 3.0), "d_shami": ("d", 210.0, 3.0),
    "d_pak_win": ("d", 258.0, 5.0), "d_kohli_congrats": ("d", 263.0, 8.0),
    # MCG 2022, Pakistan's innings (vertical upload, 16:9 picture cropped out)
    "p_crowd": ("p", 10.0, 3.0, VCROP), "p_babar_out": ("p", 15.0, 13.0, VCROP), "p_huddle": ("p", 38.0, 4.0, VCROP),
    "p_babar_walk": ("p", 55.0, 3.0, VCROP), "p_rohit": ("p", 80.0, 2.0, VCROP), "p_dive": ("p", 88.0, 8.0, VCROP),
    "p_rizwan_out": ("p", 100.0, 12.0, VCROP), "p_rizwan_walk": ("p", 118.0, 4.0, VCROP),
    "p_iftikhar_six": ("p", 128.0, 5.0, VCROP), "p_shami": ("p", 168.0, 5.0, VCROP), "p_iftikhar_walk": ("p", 174.0, 4.0, VCROP),
    "p_pak_dugout": ("p", 204.0, 3.0, VCROP), "p_masood50": ("p", 208.0, 5.0, VCROP), "p_hardik": ("p", 228.0, 8.0, VCROP),
    "p_scorecard": ("p", 268.0, 7.0, VCROP),
    # Babar lbw, 720p
    "b_arshdeep": ("b", 0.0, 9.0),
}


def lib(cid, slow=False):
    """Cut one named moment to 1080p30 (once). slow=True plays it at half speed, frame-blended."""
    src, start, dur, *crop = LIB[cid]
    name = cid + ("_slow" if slow else "")
    out = os.path.join(HERE, "footage", "clips", name + ".mp4")
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        vf = (crop[0] + "," if crop else "") + "scale=1920:1080:flags=lanczos,setsar=1,fps=30"
        if slow:
            vf += ",setpts=2.0*PTS,minterpolate=fps=30:mi_mode=blend"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i",
                        os.path.join(HERE, "footage", "user", "src", SRC[src]), "-t", str(dur), "-an", "-vf", vf,
                        "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", out], check=True)
    return os.path.relpath(out, HERE)
