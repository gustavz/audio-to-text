import os
import shutil

import streamlit as st
import whisper
from pytube import YouTube

TMP_PATH = "tmp"
SUPPORTED_FILE_TYPES = ["mp3", "wav", "flac", "mp4", "m4a", "ogg", "aac", "avi", "mkv"]
SUPPORTED_MODELS = ["tiny", "base"]  # "small", "medium", "large"

os.makedirs(TMP_PATH, exist_ok=True)


def download_youtube_audio(youtube_url):
    yt = YouTube(youtube_url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    audio_file = audio_stream.download(output_path=TMP_PATH)
    return audio_file


def transcribe_audio(audio_file_path, model_name="base"):
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_file_path)
    return result["text"]


def models_format_func(x):
    mapping = {
        "tiny": 32,
        "base": 16,
        "small": 6,
        "medium": 2,
        "large": 1,
    }
    return f"{x.upper()} (relative speed: ~{mapping[x]}x)"


if "audio_file_path" not in st.session_state:
    st.session_state.audio_file_path = ""
if "last_processed_file" not in st.session_state:
    st.session_state.last_processed_file = ""
if "transcription" not in st.session_state:
    st.session_state.transcription = ""
if "transcribed" not in st.session_state:
    st.session_state.transcribed = False
if "downloaded" not in st.session_state:
    st.session_state.downloaded = False


st.title("Audio Transcription with Whisper")
input_container = st.empty()
output_container = st.empty()

try:
    with input_container.container():
        audio_source = st.radio("Select audio source", ("Upload File", "YouTube Link"))
        if audio_source == "Upload File":
            uploaded_file = st.file_uploader("Choose an audio file", type=SUPPORTED_FILE_TYPES)
            if (
                uploaded_file is not None
                and uploaded_file.name != st.session_state.last_processed_file
            ):
                bytes_data = uploaded_file.getvalue()
                st.session_state.audio_file_path = f"{TMP_PATH}/{uploaded_file.name}"
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

    with output_container.container():
        if st.session_state.audio_file_path and not st.session_state.transcribed:
            model_name = st.selectbox(
                "Select Model", SUPPORTED_MODELS, index=1, format_func=models_format_func
            )
            if st.button("Transcribe"):
                with st.spinner("Transcribing audio..."):
                    st.session_state.transcription = transcribe_audio(
                        st.session_state.audio_file_path, model_name=model_name
                    )
                    st.session_state.transcribed = True

    with output_container.container():
        if st.session_state.transcribed:
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
            # cleanup files after transcription
            shutil.rmtree(TMP_PATH, ignore_errors=True)

    if st.session_state.downloaded:
        # reset app after download
        for key in st.session_state.keys():
            st.session_state.pop(key)
        output_container.empty()
        st.info("Transcription downloaded successfully!", icon="🎉")
        st.balloons()


except:
    st.error("An error occurred. Please reload page.", icon="🚨")
    shutil.rmtree(TMP_PATH, ignore_errors=True)
    st.stop()
