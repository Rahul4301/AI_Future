# 🏥 AI Future - Your Smart Health Assistant

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red.svg)](https://streamlit.io/)

## 🌟 Overview

AI Future is an intelligent healthcare assistant that combines advanced AI diagnostics with voice interaction capabilities. It provides quick medical assessments through both text and voice conversations, maintains patient history, and offers immediate access to healthcare professionals when needed.

## ✨ Features

- 🗣️ **Voice Interaction**: 
  - Natural conversation with AI doctor
  - Speech-to-text for symptom description
  - Text-to-speech for doctor's responses
  - Real-time voice recording and playback

- 🤖 **Smart Symptom Analysis**: 
  - AI-powered symptom evaluation
  - Medical terminology with plain language explanations
  - Concise, focused follow-up questions
  - Clear diagnostic assessments

- 📊 **Comprehensive Assessment**:
  - Severity scale (1-10)
  - Duration tracking
  - Color-coded risk levels
  - Life-threatening condition alerts

- 👨‍⚕️ **Virtual Doctor Access**:
  - Automatic consultation scheduling for medium/high risk cases
  - Video call appointments with Dr. AIbert
  - Urgent care location finder
  - Quick emergency response system

- 📝 **Patient Management**: 
  - Detailed patient history tracking
  - Insurance information management
  - PDF report generation
  - Secure local data storage

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- pip package manager
- Microphone for voice interaction
- Speakers for audio playback

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AI_Future.git
cd AI_Future
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
   - Create a `.env` file in the root directory
   - Add your Gemini API key:
```env
GEMINI_API_KEY=your_api_key_here
```

4. Run the application:
```bash
streamlit run app.py
```

## 💡 How to Use

1. **Choose Interaction Method**:
   - 💬 Talk to Doctor: Natural voice conversation
   - 📝 Text Description: Written symptom description

2. **Voice Interaction Mode**:
   - Click "Start Recording" to speak
   - Describe your symptoms naturally
   - Click "Stop Recording" when finished
   - Listen to doctor's response
   - Continue conversation as needed

3. **Text Description Mode**:
   - Enter detailed symptom description
   - Rate severity (1-10)
   - Specify symptom duration
   - Get instant diagnosis and recommendations

4. **Review and Action**:
   - View color-coded risk assessment
   - Schedule video consultation if needed
   - Access urgent care locations
   - Download PDF summary

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Voice Processing**: 
  - PyAudio for recording
  - SpeechRecognition for text conversion
  - gTTS for text-to-speech
  - Playsound for audio playback
- **AI Integration**: Google Gemini API
- **PDF Generation**: FPDF
- **Data Storage**: Local JSON files

## 📱 Screenshots

[Coming Soon]

## 🤝 Contributing

Contributions are welcome! Please read the [contribution guidelines](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini API for AI capabilities
- Streamlit for the web framework
- PyAudio and related libraries for voice processing
- Open-source community for various dependencies

## 📞 Support

For support, please open an issue in the GitHub repository or contact the maintainers.

---

Made with ❤️ by Rahul