# Kora - AI Desktop Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/AI-Desktop%20Assistant-black?style=for-the-badge" alt="AI Assistant">
  <img src="https://img.shields.io/badge/Voice-Controlled-success?style=for-the-badge" alt="Voice Controlled">
</p>

Kora is a modular desktop assistant built with Python. It combines voice input, command routing, automation, memory, and a GUI to provide a practical base for building advanced assistant workflows.

## Features

- Voice command capture and transcription
- Command routing through a centralized brain module
- Desktop action execution (apps/web tasks)
- Reminder and scheduling workflows
- Screen capture and analysis support
- Persistent memory with SQLite
- PyQt-based interactive dashboard

## Architecture

| Module | Purpose |
| --- | --- |
| `main.py` | Application entry point and runtime orchestration |
| `brain.py` | Decision-making and conversation handling |
| `ears.py` | Voice capture and speech-to-text pipeline |
| `voice.py` | Text-to-speech output |
| `actions.py` | System and browser action execution |
| `tasks.py` | Reminder/task parsing and scheduling |
| `mode_select.py` | Runtime mode selection dialog |
| `search_engine.py` | Web lookup and information retrieval |
| `screen_analysis.py` | Screen capture and vision-style analysis |
| `storage.py` | SQLite persistence and memory management |
| `gui.py` | Desktop interface and visualization |

## Project Flow

<img width="1411" height="1337" alt="Kora architecture flow" src="https://github.com/user-attachments/assets/f126f5c1-e4cf-480e-8d36-44f51d96402e" />

## Quick Start

### 1) Clone the repository

```bash
git clone https://github.com/Naman-Dua/Jarvis.git
cd Jarvis
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Run Kora

```bash
python main.py
```

## Requirements

- Python 3.10+
- Working microphone input
- Internet connection for features that depend on web/model calls

## Configuration

- Store API keys and environment-specific settings in a `.env` file.
- Keep secrets out of source control.

## Roadmap

- Deeper LLM integration for richer responses
- Improved context-aware long-term memory
- Browser automation extensions
- Remote/mobile control support
- Enhanced UI/UX and telemetry

## Contributing

Contributions are welcome. If you want to improve Kora:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

## Author

Naman Dua  
GitHub: [Naman-Dua](https://github.com/Naman-Dua)

## Support

If this project helps you, please consider:

- Starring the repository
- Forking it
- Sharing it with others
