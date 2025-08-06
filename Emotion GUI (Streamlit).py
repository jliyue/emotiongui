# STREAMLIT EMOTION LOGGER — STABLE AUDIO PLAYER + AUTO CSV DOWNLOAD
import streamlit as st
import os
import random
import time
import pandas as pd
from datetime import timedelta
from PIL import Image, ImageDraw
from streamlit_autorefresh import st_autorefresh
from streamlit_image_coordinates import streamlit_image_coordinates

# ---------------- CONFIG ----------------
AUDIO_FOLDER = "song"
IMAGE_FILE = "photo.png"
DOT_RADIUS = 5
LOG_DURATION = 180  # seconds
st.set_page_config(layout="wide")
st.title("🎧 Arousal-Valence Emotion Logger (Reliable Audio Version)")

# ---------------- SESSION STATE ----------------
for key, default in {
    "played_songs": [],
    "current_song": None,
    "song_start_time": None,
    "emotions": [],
    "participant_id": "anonymous",
    "logging_enabled": False,
    "logging_start_time": None,
    "auto_csv_ready": False
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

# ---------------- SONG SELECTION ----------------
if not os.path.exists(AUDIO_FOLDER):
    st.error(f"Missing audio folder: {AUDIO_FOLDER}")
    st.stop()

songs = sorted([f for f in os.listdir(AUDIO_FOLDER) if f.endswith((".mp3", ".wav"))])
remaining = list(set(songs) - set(st.session_state.played_songs))

if not st.session_state.current_song and remaining:
    song = random.choice(remaining)
    st.session_state.current_song = song
    st.session_state.song_start_time = time.time()
    st.session_state.emotions = []
    st.session_state.logging_enabled = False
    st.session_state.logging_start_time = None
    st.session_state.auto_csv_ready = False

# ---------------- AUDIO PLAYER ----------------
if st.session_state.current_song:
    audio_path = os.path.join(AUDIO_FOLDER, st.session_state.current_song)
    st.markdown(f"### 🎶 Now Playing: `{st.session_state.current_song}`")
    with open(audio_path, "rb") as f:
        st.audio(f.read(), format="audio/mp3")
    st.info("Click ▶️ above to start the music.")

# ---------------- LOGGING CONTROLS ----------------
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("▶️ Start Logging (lasts 180s)"):
        st.session_state.logging_enabled = True
        st.session_state.logging_start_time = time.time()
        st.session_state.auto_csv_ready = False
        st.toast("✅ Logging started!", icon="🟢")
with col2:
    if st.button("⏹ Stop Logging"):
        st.session_state.logging_enabled = False
        st.toast("🛑 Logging stopped.", icon="🔴")
with col3:
    if st.button("🧹 Reset Log"):
        st.session_state.emotions = []
        st.toast("🧽 Log cleared.")

# ---------------- TIMER ----------------
if st.session_state.logging_enabled and st.session_state.logging_start_time:
    elapsed = time.time() - st.session_state.logging_start_time
    st_autorefresh(interval=1000, key="refresh_timer")
    st.markdown(f"🟢 Logging Active — Duration: `{format_duration(elapsed)}`")

    if elapsed >= LOG_DURATION and not st.session_state.auto_csv_ready:
        st.session_state.auto_csv_ready = True
        st.toast("⏱️ 180 seconds reached! Download your data below.", icon="📥")
else:
    st.markdown("🔴 Logging Inactive")

# ---------------- IMAGE + CLICK ----------------
if not os.path.exists(IMAGE_FILE):
    st.error(f"Missing image: {IMAGE_FILE}")
    st.stop()

image = Image.open(IMAGE_FILE).convert("RGBA")
image_width, image_height = image.size

# Draw red dots
display_image = image.copy()
draw = ImageDraw.Draw(display_image)
for _, _, val, aro, _ in st.session_state.emotions:
    x = int((val + 1) / 2 * image_width)
    y = int((1 - (aro + 1) / 2) * image_height)
    draw.ellipse([x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS], fill="red")

# Layout with axis labels
left_col, image_col, right_col = st.columns([1, 8, 1])
with left_col:
    st.markdown("<div style='height: 100%; display: flex; align-items: center; justify-content: center; transform: rotate(-90deg); font-weight: bold;'>Arousal</div>", unsafe_allow_html=True)
with image_col:
    coords = streamlit_image_coordinates(display_image, key="avgrid")
st.markdown("<div style='text-align: center; font-weight: bold;'>Valence</div>", unsafe_allow_html=True)

# ---------------- HANDLE CLICK ----------------
if coords and st.session_state.logging_enabled:
    x_px, y_px = coords["x"], coords["y"]
    val = round((x_px / image_width) * 2 - 1, 2)
    aro = round(-((y_px / image_height) * 2 - 1), 2)
    t = format_duration(time.time() - st.session_state.logging_start_time)
    q = get_quadrant(val, aro)
    st.session_state.emotions.append((t, st.session_state.current_song, val, aro, q))
    st.toast(f"✅ Logged: Val={val}, Aro={aro}, Quadrant={q}")

# ---------------- EXPORT LOGS ----------------
st.markdown("---")
df = pd.DataFrame(
    st.session_state.emotions,
    columns=["Time", "Song", "Valence", "Arousal", "Quadrant"]
)
st.markdown("### 📁 Logged Emotions")
st.dataframe(df, use_container_width=True)

filename_base = os.path.splitext(st.session_state.current_song)[0]
csv_data = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download CSV",
    data=csv_data,
    file_name=f"{filename_base}_emotions.csv",
    mime="text/csv",
    disabled=df.empty
)

# ---------------- AUTO CSV DOWNLOAD ----------------
if st.session_state.auto_csv_ready and not df.empty:
    st.success("🕒 Logging complete. Download your emotion log:")
    st.download_button(
        label="📥 Download Final CSV (Auto)",
        data=csv_data,
        file_name=f"{filename_base}_180sec.csv",
        mime="text/csv"
    )

# ---------------- NEXT SONG ----------------
if len(st.session_state.played_songs) < len(songs):
    if st.button("▶️ Next Song"):
        st.session_state.played_songs.append(st.session_state.current_song)
        st.session_state.current_song = None
        st.session_state.emotions = []
        st.session_state.logging_enabled = False
        st.session_state.logging_start_time = None
        st.rerun()
elif len(st.session_state.played_songs) >= len(songs):
    st.success("✅ All songs played!")
