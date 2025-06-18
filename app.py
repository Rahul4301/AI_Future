import streamlit as st
import json
from fpdf import FPDF
from typing import Optional
from random import randint
import requests
import os
from dotenv import load_dotenv
import pyaudio
import wave
import speech_recognition as sr
from datetime import datetime
from gtts import gTTS
import tempfile
from playsound import playsound
import threading

# Load environment variables
load_dotenv()

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

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
    
    def stop_recording(self):
        self.is_recording = False
        if hasattr(self, 'record_thread'):
            self.record_thread.join()
        
        # Stop and close the stream
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        
        # Create a temporary file for the recording
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as fp:
            temp_filename = fp.name
            
        # Save the recorded data as a WAV file
        with wave.open(temp_filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.frames))
        
        # Transcribe the recording
        text = transcribe_audio(temp_filename)
        os.remove(temp_filename)
        return text

def text_to_speech(text: str):
    """Convert text to speech and play it"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            temp_filename = fp.name
        
        tts = gTTS(text=text)
        tts.save(temp_filename)
        playsound(temp_filename)
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

def get_doctor_response(conversation_history: list) -> str:
    """Get AI doctor's response using Gemini API"""
    headers = {
        "Content-Type": "application/json"
    }
    
    # Count patient responses to track conversation stage
    patient_responses = len([entry for entry in conversation_history if entry['role'] == 'patient'])
    
    if patient_responses <= 2:
        # Initial responses - ask key diagnostic questions
        prompt = f"""You are a concise medical doctor. Based on the patient's symptoms, ask ONE critical follow-up question.
        Focus on: severity, duration, or key distinguishing symptoms. Keep your response to 1-2 sentences maximum.
        
        Conversation history:
        {[f"{'Doctor' if entry['role'] == 'doctor' else 'Patient'}: {entry['text']}" for entry in conversation_history]}
        """
    else:
        # Provide diagnosis
        prompt = f"""You are a concise medical doctor. Based on the symptoms described, provide a clear diagnosis with:
        1. Medical term (in parentheses)
        2. Simple explanation in everyday language
        3. One key recommendation
        
        Keep the entire response under 4 short sentences. Be direct and clear.
        
        Conversation history:
        {[f"{'Doctor' if entry['role'] == 'doctor' else 'Patient'}: {entry['text']}" for entry in conversation_history]}
        """
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        query_params = {"key": GEMINI_API_KEY}
        response = requests.post(
            GEMINI_API_URL,
            params=query_params,
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return "I apologize, but I'm having trouble processing your response. Could you please repeat that?"
    except Exception as e:
        return f"I apologize, but I'm experiencing some technical difficulties. Please try again or describe your symptoms in text."

def process_symptoms(symptoms: str) -> dict:
    """Process symptoms using Gemini API and return potential reasons and risk rating."""
    headers = {
        "Content-Type": "application/json"
    }
    
    prompt = f"""Given these symptoms, please analyze:
    Symptoms: {symptoms}
    
    Please respond in this format:
    Potential Causes:
    - [cause 1]
    - [cause 2]
    - [cause 3]
    
    Life-Threatening Assessment:
    [Yes/No] - [brief explanation]
    
    Risk Rating: [1-10]
    """
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }

    try:
        query_params = {"key": GEMINI_API_KEY}
        response = requests.post(
            GEMINI_API_URL,
            params=query_params,
            json=payload,
            headers=headers
        )
        
        # Print response for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        response.raise_for_status()
        
        data = response.json()
        if 'candidates' in data and len(data['candidates']) > 0:
            response_text = data['candidates'][0]['content']['parts'][0]['text']
            
            # Parse the response
            reasons = []
            risk_rating = 5  # Default risk rating
            life_threatening = "No assessment available"
            
            sections = response_text.split('\n')
            
            # Extract information
            for line in sections:
                if line.strip().startswith('-'):
                    reasons.append(line.strip('- ').capitalize())
                elif 'risk rating:' in line.lower():
                    try:
                        risk_rating = int(''.join(filter(str.isdigit, line)))
                    except ValueError:
                        risk_rating = 5
                elif 'life-threatening' in line.lower():
                    life_threatening = line.split(':')[-1].strip()
            
            if not reasons:
                reasons = ["No specific causes identified"]
            
            return {
                "reasons": reasons,
                "risk_rating": risk_rating,
                "life_threatening": life_threatening
            }
        else:
            st.error("Unable to get a response from the AI service. Please try again.")
            return {
                "reasons": ["Unable to analyze symptoms. Please try again or contact support."],
                "risk_rating": 0,
                "life_threatening": "Assessment unavailable"
            }
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the AI service: {str(e)}")
        return {
            "reasons": ["Unable to process symptoms. Please try again later."],
            "risk_rating": 0,
            "life_threatening": "Assessment unavailable"
        }
    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        return {
            "reasons": ["System error. Please try again or contact support."],
            "risk_rating": 0,
            "life_threatening": "Assessment unavailable"
        }

# Save patient information locally
def save_patient_info(data: dict, filename: str):
    with open(filename, 'w') as file:
        json.dump(data, file)

# Generate PDF summary
def generate_pdf_summary(data: dict, filename: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Patient History Summary", ln=True, align='C')
    for key, value in data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
    pdf.output(filename)

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = "User Info"

# Multi-page app
st.title(" AI Health Assistant")

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        background-color: #2E7D32;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1B5E20;
    }
    div.stRadio > div {
        background-color: #F0F8F1;
        padding: 1rem;
        border-radius: 8px;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
    .stTextArea>div>div>textarea {
        border-radius: 8px;
    }
    .main {
        background-color: #FFFFFF;
    }
    .st-emotion-cache-18ni7ap {
        background-color: #F0F8F1;
    }
    div[data-testid="stHeader"] {
        background-color: #FFFFFF;
    }
    .css-10trblm {
        color: #2E7D32;
    }
    div[data-baseweb="select"] > div {
        border-radius: 8px;
    }
    /* Remove background color from slider */
    div.stSlider > div[data-baseweb="slider"] > div {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

if st.session_state.page == "User Info":
    st.header("User Information")
    name = st.text_input("Enter your name:")
    dob = st.date_input("Enter your date of birth:")
    if st.button("Next"):
        save_patient_info({"name": name, "dob": str(dob)}, "user_info.json")
        st.session_state.page = "Insurance Info"
        st.rerun()

elif st.session_state.page == "Insurance Info":
    st.header("Insurance Information")
    insurance_name = st.text_input("Enter your insurance name:")
    insurance_id = st.text_input("Enter your insurance ID:")
    if st.button("Next"):
        save_patient_info({"insurance_name": insurance_name, "insurance_id": insurance_id}, "insurance_info.json")
        st.session_state.page = "Symptoms"
        st.rerun()

elif st.session_state.page == "Symptoms":
    st.header("Symptom Analysis")

    # Initialize conversation history if not exists
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'recorder' not in st.session_state:
        st.session_state.recorder = AudioRecorder()
        st.session_state.recording = False

    # Add tabs for different input methods
    tab1, tab2 = st.tabs(["💬 Talk to Doctor", "📝 Text Description"])

    with tab1:
        st.subheader("Have a Conversation with AI Doctor")
        
        # Display conversation history
        for entry in st.session_state.conversation_history:
            if entry['role'] == 'doctor':
                st.write("👨‍⚕️ Doctor:", entry['text'])
            else:
                st.write("🤒 You:", entry['text'])
        
        # Initialize conversation if empty
        if len(st.session_state.conversation_history) == 0:
            initial_question = "Hello, I'm your AI doctor today. What brings you in today?"
            st.session_state.conversation_history.append({
                'role': 'doctor',
                'text': initial_question
            })
            text_to_speech(initial_question)
            st.rerun()
        
        # Recording controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎤 Start Recording", disabled=st.session_state.recording):
                st.session_state.recording = True
                st.session_state.recorder.start_recording()
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop Recording", disabled=not st.session_state.recording):
                patient_response = st.session_state.recorder.stop_recording()
                st.session_state.recording = False
                
                if patient_response and patient_response != "Speech could not be recognized":
                    # Add patient's response to conversation
                    st.session_state.conversation_history.append({
                        'role': 'patient',
                        'text': patient_response
                    })
                    
                    # Get and speak doctor's response
                    doctor_response = get_doctor_response(st.session_state.conversation_history)
                    st.session_state.conversation_history.append({
                        'role': 'doctor',
                        'text': doctor_response
                    })
                    text_to_speech(doctor_response)
                    st.rerun()
        
        # Show recording status
        if st.session_state.recording:
            st.info("🎤 Recording in progress...")
        
        # End consultation button
        if len(st.session_state.conversation_history) > 2:
            if st.button("End Consultation"):
                # Process all symptoms from the conversation
                full_symptoms = " ".join([entry['text'] for entry in st.session_state.conversation_history if entry['role'] == 'patient'])
                diagnosis = process_symptoms(full_symptoms)
                
                # Save consultation data
                consultation_data = {
                    "conversation": st.session_state.conversation_history,
                    "diagnosis": diagnosis
                }
                save_patient_info(consultation_data, "patient_history.json")
                
                # Generate PDF summary
                generate_pdf_summary({
                    "Conversation": st.session_state.conversation_history,
                    "Final Diagnosis": diagnosis
                }, "patient_summary.pdf")
                
                st.success("Consultation completed! A summary has been saved.")
                st.session_state.conversation_history = []
                st.rerun()

    with tab2:
        st.subheader("Describe Your Symptoms")
        
        # Symptom description
        symptoms = st.text_area("Please describe your symptoms in detail:")
        
        # Symptom severity
        severity = st.slider("On a scale of 1-10, how severe are your symptoms?", 1, 10, 5)
        
        # Duration
        duration_unit = st.selectbox("How long have you been experiencing these symptoms?", 
                                   ["Hours", "Days", "Weeks", "Months"])
        duration_number = st.number_input("Number of " + duration_unit.lower(), 
                                        min_value=1, max_value=100, value=1)
        
        full_description = f"{symptoms}\nSeverity: {severity}/10\nDuration: {duration_number} {duration_unit}"
        
        if st.button("Get Diagnosis"):
            if symptoms:
                diagnosis = process_symptoms(full_description)
                
                # Display diagnosis in a formatted box
                st.markdown("""
                    <style>
                        .diagnosis-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0; }
                        .risk-low { color: #28a745; }
                        .risk-medium { color: #ffc107; }
                        .risk-high { color: #dc3545; }
                    </style>
                """, unsafe_allow_html=True)
                
                st.markdown('<div class="diagnosis-box">', unsafe_allow_html=True)
                
                st.subheader("📋 Diagnosis Results")
                
                # Display potential causes with bullet points
                st.write("**Potential Causes:**")
                for reason in diagnosis["reasons"]:
                    st.write(f"• {reason}")
                
                # Display risk assessment with color coding
                risk_level = diagnosis["risk_rating"]
                risk_class = "risk-high" if risk_level > 7 else "risk-medium" if risk_level > 4 else "risk-low"
                st.markdown(f'<p><strong>Risk Level:</strong> <span class="{risk_class}">{risk_level}/10</span></p>', 
                          unsafe_allow_html=True)
                
                # Display life-threatening assessment with emphasis
                is_life_threatening = "Yes" in diagnosis["life_threatening"]
                threat_class = "risk-high" if is_life_threatening else "risk-low"
                st.markdown(f'<p><strong>Life-Threatening Assessment:</strong> <span class="{threat_class}">{diagnosis["life_threatening"]}</span></p>', 
                          unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Add scheduling section if risk is high or moderate
                if risk_level > 4:
                    st.markdown("""
                        <style>
                            .appointment-box {
                                background-color: #e9ecef;
                                padding: 20px;
                                border-radius: 10px;
                                margin: 20px 0;
                                border-left: 5px solid #2E7D32;
                            }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                        <div class="appointment-box">
                        <h3>📋 Appointment Details</h3>
                        <p><strong>Doctor:</strong> Dr. AIbert</p>
                        <p><strong>Consultation Type:</strong> Video Call</p>
                        <p><strong>Available:</strong> Within 24 hours</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("💡 A confirmation email will be sent with the video consultation link.")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Schedule Consultation"):
                            st.success("✅ Video consultation scheduled! Check your email for details.")
                    with col2:
                        if st.button("Urgent Care Locations"):
                            st.info("🏥 Showing nearby urgent care facilities...")
                
                # Save the diagnosis
                save_patient_info({
                    "symptoms": full_description,
                    "diagnosis": diagnosis,
                    "severity": severity,
                    "duration": f"{duration_number} {duration_unit}"
                }, "patient_history.json")
                
                # Generate PDF summary
                generate_pdf_summary({
                    "Symptoms": full_description,
                    "Diagnosis": diagnosis,
                    "Severity": f"{severity}/10",
                    "Duration": f"{duration_number} {duration_unit}"
                }, "patient_summary.pdf")
                
            else:
                st.warning("Please enter your symptoms first.")
    
elif st.session_state.page == "Appointment":
    st.header("🗓️ Appointment Scheduled")
    
    # Generate random appointment details
    hour = randint(9, 16)  # 9 AM to 4 PM
    minute = randint(0, 11) * 5  # Round to nearest 5 minutes
    am_pm = "AM" if hour < 12 else "PM"
    hour = hour if hour <= 12 else hour - 12
    appointment_time = f"{hour}:{minute:02d} {am_pm}"
    
    # Get tomorrow's date
    from datetime import datetime, timedelta
    appointment_date = (datetime.now() + timedelta(days=1)).strftime("%A, %B %d, %Y")
    
    # Display appointment confirmation with styling
    st.markdown("""
        <style>
        .appointment-box {
            background-color: #F0F8F1;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border: 2px solid #2E7D32;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="appointment-box">
        <h3>📋 Appointment Details</h3>
        <p><strong>Doctor:</strong> Dr. AIbert</p>
        <p><strong>Date:</strong> {appointment_date}</p>
        <p><strong>Time:</strong> {appointment_time}</p>
        <p><strong>Location:</strong> Virtual Consultation</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 A confirmation email will be sent with the video consultation link.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add to Calendar"):
            st.success("✓ Appointment added to your calendar")
    with col2:
        if st.button("Start Over"):
            st.session_state.page = "User Info"
            st.rerun()
