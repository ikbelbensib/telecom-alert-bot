# telecom-alert-bot
Script Python qui lit un fichier de logs, détecte des patterns d'incidents (P1/P2), et envoie une alerte Slack. 
telecom-alert-bot/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── logs/
│   └── sample.log
├── src/
│   ├── parser.py       # Lecture & détection des incidents
│   ├── alerter.py      # Envoi Slack
│   └── main.py         # Point d'entrée
└── tests/
    └── test_parser.py
