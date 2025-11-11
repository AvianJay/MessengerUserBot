# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-11-11

### Added - Package Restructuring
- Created `messenger_userbot` package with clean API (like discord.py)
- Added `MessengerBot` class as main client
- Added `MessengerUser` and `MessengerMessage` data models
- Added utility functions for config loading and caching
- Added extensions module with decorators:
  - `@command()` - Command handler decorator
  - `@cooldown(seconds)` - Rate limiting decorator
  - `@requires_owner(owner_id)` - Owner-only command decorator

### Added - Packaging
- Created `setup.py` for package installation
- Created `pyproject.toml` for modern Python packaging
- Created `MANIFEST.in` for distribution
- Package can now be installed with `pip install -e .`

### Added - Examples
- Created `examples/` directory
- Added `simple_bot.py` - Basic bot example
- Added `advanced_bot.py` - Example using extensions
- Moved original bot to `bot_example.py`
- Added `config.example.json` template
- Added comprehensive examples README

### Changed
- Updated main README with package usage instructions
- Moved original `main.py` to `examples/bot_example.py`
- Moved supporting files to `examples/` (server.py, quote.py, exam scripts, fonts, templates)
- Updated `.gitignore` for examples directory

### Migration Guide
**Before:**
```python
# Run main.py directly
python3 main.py
```

**After - Simple Bot:**
```python
from messenger_userbot import MessengerBot

bot = MessengerBot(email='...', password='...', thread_id='...')

@bot.on_message
def handle_message(message):
    if '!hello' in message.message:
        bot.send_message(['Hello!'])

bot.login()
bot.run()
```

**After - Using Original Bot:**
```bash
cd examples
python bot_example.py
```

## Notes
- All original functionality is preserved in `examples/bot_example.py`
- The new package structure makes the code reusable and easier to extend
- API design inspired by discord.py for familiarity
