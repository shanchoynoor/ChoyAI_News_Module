# Choy News Documentation

This directory contains comprehensive documentation for the Choy News Telegram Bot.

## Contents

- [Installation Guide](installation.md)
- [User Guide](user-guide.md)
- [Developer Guide](developer-guide.md)
- [API Documentation](api-docs.md)
- [Deployment Guide](deployment.md)

## Project Structure

```
choynews/                  # Main package
├── api/                   # API integrations (Telegram, weather, etc.)
├── core/                  # Core business logic
├── data/                  # Data models and persistence
├── services/              # Higher-level services
└── utils/                 # Utility functions
    ├── config.py          # Configuration management
    ├── logging.py         # Logging setup
    └── time_utils.py      # Time-related utilities

bin/                       # Executable scripts
├── choynews              # Main entry point script
└── utils/                # Utility scripts

config/                    # Configuration files
├── requirements.txt       # Dependencies
└── .env.example           # Example environment variables

data/                      # Data storage
├── cache/                 # Cache files
├── db/                    # Database files
└── static/                # Static data files

docs/                      # Documentation
├── api-docs.md            # API documentation
├── deployment.md          # Deployment guide
├── developer-guide.md     # Developer guide
├── installation.md        # Installation guide
└── user-guide.md          # User guide

logs/                      # Log files
├── bot/                   # Bot logs
├── auto_news/             # Auto news service logs
└── errors/                # Error logs

tests/                     # Tests
├── unit/                  # Unit tests
├── integration/           # Integration tests
└── fixtures/              # Test fixtures

tools/                     # Development and deployment tools
├── dev/                   # Development tools
└── deploy/                # Deployment tools
```
