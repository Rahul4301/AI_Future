import streamlit as st
import pyaudio
import wave
import os
import time
import speech_recognition as sr
from datetime import datetime
from gtts import gTTS
import tempfile
from playsound import playsound
import threading

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.frames = []
        
    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK)
        
        # Start recording in a separate thread
        self.record_thread = threading.Thread(target=self._record)
        self.record_thread.start()
    
    def _record(self):
        while self.is_recording:
            data = self.stream.read(CHUNK)
            self.frames.append(data)
    
    def stop_recording(self, filename):
        self.is_recording = False
        if hasattr(self, 'record_thread'):
            self.record_thread.join()
        
        # Stop and close the stream
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        
        # Save the recorded data as a WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.frames))
        
        # Transcribe the recording
        return transcribe_audio(filename)

def text_to_speech(text, lang='en'):
    """Convert text to speech and play it"""
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_filename = fp.name
        
        # Generate speech
        tts = gTTS(text=text, lang=lang)
        tts.save(temp_filename)
        
        # Play the generated speech
        st.info("🔊 Playing speech...")
        playsound(temp_filename)
        st.success("✅ Playback complete!")
        
        # Clean up
        os.remove(temp_filename)
        
    except Exception as e:
        st.error(f"Error in text-to-speech: {str(e)}")

def transcribe_audio(filename):
    """Transcribe the audio file using Google Speech Recognition"""
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Speech could not be recognized"
        except sr.RequestError:
            return "Could not request results"

def play_audio(filename):
    # Open the wave file
    with wave.open(filename, 'rb') as wf:
        # Instantiate PyAudio
        p = pyaudio.PyAudio()
        
        # Open stream
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                       channels=wf.getnchannels(),
                       rate=wf.getframerate(),
                       output=True)
        
        st.info("🔊 Playing audio...")
        
        # Read data in chunks and play
        data = wf.readframes(CHUNK)
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(CHUNK)
            
        st.success("✅ Playback complete!")
        
        # Close stream
        stream.stop_stream()
        stream.close()
        p.terminate()

def main():
    st.title("🎙️ Audio Recorder and Player")
    
    if not os.path.exists("recordings"):
        os.makedirs("recordings")
    
    # Initialize recorder in session state if not exists
    if 'recorder' not in st.session_state:
        st.session_state.recorder = AudioRecorder()
        st.session_state.recording = False
    
    # Recording section
    st.header("Record Audio")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎤 Start Recording", disabled=st.session_state.recording):
            st.session_state.recording = True
            st.session_state.recorder.start_recording()
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Recording", disabled=not st.session_state.recording):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recordings/audio_{timestamp}.wav"
            
            transcript = st.session_state.recorder.stop_recording(filename)
            st.session_state.recording = False
            
            if transcript and transcript != "Speech could not be recognized":
                st.subheader("Transcript:")
                st.write(transcript)
                st.session_state.current_transcript = transcript
                st.rerun()
    
    # Show recording status
    if st.session_state.recording:
        st.info("🎤 Recording in progress...")
    
    # Playback section
    st.header("Play Recordings")
    
    recordings = [f for f in os.listdir("recordings") if f.endswith('.wav')]
    
    if recordings:
        selected_file = st.selectbox(
            "Select a recording to play",
            recordings,
            format_func=lambda x: x.replace("audio_", "Recording ").replace(".wav", "")
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Play Recording"):
                play_audio(os.path.join("recordings", selected_file))
        
        with col2:
            if st.button("📝 Transcribe"):
                transcript = transcribe_audio(os.path.join("recordings", selected_file))
                if transcript != "Speech could not be recognized":
                    st.session_state.current_transcript = transcript
                    st.subheader("Transcript:")
                    st.write(transcript)
                else:
                    st.error("Could not transcribe the audio. Please try again.")
        
        with col3:
            if st.button("🔊 Read Transcript", key="read_saved"):
                if 'current_transcript' in st.session_state:
                    text_to_speech(st.session_state.current_transcript)
                else:
                    st.warning("Please transcribe the recording first.")
        
        # Add download button
        with open(os.path.join("recordings", selected_file), 'rb') as file:
            st.download_button(
                label="⬇️ Download Recording",
                data=file,
                file_name=selected_file,
                mime="audio/wav"
            )
    else:
        st.info("No recordings available. Make a recording first!")

if __name__ == "__main__":
    main()
