import streamlit as st
import json
from fpdf import FPDF
from typing import Optional
from random import randint
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

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
    st.header("How can we help you today?")
    choice = st.radio("Choose an option:", ["Take Patient History", "Get Diagnosis"])
    
    if choice == "Take Patient History":
        st.subheader("Patient History Questionnaire")
        patient_history = {}
        
        # Patient history questions
        questions = {
            "full_name": st.text_input("What is your full name?"),
            "date_of_birth": st.text_input("What is your date of birth?"),
            "gender": st.text_input("What gender do you identify as?"),
            "preferred_language": st.text_input("What is your preferred language, if any?"),
            "preferred_communication": st.text_input("What is your preferred method of communication? (e.g., phone, email, in-person)"),
            "medical_conditions": st.text_input("Do you have any allergies or chronic conditions? If so, please list them."),
            "current_symptoms": st.text_input("Do you have any current symptoms or concerns?"),
            "disabilities": st.text_input("Do you have any disabilities? If so, please describe them."),
            "past_surgeries": st.text_input("Have you had any surgeries in the past? If so, please list them."),
            "past_hospitalizations": st.text_input("Have you had any hospitalizations in the past? If so, please list them."),
            "past_illnesses": st.text_input("Have you had any major illnesses in the past? If so, please list them."),
            "family_history": st.text_input("Do you have any family history of major illnesses? If so, please list them."),
            "mental_health_history": st.text_input("Do you have any history of mental health conditions, substance abuse, domestic violence or abuse, sexual abuse, PTSD, self-harm, eating disorders, sleep disorders, chronic pain, heart disease, or any other illnesses? If so, please describe them."),
            "tobacco_use": st.text_input("Do you smoke or use tobacco products? If so, how often?"),
            "alcohol_use": st.text_input("Do you consume alcohol? If so, how often?"),
            "drug_use": st.text_input("Do you use recreational drugs? If so, how often?"),
            "dietary_restrictions": st.text_input("Do you have any dietary restrictions?"),
            "mental_health_diagnosis": st.text_input("Have you ever been diagnosed or treated for a mental health condition?"),
            "recent_mental_health": st.text_input("Have you felt anxious, depressed, or hopeless in the last 2 weeks?"),
            "covid_history": st.text_input("Have you ever tested positive for COVID-19?"),
            "long_covid": st.text_input("Did you experience long-term symptoms such as fatigue, brain fog, or breathing issues?"),
            "current_covid_symptoms": st.text_input("Do you still experience any COVID-related symptoms today?"),
            "primary_care": st.text_input("Do you have a primary care provider?"),
            "primary_care_duration": st.text_input("How long have you been seeing your primary care provider?"),
            "care_plan": st.text_input("Are you following a care plan created with a doctor?"),
            "medication_review": st.text_input("Are your medications reviewed regularly by a healthcare professional?"),
            "health_management": st.text_input("Do you feel confident managing your own health?"),
            "support_needs": st.text_input("Do you need assistance from others to manage your health (e.g., emotional, financial, physical)?"),
            "insurance_coverage": st.text_input("Do you have insurance that covers your current health needs?")
        }
        
        if st.button("Submit History"):
            # Save all answers that were provided
            patient_history = {q: a for q, a in questions.items() if a}
            save_patient_info(patient_history, "patient_history.json")
            
            # Generate PDF with questions and answers
            pdf = FPDF()
            pdf.add_page()
            
            # Header with logo space and title
            pdf.set_font("Arial", 'B', size=16)
            pdf.cell(200, 10, txt="Patient Summary Report", ln=True, align='C')
            pdf.ln(5)
            
            # Add current date
            pdf.set_font("Arial", size=10)
            from datetime import datetime
            current_date = datetime.now().strftime("%B %d, %Y")
            pdf.cell(200, 10, txt=f"Generated on: {current_date}", ln=True, align='C')
            pdf.ln(10)
            
            # Group questions by category
            categories = {
                "Personal Information": ["full_name", "date_of_birth", "gender", "preferred_language", "preferred_communication"],
                "Medical History": ["medical_conditions", "current_symptoms", "disabilities", "past_surgeries", "past_hospitalizations", "past_illnesses", "family_history"],
                "Mental Health": ["mental_health_history", "mental_health_diagnosis", "recent_mental_health"],
                "COVID-19 History": ["covid_history", "long_covid", "current_covid_symptoms"],
                "Lifestyle": ["tobacco_use", "alcohol_use", "drug_use", "dietary_restrictions"],
                "Healthcare Management": ["primary_care", "primary_care_duration", "care_plan", "medication_review", "health_management", "support_needs", "insurance_coverage"]
            }
            
            # Create sections for each category
            for category, fields in categories.items():
                pdf.set_font("Arial", 'B', size=14)
                pdf.set_fill_color(240, 248, 241)  # Light green background
                pdf.cell(0, 10, category, ln=True, fill=True)
                pdf.ln(5)
                
                pdf.set_font("Arial", size=12)
                for field in fields:
                    if field in patient_history and patient_history[field]:
                        # Make the question more readable
                        question = field.replace('_', ' ').title()
                        pdf.set_font("Arial", 'B', size=11)
                        pdf.multi_cell(0, 7, question)
                        pdf.set_font("Arial", size=11)
                        pdf.multi_cell(0, 7, patient_history[field])
                        pdf.ln(3)
                pdf.ln(5)
            
            pdf.output("patient_history.pdf")
            
            # Provide download button
            with open("patient_history.pdf", "rb") as file:
                st.download_button(
                    label="Download Patient History PDF",
                    data=file,
                    file_name="patient_history.pdf",
                    mime="application/pdf"
                )
    
    else:  # Get Diagnosis
        st.subheader("Symptom Analysis")
        symptoms = st.text_area("Describe your symptoms:")
        pain_rating = st.slider("Rate your pain (1-10):", 1, 10)
        # Initialize session state for analysis results if not exists
        if 'analysis_complete' not in st.session_state:
            st.session_state.analysis_complete = False
            st.session_state.analysis_result = None

        if st.button("Process Symptoms") or st.session_state.analysis_complete:
            if not st.session_state.analysis_complete:
                with st.spinner("Analyzing symptoms..."):
                    result = process_symptoms(f"{symptoms} (Pain level: {pain_rating}/10)")
                    st.session_state.analysis_result = result
                    st.session_state.analysis_complete = True
            else:
                result = st.session_state.analysis_result
            
            st.subheader("Analysis Results")
            
            st.write("**Potential Causes:**")
            for reason in result["reasons"]:
                st.write(f"• {reason}")
            
            st.write("\n**Life-Threatening Assessment:**")
            st.write(result.get("life_threatening", "Assessment unavailable"))
            
            risk_rating = result["risk_rating"]
            st.write("\n**Risk Rating:**", risk_rating, "/10")
                
            # Visual risk indicator and recommended actions
            if risk_rating >= 7:
                st.error(f"⚠️ High Risk ({risk_rating}/10)")
                st.error("**Recommended Action:** 🚑 Seek immediate medical attention or call emergency services. Your symptoms suggest a potentially serious condition that requires urgent medical evaluation.")
            elif risk_rating >= 4:
                st.warning(f"⚠️ Moderate Risk ({risk_rating}/10)")
                st.warning("**Recommended Action:** 👨‍⚕️ Schedule an appointment with your healthcare provider within the next 24-48 hours. In the meantime:\n- Rest and avoid strenuous activity\n- Monitor your symptoms for any changes\n- Keep track of any new symptoms")
            else:
                st.success(f"✓ Low Risk ({risk_rating}/10)")
                st.info("**Recommended Action:** 🏡 Your condition can likely be managed at home. Consider:\n- Over-the-counter medications if appropriate\n- Rest and hydration\n- Apply ice/heat as needed\n- Monitor symptoms and seek medical attention if they worsen")
            
            if risk_rating >= 8:
                st.error("🚨 EMERGENCY: Please call emergency services or go to the nearest emergency room immediately!")
            
            st.markdown("---")  # Add a separator
            if st.button("Schedule Appointment 👨‍⚕️"):
                st.session_state.analysis_complete = False  # Reset for next time
                st.session_state.page = "Appointment"
                st.rerun()

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