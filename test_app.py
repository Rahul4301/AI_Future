import pytest
import json
import os
from app import process_symptoms, save_patient_info, generate_pdf_summary
from datetime import datetime

# Test data
MOCK_SYMPTOMS = "headache and fever (Pain level: 5/10)"
MOCK_PATIENT_INFO = {
    "name": "John Doe",
    "dob": "1990-01-01"
}

def test_save_patient_info(tmp_path):
    """Test saving patient information to a JSON file"""
    # Create a temporary file path
    test_file = tmp_path / "test_info.json"
    
    # Test saving data
    save_patient_info(MOCK_PATIENT_INFO, str(test_file))
    
    # Verify file exists and contains correct data
    assert test_file.exists()
    with open(test_file) as f:
        saved_data = json.load(f)
    assert saved_data == MOCK_PATIENT_INFO

def test_generate_pdf_summary(tmp_path):
    """Test PDF summary generation"""
    # Create a temporary file path
    test_file = tmp_path / "test_summary.pdf"
    
    # Generate PDF
    generate_pdf_summary(MOCK_PATIENT_INFO, str(test_file))
    
    # Verify PDF file exists
    assert test_file.exists()
    assert test_file.stat().st_size > 0  # Check if file is not empty

@pytest.mark.asyncio
async def test_process_symptoms():
    """Test symptom processing with mock API response"""
    result = process_symptoms(MOCK_SYMPTOMS)
    
    # Verify the structure of the response
    assert isinstance(result, dict)
    assert "reasons" in result
    assert "risk_rating" in result
    assert "life_threatening" in result
    
    # Verify data types
    assert isinstance(result["reasons"], list)
    assert isinstance(result["risk_rating"], int)
    assert isinstance(result["life_threatening"], str)
    
    # Verify value ranges
    assert 0 <= result["risk_rating"] <= 10

def test_patient_history_categories():
    """Test the patient history categories structure"""
    categories = {
        "Personal Information": ["full_name", "date_of_birth", "gender", "preferred_language", "preferred_communication"],
        "Medical History": ["medical_conditions", "current_symptoms", "disabilities", "past_surgeries", 
                          "past_hospitalizations", "past_illnesses", "family_history"],
        "Mental Health": ["mental_health_history", "mental_health_diagnosis", "recent_mental_health"],
        "COVID-19 History": ["covid_history", "long_covid", "current_covid_symptoms"],
        "Lifestyle": ["tobacco_use", "alcohol_use", "drug_use", "dietary_restrictions"],
        "Healthcare Management": ["primary_care", "primary_care_duration", "care_plan", "medication_review", 
                                "health_management", "support_needs", "insurance_coverage"]
    }
    
    # Verify all expected categories exist
    assert len(categories) == 6
    assert all(isinstance(fields, list) for fields in categories.values())
    
    # Verify no duplicate fields across categories
    all_fields = [field for fields in categories.values() for field in fields]
    assert len(all_fields) == len(set(all_fields))  # No duplicates
