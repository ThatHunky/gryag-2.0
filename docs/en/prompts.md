# Prompts and Personality

Gryag bot has a unique personality defined by system prompts. It's not just an assistant, but a full-fledged chat participant with its own character.

## Gryag's Personality

- **Identity**: Gryag (@gryag_bot) is a Ukrainian guy in the group chat.
- **Communication Style**: Colloquial Ukrainian, informal style, use of slang and idioms.
- **Character**: Sharp-tongued, sarcastic, with dark humor. He has his own opinions and isn't afraid to voice them.
- **Principles**: Supports Ukraine, avoids officialese, communicates like a real person.

## Available Prompts

The `prompts/` directory contains various system configuration options:

1. **`default.md`**: Main prompt. Defines basic behavior, communication style, and tool usage rules.
2. **`assistant.md`**: A more reserved and helpful version for specific tasks.
3. **`casual.md`**: A very relaxed style for friendly conversation.

## Dynamic Context

The system prompt is automatically supplemented with dynamic data:

- **Chat Info**: Title, type, member count.
- **User Data**: Name, username, pronouns.
- **Memory**: Facts about the user that the bot has remembered in the past.
- **Summarization**: Brief summaries of previous conversations to maintain long-term context.

## Configuration

You can change the active prompt file in `.env` (variable `SYSTEM_PROMPT_FILE`). Prompt files are mounted into the container as `read-only` for stability.
