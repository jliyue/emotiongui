# STREAMLIT VERSION OF YOUR MATPLOTLIB EMOTION LOGGER
# -----------------------------------------------------
# Note: Streamlit does NOT support native matplotlib interactivity like mouse click detection.
# Instead, we will use Plotly for interactivity and Streamlit to handle file playback, timing, logging, and exporting.

import streamlit as st
import os
import random
import time
import pandas as pd
import numpy as np
from datetime import timedelta
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events  # pip install streamlit-plotly-events

# ---------------- CONFIG ----------------
AUDIO_FOLDER = "songs"
SONG_DURATION = 180  # 3 minutes

# ---------------- SESSION INIT ----------------
st.set_page_config(layout="wide")
st.title("🎧 Arousal-Valence Emotion Logger")

if "played_songs" not in st.session_state:
    st.session_state.played_songs = []
if "current_song" not in st.session_state:
    st.session_state.current_song = None
if "song_start_time" not in st.session_state:
    st.session_state.song_start_time = None
if "emotions" not in st.session_state:
    st.session_state.emotions = []
if "participant_id" not in st.session_state:
    st.session_state.participant_id = "anonymous"

# ---------------- PARTICIPANT ID ----------------
st.session_state.participant_id = st.text_input("Enter Participant ID:", st.session_state.participant_id)

# ---------------- UTILS ----------------
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

# ---------------- LOAD SONGS ----------------
if not os.path.exists(AUDIO_FOLDER):
    st.error(f"Missing audio folder: {AUDIO_FOLDER}")
    st.stop()

all_songs = sorted([f for f in os.listdir(AUDIO_FOLDER) if f.endswith((".mp3", ".wav"))], key=extract_number)
remaining_songs = list(set(all_songs) - set(st.session_state.played_songs))

# ---------------- SONG SELECTION ----------------
if not st.session_state.current_song and remaining_songs:
    chosen_song = random.choice(remaining_songs)
    st.session_state.current_song = chosen_song
    st.session_state.song_start_time = time.time()
    st.session_state.played_songs.append(chosen_song)

# ---------------- PLAY AUDIO ----------------
if st.session_state.current_song:
    st.markdown(f"### 🎶 Now Playing: `{st.session_state.current_song}`")
    with open(os.path.join(AUDIO_FOLDER, st.session_state.current_song), "rb") as f:
        audio_bytes = f.read()
    st.audio(audio_bytes, format="audio/mp3")

    elapsed = time.time() - st.session_state.song_start_time
    if elapsed <= SONG_DURATION:
        st.success(f"🟢 Logging enabled! Time remaining: {int(SONG_DURATION - elapsed)}s")

        # ----------- INTERACTIVE 2D PLOT -----------
        fig = go.Figure()

        fig.add_shape(type="rect", x0=0, y0=0, x1=1, y1=1, fillcolor="green", opacity=0.3, line=dict(width=0))
        fig.add_shape(type="rect", x0=-1, y0=0, x1=0, y1=1, fillcolor="yellow", opacity=0.3, line=dict(width=0))
        fig.add_shape(type="rect", x0=-1, y0=-1, x1=0, y1=0, fillcolor="red", opacity=0.3, line=dict(width=0))
        fig.add_shape(type="rect", x0=0, y0=-1, x1=1, y1=0, fillcolor="blue", opacity=0.3, line=dict(width=0))
        fig.add_shape(type="line", x0=-1, y0=0, x1=1, y1=0, line=dict(color="black", width=2))
        fig.add_shape(type="line", x0=0, y0=-1, x1=0, y1=1, line=dict(color="black", width=2))

        # Labels
        emotion_labels = [("Excited", 67), ("Delighted", 45), ("Happy", 22), ("Content", -22),
                          ("Relaxed", -45), ("Calm", -67), ("Tired", -113), ("Bored", -135),
                          ("Depressed", -158), ("Frustrated", 158), ("Angry", 135), ("Tense", 113)]
        radius = 0.9
        for label, angle in emotion_labels:
            x = radius * np.cos(np.radians(angle))
            y = radius * np.sin(np.radians(angle))
            fig.add_trace(go.Scatter(x=[x], y=[y], text=[label], mode="text"))

        # Past logs
        if st.session_state.emotions:
            df = pd.DataFrame(st.session_state.emotions, columns=["Time", "Song", "Valence", "Arousal", "Quadrant"])
            fig.add_trace(go.Scatter(x=df["Valence"], y=df["Arousal"], mode="markers", marker=dict(size=10, color="black")))

        fig.update_layout(width=600, height=600, xaxis=dict(range=[-1, 1], title="Valence"),
                          yaxis=dict(range=[-1, 1], title="Arousal"), title="Click to Log Emotions")

        results = plotly_events(fig, click_event=True)
        if results:
            x, y = results[0]["x"], results[0]["y"]
            t = format_duration(elapsed)
            q = get_quadrant(x, y)
            st.session_state.emotions.append((t, st.session_state.current_song, x, y, q))
            st.success(f"✅ Logged via click: Valence={x:.2f}, Arousal={y:.2f}, Quadrant={q}")

        # Sliders
        st.markdown("#### Or use sliders")
        col1, col2 = st.columns(2)
        val = col1.slider("Valence", -1.0, 1.0, 0.0, 0.01)
        aro = col2.slider("Arousal", -1.0, 1.0, 0.0, 0.01)
        if st.button("Log via Sliders"):
            t = format_duration(elapsed)
            q = get_quadrant(val, aro)
            st.session_state.emotions.append((t, st.session_state.current_song, val, aro, q))
            st.success(f"✅ Logged via slider: Valence={val:.2f}, Arousal={aro:.2f}, Quadrant={q}")

    else:
        st.warning("⏰ 3 minutes done.")
        if st.button("▶️ Next Song"):
            st.session_state.current_song = None
            st.session_state.song_start_time = None
            st.experimental_rerun()
else:
    st.info("✅ All 21 songs played.")

# ---------------- EXPORT ----------------
if st.session_state.emotions:
    st.markdown("---")
    st.subheader("📄 Download Data")
    df = pd.DataFrame(st.session_state.emotions, columns=["Time", "Song", "Valence", "Arousal", "Quadrant"])
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, f"{st.session_state.participant_id}_emotions.csv", "text/csv")
