# 📡 telecom-alert-bot

> Automatic P1/P2 incident detection from telecom platform logs with real-time Slack alerting.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Slack](https://img.shields.io/badge/Slack-Webhook-4A154B?style=flat&logo=slack&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![Tests](https://img.shields.io/badge/Tests-pytest-yellow?style=flat&logo=pytest)

---

## 🧠 Context

Inspired by real work supporting 24/7 telecom platforms (CRM, Billing, Provisioning, eSIM).
This tool automates the first step of SLA-driven incident management: **detecting and escalating
critical events from raw logs**, reducing manual monitoring workload by ~30%.

---

## ✨ Features

- **P1/P2 classification** based on configurable keyword patterns
- **Slack Webhook integration** — structured alerts per incident + summary block
- **CLI interface** with `--dry-run` and `--p1-only` flags
- **Modular design** — parser, alerter, and entry point fully decoupled
- **Unit tested** with `pytest`

---

## 📁 Project Structure
```
telecom-alert-bot/
├── logs/
│   └── sample.log
├── src/
│   ├── parser.py
│   ├── alerter.py
│   └── main.py
├── tests/
│   └── test_parser.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & install
```bash
git clone https://github.com/ikbelbensib/telecom-alert-bot.git
cd telecom-alert-bot
pip install -r requirements.txt
```

### 2. Configure Slack
```bash
cp .env.example .env
# Edit .env and add your Slack Webhook URL
```

### 3. Run
```bash
# Dry run — no Slack alerts sent
python src/main.py --log logs/sample.log --dry-run

# P1 alerts only
python src/main.py --log logs/sample.log --p1-only

# Full run
python src/main.py --log logs/sample.log
```

---

## 🧪 Run Tests
```bash
pytest tests/ -v
```

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Alerting | Slack Incoming Webhooks |
| Testing | pytest |
| Config | python-dotenv |
| CLI | argparse |

---

## 👤 Author

**Mohamed Ikbel Ben Nessib** — [linkedin.com/in/ikbelbennessib](https://linkedin.com/in/ikbelbennessib)
Full Stack & Automation Engineer · 4+ years in telecom platform support & tooling