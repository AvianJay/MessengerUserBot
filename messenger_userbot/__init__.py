"""
MessengerUserBot - A Python library for creating Messenger bots using Selenium
"""

__version__ = "1.0.0"

from .models import MessengerUser, MessengerMessage
from .client import MessengerBot
from .extensions import command, requires_owner, cooldown

__all__ = ['MessengerBot', 'MessengerUser', 'MessengerMessage', 'command', 'requires_owner', 'cooldown']
