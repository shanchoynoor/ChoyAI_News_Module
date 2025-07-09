# Developer Guide

This guide provides information for developers who want to contribute to or modify the Choy News Telegram Bot.

## Development Setup

Follow the [installation guide](installation.md) first, then:

1. Install development dependencies:
   ```bash
   pip install -r config/dev-requirements.txt
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Project Structure

The project follows a modular architecture:

```
choynews/                  # Main package
├── api/                   # API integrations
│   ├── __init__.py
│   └── telegram.py        # Telegram API client
├── core/                  # Core business logic
│   ├── __init__.py
│   ├── bot.py             # Bot main functionality
│   └── digest_builder.py  # News digest creation
├── data/                  # Data models and persistence
│   ├── __init__.py
│   ├── crypto_cache.py    # Crypto data caching
│   ├── models.py          # Database models
│   ├── subscriptions.py   # User subscription management
│   └── user_logs.py       # User activity logging
├── services/              # Higher-level services
│   ├── __init__.py
│   └── bot_service.py     # Bot service layer
└── utils/                 # Utility functions
    ├── __init__.py
    ├── config.py          # Configuration management
    ├── logging.py         # Logging setup
    └── time_utils.py      # Time-related utilities
```

## Key Components

### Main Entry Point

The main entry point is in `bin/choynews`, which handles command-line arguments and starts the requested services.

### Telegram Bot

The core bot functionality is in `choynews/core/bot.py`, which defines the `ChoyNewsBot` class responsible for handling Telegram commands and interactions.

### News Digest Builder

The `choynews/core/digest_builder.py` module contains the logic for creating personalized news digests by fetching and formatting content from various sources.

### Data Models

The `choynews/data/models.py` module defines database models and interaction functions for storing user preferences, subscriptions, and logging.

## Adding New Features

### Adding a New Command

1. Add the command handler in `choynews/core/bot.py`:
   ```python
   def handle_new_command(self, update, context):
       # Command implementation
       pass
   ```

2. Register the command in the `__init__` method:
   ```python
   self.dispatcher.add_handler(CommandHandler("newcommand", self.handle_new_command))
   ```

### Adding a New News Source

1. Add the source URL to the configuration in `choynews/utils/config.py`
2. Create a parser function in `choynews/core/digest_builder.py`
3. Add the source to the appropriate category in the digest building logic

## Testing

Run tests using pytest:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/unit/
```

Write new tests in the appropriate directory:
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Test fixtures: `tests/fixtures/`

## Code Style

The project follows PEP 8 guidelines. Ensure your code adheres to these standards.

## Documentation

When adding new features or making significant changes, update the relevant documentation files in the `docs/` directory.
