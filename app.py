import os

import streamlit as st
import whisper
from pytube import YouTube

if "audio_file_path" not in st.session_state:
    st.session_state.audio_file_path = ""
if "transcription" not in st.session_state:
    st.session_state.transcription = ""
if "transcribed" not in st.session_state:
    st.session_state.transcribed = False
if "downloaded" not in st.session_state:
    st.session_state.downloaded = False
if "last_processed_file" not in st.session_state:
    st.session_state.last_processed_file = ""


os.makedirs("temp", exist_ok=True)


def download_youtube_audio(youtube_url):
    yt = YouTube(youtube_url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_file = audio_stream.download(output_path="temp")
    return audio_file


def transcribe_audio(audio_file_path, model_name="base"):
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_file_path)
    return result["text"]


def flush_session_state():
    keys = list(st.session_state.keys())
    for key in keys:
        st.session_state.pop(key)


st.title("Audio Transcription with Whisper")

audio_source = st.radio("Select audio source", ("Upload File", "YouTube Link"))

try:
    if audio_source == "Upload File":
        allowed_file_types = ["mp3", "wav", "flac", "mp4", "m4a", "ogg", "aac", "avi", "mkv"]
        uploaded_file = st.file_uploader("Choose an audio file", type=allowed_file_types)
        if uploaded_file is not None and uploaded_file.name != st.session_state.last_processed_file:
            bytes_data = uploaded_file.getvalue()
            st.session_state.audio_file_path = f"temp/{uploaded_file.name}"
            with open(st.session_state.audio_file_path, "wb") as f:
                f.write(bytes_data)
            st.session_state.last_processed_file = uploaded_file.name
            st.session_state.transcribed = False

    elif audio_source == "YouTube Link":
        youtube_url = st.text_input("Enter YouTube video link:")
        if youtube_url and youtube_url != st.session_state.last_processed_file:
            with st.spinner("Downloading YouTube video audio..."):
                st.session_state.audio_file_path = download_youtube_audio(youtube_url)
                st.session_state.last_processed_file = youtube_url
            st.session_state.transcribed = False

    if st.session_state.audio_file_path and not st.session_state.transcribed:
        if st.button("Transcribe"):
            with st.spinner("Transcribing audio..."):
                st.session_state.transcription = transcribe_audio(
                    st.session_state.audio_file_path, model_name="base"
                )
                st.session_state.transcribed = True

    if st.session_state.transcribed and not st.session_state.downloaded:
        edited_transcription = st.text_area(
            "Transcription", st.session_state.transcription, height=300
        )
        st.session_state.transcription = edited_transcription
        st.session_state.downloaded = st.download_button(
            label="Download Transcription as TXT",
            data=st.session_state.transcription,
            file_name="transcription.txt",
            mime="text/plain",
        )
        if st.session_state.downloaded:
            st.session_state.transcribed = False
            st.session_state.downloaded = False
        try:
            os.remove(st.session_state.audio_file_path)
        except OSError:
            pass
except:
    st.error("An error occurred. Please reload page.")
    flush_session_state()
    st.stop()
