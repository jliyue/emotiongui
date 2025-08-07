# EMOTION LOGGER — 21 Google Drive Songs + Manual Logging + Export
import streamlit as st
import os
import time
import pandas as pd
from datetime import timedelta
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# ---------------- CONFIG ----------------
IMAGE_FILE = "photo.png"
EXPORT_FOLDER = "export"
DOT_RADIUS = 5
LOG_DURATION = 180

st.set_page_config(layout="wide")
st.title("🎧 Arousal-Valence Emotion Logger — 21 Songs Edition")

# ---------------- SESSION STATE ----------------
for key, default in {
    "emotions": [],
    "logging_enabled": False,
    "logging_start_time": None,
    "auto_csv_ready": False,
    "selected_song_index": 0
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ---------------- SONG LINKS ----------------
song_urls = [
    "https://drive.google.com/uc?export=download&id=1YHgQcfXcs0L-ZbRQWZk9inWxWJqDiplT",
    "https://drive.google.com/uc?export=download&id=1nlrwDmMnqHvPBIu5tlq7r40ThRJp395d",
    "https://drive.google.com/uc?export=download&id=1maapzKvrnkVkpxw_pzdWn7BQTpUaVVgb",
    "https://drive.google.com/uc?export=download&id=1-0nLDaDUDtEIBF5G29Im0vEvb4_jWuAi",
    "https://drive.google.com/uc?export=download&id=1c5D2VtW0qK173YDRmbAHIfm43u3EAcq",
    "https://drive.google.com/uc?export=download&id=1ojX8O5mVTA6IzM6ILt7ssp5suOrlL_c8",
    "https://drive.google.com/uc?export=download&id=14nSioRFinDaVVuUNLereCB2VtmYlPzLo",
    "https://drive.google.com/uc?export=download&id=1aTR1iSdcTsIZUfgZpameIRlYbget-GRq",
    "https://drive.google.com/uc?export=download&id=1A40_NigxlyzTrqHo1_yhhTZPiijnoBAg",
    "https://drive.google.com/uc?export=download&id=17-afTf_2xh3y0pdWu_PNg6aT3RWccd--",
    "https://drive.google.com/uc?export=download&id=1fg61WMu3OAIlMxCS2hQPdAAJ5KKcsDrB",
    "https://drive.google.com/uc?export=download&id=1LJ34xfyCoolKIEYEkqo5TtjYJiXAkels",
    "https://drive.google.com/uc?export=download&id=1InaDyzOiVuGaREkRbSY1lynr-phgdTeu",
    "https://drive.google.com/uc?export=download&id=1RKhtmByfUi-JXxU9kkUkSh5ZnoeMqhpo",
    "https://drive.google.com/uc?export=download&id=1E6g_SU9fBbWlvpemfXqbsla9MQOfF03q",
    "https://drive.google.com/uc?export=download&id=1Xrnkzftzk80Jvb1odpDrO-pIzcK-Y1cd",
    "https://drive.google.com/uc?export=download&id=1Vxa5zXZtMeNLnNC7eBy3SCEQLV7YpW_a",
    "https://drive.google.com/uc?export=download&id=1jjT-Q_BvjIX3EPa4Qr9WI6gkZ_P-wpih",
    "https://drive.google.com/uc?export=download&id=1YbjRMOrUweXTTXVjzao_lR7qDSHGZKYP",
    "https://drive.google.com/uc?export=download&id=1sdeRZa_lxGSPoi_eB6IXcXkgsedfNfWS",
    "https://drive.google.com/uc?export=download&id=1zXb41sWN39rZrFBGQO8dKKFPiJVc56ly"
]

# ---------------- PARTICIPANT ID + SONG SELECT ----------------
participant_id = st.text_input("Enter Participant ID:", value="anonymous")
song_names = [f"Song {i+1}" for i in range(len(song_urls))]
st.session_state.selected_song_index = st.selectbox("Choose Song", range(len(song_urls)), format_func=lambda i: song_names[i])

# ---------------- AUDIO TIP + PLAYER ----------------
st.markdown("""
<div style='
    background-color: #f9f9f9;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #ddd;
    margin-bottom: 1rem;
'>
    <strong>🎧 Tip:</strong> Please use <u>headphones</u> and adjust your volume before starting. Then press ▶️ below to play the audio.
</div>
""", unsafe_allow_html=True)

st.markdown(f"### ▶️ {song_names[st.session_state.selected_song_index]}")
components.html(f"""
<audio controls style='width: 100%; margin-bottom: 16px;'>
  <source src="{song_urls[st.session_state.selected_song_index]}" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>
""", height=90)

# ---------------- LOGGING CONTROLS ----------------
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Start Logging"):
        st.session_state.logging_enabled = True
        st.session_state.logging_start_time = time.time()
        st.session_state.auto_csv_ready = False

        components.html("""
            <script>
                const player = document.querySelector('audio');
                if (player) {
                    player.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            </script>
        """, height=0)

        st.toast("✅ Logging started — press ▶️ to play audio.", icon="🟢")


with col2:
    if st.button("Stop Logging"):
        st.session_state.logging_enabled = False
        st.toast("🛑 Logging stopped.")

with col3:
    if st.button("Reset Log"):
        st.session_state.emotions = []
        st.toast("🧽 Log cleared.")

# ---------------- TIMER BAR ----------------
if st.session_state.logging_enabled and st.session_state.logging_start_time:
    elapsed = time.time() - st.session_state.logging_start_time
    st_autorefresh(interval=1000, key="refresh_timer")
    percent_complete = min(elapsed / LOG_DURATION, 1.0)
    st.progress(percent_complete, text=f"{int(elapsed)}s / {LOG_DURATION}s")
else:
    st.markdown("🔴 Logging Inactive")

# ---------------- LOAD + DRAW EMOTION MAP ----------------
if not os.path.exists(IMAGE_FILE):
    st.error("Missing emotion grid image file.")
    st.stop()

image = Image.open(IMAGE_FILE).convert("RGBA")
image_width, image_height = image.size

def draw_dots(img, data):
    draw = ImageDraw.Draw(img)
    for _, _, val, aro, _ in data:
        x = int((val + 1) / 2 * image_width)
        y = int((1 - (aro + 1) / 2) * image_height)
        draw.ellipse([x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS], fill="blue")
    return img

image_with_dots = draw_dots(image.copy(), st.session_state.emotions)

# ---------------- IMAGE LOGGER ----------------
left, center, right = st.columns([1, 8, 1])
with left:
    st.markdown("<div style='height: 100%; display: flex; align-items: center; justify-content: center; transform: rotate(-90deg); font-weight: bold;'>Arousal</div>", unsafe_allow_html=True)
with center:
    coords = streamlit_image_coordinates(image_with_dots, key="emotion_grid")
st.markdown("<div style='text-align: center; font-weight: bold;'>Valence</div>", unsafe_allow_html=True)

# ---------------- CLICK TO LOG ----------------
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
    st.session_state.emotions.append((t, song_names[st.session_state.selected_song_index], val, aro, q))
    st.toast(f"✅ Logged: Val={val}, Aro={aro}, Quadrant={q}")

# ---------------- EXPORT SECTION ----------------
st.markdown("---")
df = pd.DataFrame(
    st.session_state.emotions,
    columns=["Time", "Song", "Valence", "Arousal", "Quadrant"]
)
st.markdown("### 📁 Logged Emotions")
st.dataframe(df, use_container_width=True)

os.makedirs(EXPORT_FOLDER, exist_ok=True)
filename_base = f"song_{st.session_state.selected_song_index+1}"
csv_path = os.path.join(EXPORT_FOLDER, f"{filename_base}_log.csv")
png_path = os.path.join(EXPORT_FOLDER, f"{filename_base}_dots.png")
df.to_csv(csv_path, index=False)
image_with_dots.save(png_path)

st.download_button("⬇️ Download CSV", open(csv_path, "rb").read(), file_name=os.path.basename(csv_path), mime="text/csv")
st.download_button("🖼️ Download PNG Grid", open(png_path, "rb").read(), file_name=os.path.basename(png_path), mime="image/png")
