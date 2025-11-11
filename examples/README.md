# Examples

This directory contains example implementations using the `messenger_userbot` package.

## Files

### `simple_bot.py`
A minimal example showing how to create a basic bot with simple command handling.

**Features:**
- Basic command handling (!hello, !help, !echo)
- Message event handling
- Configuration loading

**Usage:**
```bash
cd examples
python simple_bot.py
```

### `bot_example.py`
The original full-featured bot with all commands and features.

**Features:**
- Multiple commands (GPT integration, image quotes, user info, etc.)
- Auto-reply system
- Web server for message logs
- PaGamO integration
- And more...

**Usage:**
```bash
cd examples
python bot_example.py
```

## Setup

1. Install the package:
```bash
pip install -e ..
```

2. Copy and edit configuration:
```bash
cp config.example.json config.json
nano config.json  # Edit with your credentials
```

3. Run an example:
```bash
python simple_bot.py
# or
python bot_example.py
```

## Creating Your Own Bot

Here's a minimal example:

```python
from messenger_userbot import MessengerBot

bot = MessengerBot(
    email='your_email@example.com',
    password='your_password',
    thread_id='your_thread_id'
)

@bot.on_message
def handle_message(message):
    if message.sender.is_self():
        return
    
    if '!ping' in message.message:
        bot.send_message(['Pong!'])

bot.login()
bot.run()
```

## Notes

- The bot uses Selenium WebDriver to interact with Messenger
- First run will require manual login verification
- Cookies are saved for subsequent runs
- Use CTRL+C to stop the bot gracefully
