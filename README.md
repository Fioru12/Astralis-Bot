# 🤖 Astralis Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&style=flat-square)
![Telegram](https://img.shields.io/badge/Telegram-Bot_API-26A5E4?logo=telegram&style=flat-square)
![Docker](https://img.shields.io/badge/Docker-orchestration-2496ED?logo=docker&style=flat-square)
![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
![Status](https://img.shields.io/badge/status-production-green?style=flat-square)

**Advanced Telegram bot for remote server management**  
Control your game servers, Docker containers, and Linux system from anywhere with an intuitive inline keyboard interface.

[🚀 Features](#-features) • [📦 Installation](#-installation) • [🛠️ Tech Stack](#️-tech-stack) • [🔒 Security](#-security)

</div>

---

## ✨ Features

### 🎮 Game Server Management
- Start/stop/restart game servers (Project Zomboid)
- Real-time status monitoring
- Server configuration viewer
- Player count tracking

### 🖥️ System Control
- Reboot/shutdown remote machine
- Screen on/off control
- Real-time CPU, RAM, disk usage
- Temperature monitoring
- Uptime and load average

### 🐳 Docker Orchestration
- List all containers with status
- Start/stop/restart containers
- View container logs
- Resource usage monitoring

### 📊 Monitoring & Notifications
- Live system metrics
- Server status alerts
- Docker container health checks
- Automated notifications

### 🔐 Security
- Chat ID based authorization
- Environment variable configuration
- No hardcoded credentials
- Input validation

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.11+** | Core language |
| **python-telegram-bot** | Telegram Bot API wrapper |
| **asyncio** | Async/await for concurrent operations |
| **Docker** | Containerization |
| **subprocess** | System command execution |
| **logging** | Structured logging |

---

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- Telegram Bot Token (from @BotFather)
- Linux server (Ubuntu/Debian recommended)

### Option 1: Docker (Recommended)
```bash
docker run -d \
  --name astralis-bot \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e TELEGRAM_CHAT_ID=your_chat_id \
  -v /var/run/docker.sock:/var/run/docker.sock \
  fioru12/astralis-bot:latest
```

### Option 2: Manual Installation
```bash
git clone https://github.com/Fioru12/Astralis-Bot.git
cd Astralis-Bot
pip install -r requirements.txt
python bot_telegram.py
```

### Option 3: Systemd Service
```bash
# Copy service file
sudo cp astralis-bot.service /etc/systemd/system/

# Edit with your token and chat ID
sudo nano /etc/systemd/system/astralis-bot.service

# Enable and start
sudo systemctl enable astralis-bot
sudo systemctl start astralis-bot
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ Yes | Bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ Yes | Your Telegram Chat ID for authorization |

### Getting Your Chat ID
1. Start a chat with your bot on Telegram
2. Send any message
3. Check the bot logs or use @getidsbot

---

## 🏗️ Architecture

```
Astralis-Bot/
├── bot_telegram.py          # Main bot application
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container image
├── docker-compose.yml       # Orchestration
├── astralis-bot.service     # Systemd unit file
└── README.md               # Documentation
```

### Key Components

- **Command Handlers**: `/start`, `/help` commands
- **Callback Handlers**: Inline keyboard button presses
- **System Monitor**: CPU, RAM, disk, temperature
- **Docker Manager**: Container lifecycle management
- **Authorization**: Chat ID based access control

---

## 📸 Screenshots

> *Coming soon - bot interface screenshots*

---

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Or with Docker
docker compose -f docker-compose.test.yml up --build
```

---

## 🔒 Security Best Practices

This bot implements several security measures:

1. **Chat ID Authorization**: Only authorized users can interact
2. **Environment Variables**: No hardcoded credentials
3. **Input Validation**: All user inputs are validated
4. **Timeout Protection**: Commands have execution timeouts
5. **Error Handling**: Graceful failure with logging

---

## 🚀 Deployment

### Using Docker Compose
```yaml
version: '3.8'
services:
  astralis-bot:
    build: .
    container_name: astralis-bot
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

### Using Systemd
```ini
[Unit]
Description=Astralis Telegram Bot
After=network.target

[Service]
Type=simple
User=astralis
WorkingDirectory=/opt/astralis-bot
ExecStart=/usr/bin/python3 bot_telegram.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 📈 Roadmap

- [ ] Add webhook support for faster responses
- [ ] Implement user roles and permissions
- [ ] Add scheduled tasks and reminders
- [ ] Multi-language support (i18n)
- [ ] Web dashboard for bot management
- [ ] Integration with monitoring tools (Prometheus, Grafana)

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Fioru12** - [GitHub Profile](https://github.com/Fioru12)

---

<div align="center">
  <sub>Built with ❤️ for efficient server management</sub>
</div>
