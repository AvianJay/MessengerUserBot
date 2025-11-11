"""
Simple example bot using messenger_userbot package
"""
import sys
import os

# Add parent directory to path to import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from messenger_userbot import MessengerBot
from messenger_userbot.utils import load_config

# Example configuration
default_config = {
    "email": "your_email@example.com",
    "password": "your_password",
    "thread_id": "123456789",
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


# Define message handler
@bot.on_message
def handle_message(message):
    """Handle incoming messages"""
    # Ignore messages from self
    if message.sender.is_self():
        return
    
    print(f"Received message from {message.sender.name}: {message.message}")
    
    # Simple command handling
    msg_parts = message.message.strip().split()
    
    if len(msg_parts) > 0 and msg_parts[0].startswith('!'):
        command = msg_parts[0]
        
        if command == '!hello':
            bot.send_message(['Hello! I am a bot created with messenger_userbot!'])
        
        elif command == '!help':
            bot.send_message([
                'Available commands:',
                '!hello - Say hello',
                '!echo [text] - Echo your message',
                '!help - Show this help'
            ])
        
        elif command == '!echo':
            if len(msg_parts) > 1:
                echo_text = ' '.join(msg_parts[1:])
                bot.send_message([echo_text])
            else:
                bot.send_message(['Usage: !echo [text]'])


if __name__ == '__main__':
    print('Simple Messenger Bot Example')
    
    # Login to Messenger
    bot.login()
    
    # Start the bot
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\nStopping bot...")
        bot.stop()
