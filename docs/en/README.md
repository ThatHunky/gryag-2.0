# Gryag 2.0 - AI Telegram Bot

A comprehensive, dockerized Telegram bot with advanced context management, LLM integration, tool calling, and multimodality.

## Quick Start

1. Copy `.env.example` to `.env` and fill in your credentials:

   ```bash
   cp .env.example .env
   ```

2. Start with Docker:

   ```bash
   docker compose up -d
   ```

3. Check logs:

   ```bash
   docker compose logs -f bot
   ```

## Features

- **Multi-chat support**: Works in private chats and groups
- **Context management**: Remembers conversation history
- **Tool calling**: Calculator, weather, image generation, and more
- **User memory**: Persistent facts about users
- **Admin controls**: Ban, restrict, rate limit via DM commands
- **Multimodal**: Image recognition and generation

## Configuration

See [configuration.md](configuration.md) for all options.

## Documentation

- [Configuration Guide](configuration.md)
- [Deployment Guide](deployment.md)
- [Tools Reference](tools.md)
- [System Prompts](prompts.md)
