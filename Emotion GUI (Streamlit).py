# STREAMLIT EMOTION LOGGER — FINAL VERSION USING BASE64 IMAGE URL ONLY
import streamlit as st
import os
import random
import time
import pandas as pd
import numpy as np
from datetime import timedelta
from streamlit_drawable_canvas import st_canvas
from streamlit_autorefresh import st_autorefresh
from PIL import Image, ImageDraw
import io
import base64

# ---------------- CONFIG ----------------
AUDIO_FOLDER = "song"
BACKGROUND_IMAGE_PATH = "photo.png"
st.set_page_config(layout="wide")
st.title("🎧 Arousal-Valence Emotion Logger (Base64 Canvas + Dots)")

# ---------------- SESSION STATE INIT ----------------
for key, default in {
    "played_songs": [],
    "current_song": None,
    "song_start_time": None,
    "emotions": [],
    "participant_id": "anonymous",
    "logging_enabled": False,
    "logging_start_time": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- HELPERS ----------------
def format_duration(seconds):
    return str(timedelta(seconds=int(seconds)))

def get_quadrant(x, y):
    if x >= 0 and y >= 0:
        return "Green"
    elif x < 0 and y >= 0:
        return "Yellow"
    elif x < 0 and y < 0:
        return "Red"
    elif x >= 0 and y < 0:
        return "Blue"
    return "Unknown"

# ---------------- PARTICIPANT ID ----------------
st.session_state.participant_id = st.text_input("Enter Participant ID:", st.session_state.participant_id)

# ---------------- SONG LOAD ----------------
if not os.path.exists(AUDIO_FOLDER):
    st.error(f"Missing audio folder: {AUDIO_FOLDER}")
    st.stop()

songs = sorted([f for f in os.listdir(AUDIO_FOLDER) if f.endswith((".mp3", ".wav"))])
remaining = list(set(songs) - set(st.session_state.played_songs))

if not st.session_state.current_song and remaining:
    song = random.choice(remaining)
    st.session_state.current_song = song
    st.session_state.song_start_time = time.time()
    st.session_state.logging_enabled = False
    st.session_state.logging_start_time = None
    st.session_state.emotions = []

# ---------------- AUDIO ----------------
if st.session_state.current_song:
    st.markdown(f"### 🎶 Now Playing: `{st.session_state.current_song}`")
    with open(os.path.join(AUDIO_FOLDER, st.session_state.current_song), "rb") as f:
        audio_bytes = f.read()
    st.audio(audio_bytes, format="audio/mp3")
    elapsed = time.time() - st.session_state.song_start_time
    st.success(f"🎵 Playing — Time elapsed: {int(elapsed)}s")

# ---------------- START / STOP LOGGING ----------------
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("▶️ Start Logging"):
        st.session_state.logging_enabled = True
        st.session_state.logging_start_time = time.time()
        st.toast("✅ Logging started!", icon="🟢")
with col2:
    if st.button("⏹ Stop Logging"):
        st.session_state.logging_enabled = False
        st.toast("⏹ Logging stopped.", icon="🔴")
with col3:
    if st.button("🧹 Reset Log"):
        st.session_state.emotions = []
        st.toast("🧽 Emotion log cleared")

# ---------------- TIMER ----------------
if st.session_state.logging_enabled and st.session_state.logging_start_time:
    elapsed = time.time() - st.session_state.logging_start_time
    st_autorefresh(interval=1000, key="logging_refresh")
    st.markdown(f"🟢 **Logging Active** — Duration: `{format_duration(elapsed)}`")
else:
    st.markdown("🔴 **Logging Inactive**")

# ---------------- LOAD IMAGE AND DRAW DOTS ----------------
if not os.path.exists(BACKGROUND_IMAGE_PATH):
    st.error(f"Missing background image: {BACKGROUND_IMAGE_PATH}")
    st.stop()

# Load and convert image
image = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
image_width, image_height = image.size

# Draw red dots onto the image
image_with_dots = image.copy()
draw = ImageDraw.Draw(image_with_dots)
dot_radius = 4

for _, _, val, aro, _ in st.session_state.emotions:
    x = int((val + 1) / 2 * image_width)
    y = int((1 - ((aro + 1) / 2)) * image_height)
    draw.ellipse((x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius), fill="red")

# Encode the modified image to base64
buf = io.BytesIO()
image_with_dots.save(buf, format="PNG")
base64_img = base64.b64encode(buf.getvalue()).decode("utf-8")
image_url = f"data:image/png;base64,{base64_img}"

# ---------------- CANVAS ----------------
st.markdown("### 🎨 Click to Log Emotion")

canvas_result = st_canvas(
    fill_color="rgba(0, 0, 0, 0)",
    stroke_width=0,
    background_image_url=image_url,  # ✅ Only using base64 image
    update_streamlit=True,
    height=image_height,
    width=image_width,
    drawing_mode="point",
    key="emotion_canvas"
)

# ---------------- HANDLE NEW CLICKS ----------------
if canvas_result.json_data and st.session_state.logging_enabled:
    objects = canvas_result.json_data["objects"]
    if objects:
        last_point = objects[-1]
        x_px = last_point["left"]
        y_px = last_point["top"]

        valence = round((x_px / image_width) * 2 - 1, 2)
        arousal = round(-((y_px / image_height) * 2 - 1), 2)

        t = format_duration(time.time() - st.session_state.logging_start_time)
        q = get_quadrant(valence, arousal)

        if len(st.session_state.emotions) == 0 or (valence, arousal) != (st.session_state.emotions[-1][2], st.session_state.emotions[-1][3]):
            st.session_state.emotions.append((t, st.session_state.current_song, valence, arousal, q))
            st.toast(f"✅ Logged: Valence={valence}, Arousal={arousal}, Quadrant={q}")

# ---------------- EXPORT SECTION ----------------
st.markdown("---")
st.markdown("### 📁 Logged Emotions")

df = pd.DataFrame(
    st.session_state.emotions,
    columns=["Time", "Song", "Valence", "Arousal", "Quadrant"]
)

st.dataframe(df, use_container_width=True)

filename_base = os.path.splitext(st.session_state.current_song)[0] if st.session_state.current_song else "session"
csv_data = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download CSV",
    data=csv_data,
    file_name=f"{filename_base}_emotions.csv",
    mime="text/csv",
    disabled=df.empty
)

# ---------------- NEXT SONG ----------------
if st.session_state.current_song and len(st.session_state.played_songs) < len(songs):
    if st.button("▶️ Next Song"):
        st.session_state.played_songs.append(st.session_state.current_song)
        st.session_state.current_song = None
        st.session_state.emotions = []
        st.session_state.logging_enabled = False
        st.session_state.logging_start_time = None
        st.experimental_rerun()
elif len(st.session_state.played_songs) >= len(songs):
    st.success("✅ All songs played!")
