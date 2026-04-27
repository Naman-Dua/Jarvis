# 💠 Kora: The Autonomous AI Assistant

Kora (Jarvis 2.0) is a next-generation, local-first AI assistant designed for Windows. She combines a stunning 3D glassmorphic dashboard with autonomous agency, self-healing capabilities, and proactive task management.

---

## 🚀 Python 3.14 (Experimental) Build Success
We have successfully optimized Kora for Python 3.14. 
- **Voice**: Fully working via `sounddevice`.
- **Vision**: Fully working via `mss` (Pillow-free capture).
- **Intelligence**: Powered by Ollama.

---

## 🌟 Core Features

### 🧠 1. Neural Intelligence (Local LLM)
- **Brain**: Powered by **Llama 3.1:8b** via Ollama. 100% private and offline.
- **Emotional Synchrony**: The 3D dashboard reacts to the conversation's sentiment (Calm Blue, Energetic Orange, Warning Red, Positive Pink).
- **Fact Extraction**: Kora autonomously "overhears" and remembers facts about you.

### 👁️ 2. Live Eye (Proactive Vision)
- **Screen Analysis**: Ask "What's on my screen?" and Kora will describe your desktop.
- **Proactivity**: Kora monitors your screen for errors or interesting content and proactively offers help.

### 📅 3. Digital Life Manager
- **Autonomous Scheduling**: Mention an appointment in chat, and she will automatically queue a reminder.
- **Morning Briefing**: A single command (`"Start my day"`) generates a report of weather, news, and todos.

### 🛠️ 4. The Plugin Architect (Self-Evolution)
- **Autonomous Coding**: Kora can write her own Python plugins to expand her skills.
- **Full OS Control**: Native modules for File management, Window control, and Media.

---

## 🚀 Setup & Installation

### 1. Install Dependencies
```bash
ollama pull llama3.1:8b   # Brain
ollama pull moondream     # Vision
pip install -r requirements.txt
```

### 2. Launch Kora
```bash
python main.py
```

### 3. Build Your Own .exe
```bash
pyinstaller --noconfirm --onefile --windowed --name "Kora_AI" --collect-all chromadb main.py
```

---

**Developed with ❤️ by Naman Dua**
