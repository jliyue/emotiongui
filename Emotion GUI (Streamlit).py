# STREAMLIT EMOTION LOGGER — FINAL VERSION: Audio + Blue Dots + Export + Timer
import streamlit as st
import os
import random
import time
import pandas as pd
from datetime import timedelta
from PIL import Image, ImageDraw
from streamlit_autorefresh import st_autorefresh
from streamlit_image_coordinates import streamlit_image_coordinates
import streamlit.components.v1 as components

# ---------------- CONFIG ----------------
AUDIO_FOLDER = "song"
IMAGE_FILE = "photo.png"
EXPORT_FOLDER = "export"
DOT_RADIUS = 5
LOG_DURATION = 180  # seconds

st.set_page_config(layout="wide")
st.title("🎧 Arousal-Valence Emotion Logger (Auto Audio + Export)")

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

def draw_dots(image, emotion_data):
    image_copy = image.copy()
    draw = ImageDraw.Draw(image_copy)
    for _, _, val, aro, _ in emotion_data:
        x = int((val + 1) / 2 * image.width)
        y = int((1 - ((aro + 1) / 2)) * image.height)
        draw.ellipse(
            [x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS],
            fill="blue"
        )
    return image_copy

def play_audio():
    components.html("""
        <script>
            const audio = document.getElementById("audio-player");
            if (audio) {
                audio.currentTime = 0;
                audio.play();
            }
        </script>
    """, height=0)

# ---------------- PARTICIPANT ID ----------------
st.session_state.participant_id = st.text_input("Enter Participant ID:", st.session_state.participant_id)

# ---------------- SONG SETUP ----------------
if not os.path.exists(AUDIO_FOLDER):
    st.error(f"Missing audio folder: {AUDIO_FOLDER}")
    st.stop()

songs = sorted([f for f in os.listdir(AUDIO_FOLDER) if f.endswith((".mp3", ".wav"))])
remaining = list(set(songs) - set(st.session_state.played_songs))

if not st.session_state.current_song and remaining:
    st.session_state.current_song = random.choice(remaining)
    st.session_state.song_start_time = time.time()
    st.session_state.emotions = []
    st.session_state.logging_enabled = False
    st.session_state.logging_start_time = None
    st.session_state.auto_csv_ready = False

# ---------------- AUDIO PLAYER INJECTION ----------------
audio_path = os.path.join(AUDIO_FOLDER, st.session_state.current_song)
st.markdown(f"### 🎶 Now Playing: `{st.session_state.current_song}`")

components.html(f"""
<audio id="audio-player" controls preload="auto">
  <source src="{audio_path}" type="audio/mp3">
  Your browser does not support the audio element.
</audio>
""", height=80)

st.info("ℹ️ The audio will start when you click ▶️ Start Logging.")

# ---------------- LOGGING CONTROLS ----------------
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("▶️ Start Logging + Play Audio"):
        st.session_state.logging_enabled = True
        st.session_state.logging_start_time = time.time()
        st.session_state.auto_csv_ready = False
        play_audio()
        st.toast("✅ Logging started & audio playing!", icon="🟢")

with col2:
    if st.button("⏹ Stop Logging"):
        st.session_state.logging_enabled = False
        st.toast("🛑 Logging stopped.", icon="🔴")

with col3:
    if st.button("🧹 Reset Log"):
        st.session_state.emotions = []
        st.toast("🧽 Log cleared.")

# ---------------- TIMER BAR ----------------
if st.session_state.logging_enabled and st.session_state.logging_start_time:
    elapsed = time.time() - st.session_state.logging_start_time
    st_autorefresh(interval=1000, key="refresh_timer")
    percent_complete = min(elapsed / LOG_DURATION, 1.0)
    st.progress(percent_complete, text=f"{int(elapsed)}s / 180s")

    if elapsed >= LOG_DURATION and not st.session_state.auto_csv_ready:
        st.session_state.auto_csv_ready = True
        st.toast("⏱️ 180 seconds reached! Download available below.", icon="📥")
else:
    st.markdown("🔴 Logging Inactive")

# ---------------- IMAGE LOADING ----------------
if not os.path.exists(IMAGE_FILE):
    st.error(f"Missing image: {IMAGE_FILE}")
    st.stop()

image = Image.open(IMAGE_FILE).convert("RGBA")
image_width, image_height = image.size
image_with_dots = draw_dots(image, st.session_state.emotions)

# ---------------- IMAGE + CLICK TRACKING ----------------
left_col, image_col, right_col = st.columns([1, 8, 1])
with left_col:
    st.markdown("<div style='height: 100%; display: flex; align-items: center; justify-content: center; transform: rotate(-90deg); font-weight: bold;'>Arousal</div>", unsafe_allow_html=True)
with image_col:
    coords = streamlit_image_coordinates(image_with_dots, key="avgrid")
st.markdown("<div style='text-align: center; font-weight: bold;'>Valence</div>", unsafe_allow_html=True)

# ---------------- HANDLE CLICKS ----------------
if coords and st.session_state.logging_enabled:
    x_px, y_px = coords["x"], coords["y"]
    val = round((x_px / image_width) * 2 - 1, 2)
    aro = round(-((y_px / image_height) * 2 - 1), 2)
    t = format_duration(time.time() - st.session_state.logging_start_time)
    q = get_quadrant(val, aro)
    st.session_state.emotions.append((t, st.session_state.current_song, val, aro, q))
    st.toast(f"✅ Logged: Val={val}, Aro={aro}, Quadrant={q}")

# ---------------- EXPORT SECTION ----------------
st.markdown("---")
df = pd.DataFrame(
    st.session_state.emotions,
    columns=["Time", "Song", "Valence", "Arousal", "Quadrant"]
)
st.markdown("### 📁 Logged Emotions")
st.dataframe(df, use_container_width=True)

# Save CSV and PNG to export folder
os.makedirs(EXPORT_FOLDER, exist_ok=True)

filename_base = os.path.splitext(st.session_state.current_song)[0]
csv_path = os.path.join(EXPORT_FOLDER, f"{filename_base}_log.csv")
png_path = os.path.join(EXPORT_FOLDER, f"{filename_base}_grid_dots.png")

df.to_csv(csv_path, index=False)
image_with_dots.save(png_path)

# Download buttons
st.download_button(
    label="⬇️ Download CSV",
    data=open(csv_path, "rb").read(),
    file_name=os.path.basename(csv_path),
    mime="text/csv"
)

st.download_button(
    label="🖼️ Download Grid Image with Blue Dots",
    data=open(png_path, "rb").read(),
    file_name=os.path.basename(png_path),
    mime="image/png"
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
