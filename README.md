# ⚡ J.A.R.V.I.S. — AI Desktop Assistant

<h1 align="center">J.A.R.V.I.S.</h1>

<p align="center">
  <strong>Just A Rather Very Intelligent System</strong>
</p>

<p align="center">
  A futuristic, AI-powered desktop assistant designed to make your computer smarter, more interactive, and easier to control.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13">
  <img src="https://img.shields.io/badge/GUI-PySide6-green?style=for-the-badge" alt="PySide6">
  <img src="https://img.shields.io/badge/AI-Google%20Gemini-orange?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Google Gemini">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
</p>

---

## 🚀 About the Project

J.A.R.V.I.S. is a personal desktop AI assistant built with Python. It combines artificial intelligence, voice interaction, desktop automation, system monitoring, file management, and security-focused operations in one futuristic interface.

Inspired by the intelligent assistant from Iron Man, this project aims to bring a more natural and intelligent computer experience to everyday desktop use.

The goal is simple:

**Make your computer work with you, not just for you.**

## ✨ Features

### 🧠 AI Intelligence
- Google Gemini AI integration.
- AI-powered conversations.
- Intelligent command processing.
- Context-aware assistant interactions.

### 🎙️ Voice & Communication
- Voice input and interaction.
- Text-to-speech capabilities.
- Background voice controller.
- Optional wake-word functionality.

### 🖥️ System Monitoring
- System resource monitoring.
- CPU and memory information.
- System diagnostics.
- Network diagnostics.

### 📁 File Management
- Browse files and folders.
- Copy and move files.
- File operation safety checks.
- Confirmation before sensitive operations.

### ⚙️ Desktop Automation
- Application management.
- Desktop command processing.
- Automation tools.
- System utility operations.

### 🛡️ Security & Safety
- Permission management.
- Safety gateway.
- Confirmation dialogs.
- Activity logging.

### 🧹 System Maintenance
- Temporary file cleanup.
- Recycle Bin management.
- System repair utilities.
- Diagnostic tools.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| PySide6 | Desktop graphical interface |
| Google Gemini | AI integration |
| psutil | System monitoring |
| python-dotenv | Environment configuration |
| sounddevice | Audio input/output |
| NumPy | Numerical processing |
| SciPy | Audio and signal processing |
| OpenWakeWord | Wake-word functionality |
| ONNX Runtime | Model execution |

## 📂 Project Structure

```text
MY_JARVIS/
│
├── assets/
│   └── fonts/
│
├── core/
│   ├── ai_engine.py
│   └── gemini_provider.py
│
├── database/
│
├── interface/
│   ├── panels/
│   ├── chat_dialog.py
│   ├── connected_window.py
│   └── main_window.py
│
├── modules/
│   ├── background_voice_controller.py
│   ├── command_processor.py
│   ├── file_manager.py
│   ├── network_diagnostics.py
│   ├── recycle_bin_manager.py
│   ├── system_diagnostics.py
│   ├── system_monitor.py
│   ├── temp_file_cleaner.py
│   └── voice_engine.py
│
├── safety/
│   ├── confirmation_dialog.py
│   ├── permission_manager.py
│   └── safety_gateway.py
│
├── tests/
│
├── config.py
├── main.py
├── requirements.txt
├── setup jarvis Ai.txt
└── README.md
```

## 💻 Installation Guide

Follow these steps to install JARVIS on your Windows computer.

### Step 1 — Install Python

1. Visit https://www.python.org/downloads/
2. Download Python 3.13.
3. Run the installer.
4. Select **Add Python to PATH**.
5. Click **Install Now**.

### Step 2 — Install Git

1. Visit https://git-scm.com/downloads.
2. Download Git for Windows.
3. Install it using the default options.

### Step 3 — Download JARVIS

Open PowerShell and run:

```powershell
git clone https://github.com/YOUR_USERNAME/JARVIS-AI-Desktop-Assistant.git
```

Replace `YOUR_USERNAME` with your GitHub username.

Enter the project folder:

```powershell
cd JARVIS-AI-Desktop-Assistant
```

### Step 4 — Create a Virtual Environment

```powershell
py -3.13 -m venv .venv
```

### Step 5 — Activate the Environment

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### Step 6 — Install Dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install the required packages:

```powershell
pip install -r requirements.txt
```

### Step 7 — Configure the Gemini API

1. Visit https://aistudio.google.com/apikey.
2. Generate your Gemini API key.
3. Open the JARVIS project folder in VS Code.
4. Create a new file named `.env` in the main project directory.
5. Add your key using the environment variable name expected by the source code.

Example, if the code expects `GEMINI_API_KEY`:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

6. Save the file.

**Security warning:** Never upload your `.env` file or expose your API key publicly.

### Step 8 — Launch JARVIS

Make sure your virtual environment is active.

Run:

```powershell
python main.py
```

JARVIS should now launch!

## 🔄 Running JARVIS Again

You do not need to reinstall the packages every time.

Open PowerShell inside the JARVIS project folder and run:

```powershell
.venv\Scripts\Activate.ps1
python main.py
```

## 🔐 Security Notes

- Keep your Gemini API key private.
- Never upload `.env` files.
- Do not upload your `.venv` folder.
- Review sensitive operations before confirming them.
- Use your own API key when setting up JARVIS on another computer.

## 🧪 Testing

The project includes a `tests/` directory containing tests for selected components, including:

- File manager safety.
- Permission management.
- Recycle Bin management.
- Safety gateway.
- Temporary file cleanup.

Run the automated tests using:

```powershell
python -m pytest
```

Install pytest first if it is not already available:

```powershell
pip install pytest
```

## 🗺️ Future Development

JARVIS is an evolving project. Planned improvements may include:

- More advanced AI capabilities.
- Improved voice recognition.
- Expanded desktop automation.
- Enhanced system diagnostics.
- More intelligent command execution.
- Additional safety and permission controls.
- Further interface improvements.

## 🤝 Contributing

Suggestions, bug reports, and improvements are welcome.

If you want to contribute:

1. Fork the repository.
2. Create a new branch.
3. Make your improvements.
4. Test your changes.
5. Submit a Pull Request.

## ⚠️ Disclaimer

JARVIS is an independent personal software project inspired by the fictional AI assistant from Iron Man. It is not affiliated with, endorsed by, or connected to Marvel, Disney, or OpenAI.

Some features may require internet access, additional permissions, or external API services.

## 👨‍💻 Developer

**JARVIS Development Team**

Built with Python, curiosity, and a vision for a smarter desktop experience.

---

<p align="center">
  <strong>⚡ INITIALIZING J.A.R.V.I.S. ...</strong>
  <br>
  <em>Your desktop. Your assistant. Your intelligence.</em>
</p>
