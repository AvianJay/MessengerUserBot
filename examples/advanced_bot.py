"""
Advanced example bot using messenger_userbot with extensions
"""
import sys
import os

# Add parent directory to path to import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from messenger_userbot import MessengerBot, command, requires_owner, cooldown
from messenger_userbot.utils import load_config

# Example configuration
default_config = {
    "email": "your_email@example.com",
    "password": "your_password",
    "thread_id": "123456789",
    "owner_id": 0,  # Set this to your user ID
    "headless": False,
    "use_wdm": True,
}

# Load config
config = load_config("config.json", default_config)

# Check if using default config
if config['email'] == "your_email@example.com":
    print("Please edit config.json with your credentials and thread_id!")
    sys.exit(1)

# Create bot instance
bot = MessengerBot(config=config)


# Define commands using decorators
@command()
def hello(bot, message, args):
    """Simple hello command"""
    bot.send_message([f'Hello {message.sender.name}!'])


@command()
def echo(bot, message, args):
    """Echo command - repeats user's message"""
    if len(args) > 0:
        bot.send_message([' '.join(args)])
    else:
        bot.send_message(['Usage: !echo [text]'])


@command()
@cooldown(30)
def cooldown_test(bot, message, args):
    """Command with 30 second cooldown"""
    bot.send_message(['This command has a 30 second cooldown!'])


@command()
@requires_owner(config.get('owner_id', 0))
def admin(bot, message, args):
    """Admin only command"""
    bot.send_message(['Admin command executed!'])


@command()
def help_cmd(bot, message, args):
    """Show help message"""
    bot.send_message([
        'Available commands:',
        '!hello - Say hello',
        '!echo [text] - Echo your message',
        '!cooldown_test - Test cooldown (30s)',
        '!admin - Admin only command',
        '!help - Show this help',
    ])


# List of all commands
commands = [hello, echo, cooldown_test, admin, help_cmd]


# Register main message handler
@bot.on_message
def handle_message(message):
    """Handle incoming messages"""
    # Ignore messages from self
    if message.sender.is_self():
        return
    
    print(f"Received: {message.sender.name}: {message.message}")
    
    # Try each command
    for cmd in commands:
        if hasattr(cmd, 'check_and_execute'):
            if cmd.check_and_execute(bot, message):
                return  # Command was handled
    
    # If no command matched, you can add other logic here
    # For example, auto-replies or other message processing


if __name__ == '__main__':
    print('Advanced Messenger Bot Example')
    print('Using extensions: @command, @cooldown, @requires_owner')
    
    # Login to Messenger
    bot.login()
    
    # Start the bot
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\nStopping bot...")
        bot.stop()
