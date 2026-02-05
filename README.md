<div align="center">

# 🚌 Aroh Ezay? (How Do I Go?) 🇪🇬

### *Your Smart Transit Companion for Cairo*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://aroh-ezay-app-ghhcm85ovsbq8b7cguthgf.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)

**Bridging the gap between static transportation data and dynamic AI reasoning for Cairo's commuters**

[Features](#-key-features) • [Demo](#-live-demo) • [Installation](#-installation) • [Tech Stack](#️-tech-stack) • [Usage](#-usage)

</div>

---

## 📖 Overview

Navigating Cairo's complex transit system shouldn't be a puzzle. **Aroh Ezay** simplifies your journey using a powerful **Hybrid Search Engine** that combines:

- 🗄️ **Curated Local Database** — Precise microbus and metro routes from SQLite
- 🤖 **AI-Powered Fallback** — Context-aware suggestions via Google Gemini when exact matches aren't available
- 🇪🇬 **Egyptian-Friendly** — Responses in natural Egyptian slang for authentic local experience

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🔍 **Hybrid Search Architecture**
Combines structured SQL data with Generative AI fallback for comprehensive coverage

### 🧠 **AI-Powered Insights**
Gemini 1.5 Flash generates intelligent route suggestions in friendly Egyptian slang

### ⚡ **Smart Autocomplete**
Dynamic search box with suggestions for Cairo areas and landmarks

</td>
<td width="50%">

### 💾 **Intelligent Caching**
Stores AI responses to reduce latency and API costs

### 📱 **Social Ready**
One-tap buttons to copy routes or share directly via WhatsApp

### 🎨 **Modern UI**
Responsive design with native Arabic RTL support and Dark Mode

</td>
</tr>
</table>

## 🌐 Live Demo

Experience Aroh Ezay in action:

**👉 [Try it on Streamlit Cloud](https://aroh-ezay-app-ghhcm85ovsbq8b7cguthgf.streamlit.app/)**

## 🛠️ Tech Stack

```
Framework:      Streamlit (Python-based web framework)
Language:       Python 3.10+
Database:       SQLite (aroh_ezay.db)
AI Models:      Google Gemini 1.5 Flash (primary) + Groq Llama 3 (backup)
Deployment:     Streamlit Cloud
```

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/AhmedHesham202/aroh-ezay-app.git
   cd aroh-ezay-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**
   
   Create a `.streamlit/secrets.toml` file or `.env` file in the project root:
   
   ```toml
   # .streamlit/secrets.toml
   GOOGLE_API_KEY = "your_gemini_api_key_here"
   GROQ_API_KEY = "your_groq_api_key_here"
   ```

4. **Launch the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   
   Navigate to `http://localhost:8501`

## 🚀 Usage

1. Enter your **starting location** in the search box
2. Enter your **destination**
3. Click **"Find Route"**
4. Get instant route suggestions from the database or AI-generated recommendations
5. Share your route via WhatsApp or copy to clipboard

## 🗂️ Project Structure

```
aroh-ezay-app/
├── app.py                 # Main Streamlit application
├── aroh_ezay.db          # SQLite database (routes & locations)
├── requirements.txt      # Python dependencies
├── .streamlit/
│   └── secrets.toml      # API keys (not in repo)
└── README.md             # This file
```

## 🔑 API Keys

To run the app, you'll need:

- **Google Gemini API Key**: Get it from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Groq API Key** (optional): Get it from [Groq Console](https://console.groq.com/)

## 🤝 Contributing

Contributions are welcome! Whether it's:
- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🌍 Additional city data

Feel free to open an issue or submit a pull request!

## 📄 License

This project is open source and available for educational and personal use.

## 💡 Future Enhancements

- [ ] Multi-city support (Alexandria, Giza, etc.)
- [ ] Real-time traffic integration
- [ ] Crowdsourced route updates
- [ ] Fare estimation
- [ ] Multi-language support (Arabic & English)
- [ ] Offline mode for basic routes
- [ ] Mobile app (iOS & Android)

---

<div align="center">

### Developed with ❤️ to help Egyptians navigate their city

**Made by [Ahmed Hesham](https://github.com/AhmedHesham202)**

⭐ Star this repo if you find it helpful!

</div>
