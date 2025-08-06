# STREAMLIT EMOTION LOGGER - OPTIMIZED VERSION FOR STREAMLIT CLOUD
import streamlit as st
import os
import random
import time
import pandas as pd
import numpy as np
from datetime import timedelta
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events

# ---------------- CONFIG ----------------
AUDIO_FOLDER = "song"
SONG_DURATION = 180  # in seconds

# ---------------- SESSION STATE ----------------
st.set_page_config(layout="wide")
st.title("🎧 Arousal-Valence Emotion Logger (Real-Time + Export)")

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

# ---------------- PARTICIPANT ID ----------------
st.session_state.participant_id = st.text_input("Enter Participant ID:", st.session_state.participant_id)

# ---------------- HELPERS ----------------
def extract_number(filename):
    import re
    match = re.search(r"(\d+)", filename)
    return int(match.group(1)) if match else float("inf")

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

# ---------------- SONG LOAD ----------------
if not os.path.exists(AUDIO_FOLDER):
    st.error(f"Missing audio folder: {AUDIO_FOLDER}")
    st.stop()

songs = sorted([f for f in os.listdir(AUDIO_FOLDER) if f.endswith((".mp3", ".wav"))], key=extract_number)
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
col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Start Logging"):
        st.session_state.logging_enabled = True
        st.session_state.logging_start_time = time.time()
        st.toast("✅ Logging started!", icon="🟢")

with col2:
    if st.button("⏹ Stop Logging"):
        st.session_state.logging_enabled = False
        st.toast("⏹ Logging stopped.", icon="🔴")

# ---------------- LOGGING STATUS ----------------
if st.session_state.logging_enabled and st.session_state.logging_start_time:
    elapsed_log = time.time() - st.session_state.logging_start_time
    st.markdown(f"🟢 **Logging Active** — Duration: `{format_duration(elapsed_log)}`")
else:
    st.markdown("🔴 **Logging Inactive** — Press 'Start Logging' to begin.")

# ---------------- EMOTION LOGGER PLOT ----------------
fig = go.Figure()

# Quadrants + labels
fig.add_shape(type="rect", x0=0, y0=0, x1=1, y1=1, fillcolor="green", opacity=0.3, line=dict(width=0))
fig.add_shape(type="rect", x0=-1, y0=0, x1=0, y1=1, fillcolor="yellow", opacity=0.3, line=dict(width=0))
fig.add_shape(type="rect", x0=-1, y0=-1, x1=0, y1=0, fillcolor="red", opacity=0.3, line=dict(width=0))
fig.add_shape(type="rect", x0=0, y0=-1, x1=1, y1=0, fillcolor="blue", opacity=0.3, line=dict(width=0))
fig.add_shape(type="line", x0=-1, y0=0, x1=1, y1=0, line=dict(color="black", width=2))
fig.add_shape(type="line", x0=0, y0=-1, x1=0, y1=1, line=dict(color="black", width=2))

labels = [("Excited", 67), ("Delighted", 45), ("Happy", 22), ("Content", -22),
          ("Relaxed", -45), ("Calm", -67), ("Tired", -113), ("Bored", -135),
          ("Depressed", -158), ("Frustrated", 158), ("Angry", 135), ("Tense", 113)]
r = 0.9
for label, angle in labels:
    x = r * np.cos(np.radians(angle))
    y = r * np.sin(np.radians(angle))
    fig.add_trace(go.Scatter(x=[x], y=[y], text=[label], mode="text"))

# Transparent clickable layer
fig.add_trace(go.Scatter(
    x=[-1, -0.5, 0, 0.5, 1],
    y=[-1, 0, 1, 0, -1],
    mode="markers",
    marker=dict(size=1, opacity=0),
    hoverinfo='skip',
    showlegend=False
))

# Logged points
if st.session_state.emotions:
    df = pd.DataFrame(
        st.session_state.emotions,
        columns=["Time", "Song", "Valence", "Arousal", "Quadrant"]
    )
    fig.add_trace(go.Scatter(
        x=df["Valence"],
        y=df["Arousal"],
        mode="markers",
        marker=dict(size=10, color="black"),
        name="Logged Emotions"
    ))

fig.update_layout(
    width=600,
    height=600,
    dragmode=False,
    hovermode=False,
    xaxis=dict(range=[-1, 1], title="Valence", fixedrange=True),
    yaxis=dict(range=[-1, 1], title="Arousal", fixedrange=True),
    title="Click to Log Emotions"
)

results = plotly_events(fig, click_event=True)

# ---------------- LOGGING CLICKS ----------------
if results and st.session_state.logging_enabled:
    try:
        x, y = results[0]["x"], results[0]["y"]
        log_time = time.time() - st.session_state.logging_start_time
        t = format_duration(log_time)
        q = get_quadrant(x, y)
        st.session_state.emotions.append((t, st.session_state.current_song, x, y, q))
        st.toast("✅ Logged!", icon="🟢")
        st.experimental_rerun()  # <- Refresh to show updated points
    except Exception as e:
        st.error(f"❌ Error logging click: {e}")

# ---------------- EXPORT SECTION ----------------
st.markdown("---")
st.markdown("### 📁 Export Emotion Data")

if not st.session_state.emotions:
    st.info("ℹ️ No data logged yet.")
else:
    st.success(f"✅ You’ve logged {len(st.session_state.emotions)} emotion(s)")

    with st.expander("⬇️ Download Logged Data", expanded=True):
        df = pd.DataFrame(
            st.session_state.emotions,
            columns=["Time", "Song", "Valence", "Arousal", "Quadrant"]
        )

        filename_base = os.path.splitext(st.session_state.current_song)[0]

        # Generate CSV in memory
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv_data, file_name=f"{filename_base}_emotions.csv", mime="text/csv")

        # (Optional) Skip image export to avoid Streamlit Cloud issues
        st.info("🖼️ Emotion map image export is disabled for now.")

# ---------------- NEXT SONG BUTTON ----------------
if st.session_state.current_song and len(st.session_state.played_songs) < len(songs):
    if st.button("▶️ Next Song"):
        st.session_state.played_songs.append(st.session_state.current_song)  # Add to history
        st.session_state.current_song = None
        st.session_state.emotions = []
        st.session_state.logging_enabled = False
        st.session_state.logging_start_time = None
        st.experimental_rerun()
elif len(st.session_state.played_songs) >= len(songs):
    st.success("✅ All songs played!")
