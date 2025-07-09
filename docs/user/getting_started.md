# Getting Started with Choy News

This guide will help you set up and start using Choy News.

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r config/requirements.txt`
3. Configure your environment: `cp config/.env.example .env`
4. Edit `.env` with your API keys and settings
5. Run the application: `./bin/choynews`

## Basic Usage

- To run just the bot: `./bin/choynews --service bot`
- To run just the auto news service: `./bin/choynews --service auto`
- To run both (default): `./bin/choynews`

## Configuration

See `config/.env.example` for all available configuration options.
