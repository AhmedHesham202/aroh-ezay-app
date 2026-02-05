# 🚌 Aroh Ezay? (How Do I Go?) 🇪🇬

**Aroh Ezay** is a smart transit guide for Cairo's commuters. It bridges the gap between static transportation data and dynamic AI reasoning to provide the most reliable route suggestions in the city of Cairo.

🚀 **Live Demo:** [Check it out on Streamlit Cloud](https://aroh-ezay-app-ghhcm85ovsbq8b7cguthgf.streamlit.app/)

## 🌟 Overview
Navigation in Cairo can be complex. This application simplifies the journey by utilizing a **Hybrid Search Engine**. It first queries a curated local SQLite database for precise microbus and metro routes. If no match is found, it automatically leverages **Google Gemini AI** to generate intelligent, context-aware transit advice.

## ✨ Key Features
- **Hybrid Search Architecture:** Combines structured SQL data with Generative AI fallback.
- **AI-Powered Insights:** Uses **Gemini 1.5 Flash** to provide route suggestions in friendly Egyptian slang.
- **Smart Autocomplete:** Features a dynamic search box for areas and landmarks.
- **Efficiency First:** Includes a **Caching System** that stores AI responses to reduce latency and API costs.
- **Social Ready:** One-tap buttons to copy route details or share them directly via **WhatsApp**.
- **Modern UI:** Responsive design with a native Arabic RTL support and a sleek Dark Mode option.

## 🛠️ Tech Stack
- **Framework:** [Streamlit](https://streamlit.io/)
- **Logic:** Python 3.10+
- **Database:** SQLite (local `aroh_ezay.db`)
- **LLM Integration:** Google Generative AI (Gemini) & Groq (Llama 3 backup)
- **Deployment:** Streamlit Cloud

## 📦 Local Installation

1. **Clone the repository:**

git clone [https://github.com/AhmedHesham202/aroh-ezay-app.git](https://github.com/AhmedHesham202/aroh-ezay-app.git)

2. **Install dependencies:**

pip install -r requirements.txt

4. **Environment Setup: Create a .secrets.toml (for Streamlit) or a .env file and add your keys:**

GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY"
GROQ_API_KEY = "YOUR_GROQ_API_KEY"

4.**Launch the app:**

streamlit run app.py

**Developed with ❤️ to help Egyptians navigate the city.**
