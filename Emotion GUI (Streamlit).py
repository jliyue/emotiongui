# EMOTION LOGGER — Upload Audio OR Use Songs Folder + Export
import streamlit as st
import os
import time
import pandas as pd
from datetime import timedelta
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
from streamlit_autorefresh import st_autorefresh

# ---------------- CONFIG ----------------
IMAGE_FILE = "photo.png"
AUDIO_FOLDER = "emotiongui/song"
EXPORT_FOLDER = "export"
DOT_RADIUS = 5
LOG_DURATION = 180

st.set_page_config(layout="wide")
st.title("💡 Arousal-Valence Emotion Logger (Upload or Use Playlist)")

# ---------------- SESSION STATE ----------------
for key, default in {
    "emotions": [],
    "logging_enabled": False,
    "logging_start_time": None,
    "auto_csv_ready": False,
    "uploaded_audio_data": None,
    "uploaded_audio_name": None,
    "song_index": 0,
    "playlist_mode": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- PARTICIPANT ID ----------------
participant_id = st.text_input("Enter Participant ID:", value="anonymous")

# ---------------- AUDIO UPLOAD OR PLAYLIST ----------------
uploaded_audio = st.file_uploader("🎧 Upload your own MP3 or skip to use preloaded playlist:", type=["mp3"])

if uploaded_audio:
    st.session_state.uploaded_audio_data = uploaded_audio.read()
    st.session_state.uploaded_audio_name = uploaded_audio.name
    st.session_state.playlist_mode = False
else:
    songs = sorted([f for f in os.listdir(AUDIO_FOLDER) if f.endswith(".mp3")])
    if songs:
        st.session_state.playlist_mode = True
        st.session_state.uploaded_audio_name = songs[st.session_state.song_index]
        audio_path = os.path.join(AUDIO_FOLDER, st.session_state.uploaded_audio_name)
        with open(audio_path, "rb") as f:
            st.session_state.uploaded_audio_data = f.read()
    else:
        st.warning("Upload an MP3 file or add files to 'emotiongui/song' folder.")
        st.stop()

# ---------------- AUDIO PLAYER ----------------
st.markdown(f"### 🎶 Now Playing: `{st.session_state.uploaded_audio_name}`")
st.audio(st.session_state.uploaded_audio_data, format="audio/mp3")

# ---------------- CONTROLS ----------------
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("▶️ Start Logging"):
        st.session_state.logging_enabled = True
        st.session_state.logging_start_time = time.time()
        st.session_state.auto_csv_ready = False
        st.toast("✅ Logging started!", icon="🟢")

with col2:
    if st.button("⏹ Stop Logging"):
        st.session_state.logging_enabled = False
        st.toast("🛑 Logging stopped.")

with col3:
    if st.button("🧹 Reset Log"):
        st.session_state.emotions = []
        st.toast("🧽 Log cleared.")

# ---------------- TIMER ----------------
if st.session_state.logging_enabled and st.session_state.logging_start_time:
    elapsed = time.time() - st.session_state.logging_start_time
    st_autorefresh(interval=1000, key="refresh_timer")
    percent_complete = min(elapsed / LOG_DURATION, 1.0)
    st.progress(percent_complete, text=f"{int(elapsed)}s / {LOG_DURATION}s")

    if elapsed >= LOG_DURATION and not st.session_state.auto_csv_ready:
        st.session_state.auto_csv_ready = True
        st.toast("⏱️ 180 seconds reached! Download available below.", icon="📥")
else:
    st.markdown("🔴 Logging Inactive")

# ---------------- LOAD IMAGE ----------------
if not os.path.exists(IMAGE_FILE):
    st.error("Missing emotion grid image file.")
    st.stop()

image = Image.open(IMAGE_FILE).convert("RGBA")
image_width, image_height = image.size

# Draw blue dots
def draw_dots(img, data):
    draw = ImageDraw.Draw(img)
    for _, _, val, aro, _ in data:
        x = int((val + 1) / 2 * img.width)
        y = int((1 - (aro + 1) / 2) * img.height)
        draw.ellipse([x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS], fill="blue")
    return img

image_with_dots = draw_dots(image.copy(), st.session_state.emotions)

# ---------------- IMAGE + CLICK ----------------
left, center, right = st.columns([1, 8, 1])
with left:
    st.markdown("<div style='height: 100%; display: flex; align-items: center; justify-content: center; transform: rotate(-90deg); font-weight: bold;'>Arousal</div>", unsafe_allow_html=True)

with center:
    coords = streamlit_image_coordinates(image_with_dots, key="emotion_grid")

st.markdown("<div style='text-align: center; font-weight: bold;'>Valence</div>", unsafe_allow_html=True)

# ---------------- HANDLE CLICKS ----------------
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

def format_duration(seconds):
    return str(timedelta(seconds=int(seconds)))

if coords and st.session_state.logging_enabled:
    x_px, y_px = coords["x"], coords["y"]
    val = round((x_px / image_width) * 2 - 1, 2)
    aro = round(-((y_px / image_height) * 2 - 1), 2)
    t = format_duration(time.time() - st.session_state.logging_start_time)
    q = get_quadrant(val, aro)
    st.session_state.emotions.append((t, st.session_state.uploaded_audio_name, val, aro, q))
    st.toast(f"✅ Logged: Val={val}, Aro={aro}, Quadrant={q}")

# ---------------- EXPORT ----------------
st.markdown("---")
df = pd.DataFrame(
    st.session_state.emotions,
    columns=["Time", "Song", "Valence", "Arousal", "Quadrant"]
)
st.markdown("### 📁 Logged Emotions")
st.dataframe(df, use_container_width=True)

os.makedirs(EXPORT_FOLDER, exist_ok=True)
filename_base = os.path.splitext(st.session_state.uploaded_audio_name)[0]
csv_path = os.path.join(EXPORT_FOLDER, f"{filename_base}_log.csv")
png_path = os.path.join(EXPORT_FOLDER, f"{filename_base}_dots.png")
df.to_csv(csv_path, index=False)
image_with_dots.save(png_path)

st.download_button("⬇️ Download CSV", open(csv_path, "rb").read(), file_name=os.path.basename(csv_path), mime="text/csv")
st.download_button("🖼️ Download PNG Grid", open(png_path, "rb").read(), file_name=os.path.basename(png_path), mime="image/png")

# ---------------- NEXT SONG ----------------
if st.session_state.playlist_mode and st.session_state.song_index + 1 < len(songs):
    if st.button("▶️ Next Song"):
        st.session_state.song_index += 1
        st.session_state.emotions = []
        st.session_state.logging_enabled = False
        st.session_state.logging_start_time = None
        st.rerun()
elif st.session_state.playlist_mode and st.session_state.song_index + 1 >= len(songs):
    st.success("🎉 All songs completed! Thank you.")
