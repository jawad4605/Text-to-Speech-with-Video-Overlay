import os
import pyttsx3
import streamlit as st
port = int(os.environ.get("PORT", 8501))
st.set_option("server.port", port)
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip

def generate_audio_pyttsx3(text, gender, voice_index, pitch):
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        male_voices = [v for v in voices if "male" in v.name.lower()]
        female_voices = [v for v in voices if "female" in v.name.lower()]

        selected_voices = male_voices if gender == "male" else female_voices

        if not selected_voices:
            st.warning(f"No {gender} voices available. Falling back to default voice.")
            selected_voices = voices  # Use all available voices

        if voice_index > len(selected_voices) or voice_index < 1:
            raise IndexError(f"Invalid voice index for {gender}. Available voices: {len(selected_voices)}")

        engine.setProperty('voice', selected_voices[voice_index - 1].id)

        # Adjust pitch (pitch in pyttsx3 is set by changing the rate)
        default_rate = engine.getProperty('rate')
        engine.setProperty('rate', int(default_rate * pitch))

        audio_path = "generated_audio.wav"
        engine.save_to_file(text, audio_path)
        engine.runAndWait()

        return audio_path
    except Exception as e:
        raise RuntimeError(f"Error generating audio with pyttsx3: {e}")

def generate_audio_gtts(text, language):
    try:
        audio_path = "generated_audio.mp3"
        tts = gTTS(text=text, lang=language)
        tts.save(audio_path)
        return audio_path
    except Exception as e:
        raise RuntimeError(f"Error generating audio with gTTS: {e}")

def overlay_audio_on_video(video_path, audio_path):
    try:
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)

        # Trim the video to match audio duration
        trimmed_video = video.subclip(0, min(video.duration, audio.duration))

        # Set audio to trimmed video
        final_video = trimmed_video.set_audio(audio)
        output_video_path = "final_video.mp4"
        final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac")

        return output_video_path
    except Exception as e:
        raise RuntimeError(f"Error overlaying audio on video: {e}")
    finally:
        video.close()
        audio.close()

st.title("Text-to-Speech with Video Overlay")

st.header("Step 1: Enter Text for TTS")
text = st.text_area("Enter the text you want to convert to speech:")

st.header("Step 2: Select Language")
language = st.selectbox("Choose a language:", ["en", "es", "fr", "de", "it", "ur"])

st.header("Step 3: Select Voice Gender")
gender = st.selectbox("Choose voice gender:", ["male", "female"])

st.header("Step 4: Select Voice")
engine = pyttsx3.init()
voices = engine.getProperty('voices')
available_voices = (
    [v for v in voices if "male" in v.name.lower()] if gender == "male" else [v for v in voices if "female" in v.name.lower()]
)

voice_options = [f"Voice {i + 1}: {v.name}" for i, v in enumerate(available_voices)]
if available_voices:
    voice_index = st.selectbox(
        "Select a voice:",
        range(1, len(voice_options) + 1),
        format_func=lambda i: voice_options[i - 1],
    )
    st.write(f"Selected {gender} voice: {voice_options[voice_index - 1]}")
else:
    st.warning(f"No {gender} voices available. Falling back to default voice.")
    available_voices = voices  # Use all available voices
    voice_index = 1

st.header("Step 5: Adjust Pitch")
pitch = st.slider("Adjust voice pitch (higher values = higher pitch, lower values = lower pitch):", 0.5, 2.0, 1.0)

st.header("Step 6: Select a Video")
video_files = [f for f in os.listdir('.') if f.endswith(('.mp4', '.avi', '.mov', '.mkv'))]
if not video_files:
    st.error("No video files found in the current directory.")
    video_path = None
else:
    video_path = st.selectbox("Select a video file from the folder:", video_files)

if st.button("Generate Video"):
    if not text:
        st.error("Please enter some text for TTS.")
    elif not video_path:
        st.error("Please select a video file.")
    elif voice_index is None:
        st.error("Please select a valid voice.")
    else:
        try:
            st.info("Generating audio...")
            if language == "ur":
                audio_path = generate_audio_gtts(text, language)
            else:
                audio_path = generate_audio_pyttsx3(text, gender, voice_index, pitch)

            st.info("Overlaying audio on video...")
            final_video_path = overlay_audio_on_video(video_path, audio_path)

            st.success("Video generated successfully!")
            with open(final_video_path, "rb") as video_file:
                st.download_button(
                    label="Download Final Video",
                    data=video_file,
                    file_name="final_video.mp4",
                    mime="video/mp4",
                )

            with open(audio_path, "rb") as audio_file:
                st.download_button(
                    label="Download Generated Audio",
                    data=audio_file,
                    file_name="generated_audio" + (".mp3" if language == "ur" else ".wav"),
                    mime="audio/mpeg" if language == "ur" else "audio/wav",
                )
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)
            if 'final_video_path' in locals() and os.path.exists(final_video_path):
                os.remove(final_video_path)
