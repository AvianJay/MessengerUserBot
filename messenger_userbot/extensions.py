"""
Extensions and helper decorators for messenger_userbot
"""
import functools


def command(prefix='!'):
    """
    Decorator to create command handlers.
    
    Usage:
        @command()
        def hello(bot, message, args):
            bot.send_message(['Hello!'])
    
    Then register it:
        @bot.on_message
        def handle(message):
            hello.check_and_execute(bot, message)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        def check_and_execute(bot, message, *extra_args):
            """Check if message is this command and execute it"""
            if message.sender.is_self():
                return False
            
            parts = message.message.strip().split()
            if len(parts) == 0:
                return False
            
            cmd_name = f"{prefix}{func.__name__}"
            if parts[0] == cmd_name:
                args = parts[1:] if len(parts) > 1 else []
                func(bot, message, args, *extra_args)
                return True
            return False
        
        wrapper.check_and_execute = check_and_execute
        wrapper.command_name = f"{prefix}{func.__name__}"
        return wrapper
    
    return decorator


def requires_owner(owner_id):
    """
    Decorator to restrict command to bot owner only.
    
    Usage:
        @requires_owner(123456789)
        def admin_command(bot, message, args):
            bot.send_message(['Admin action!'])
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(bot, message, *args, **kwargs):
            if message.sender.id != owner_id:
                bot.send_message(['你沒有權限使用這個指令。'])
                return
            return func(bot, message, *args, **kwargs)
        return wrapper
    return decorator


def cooldown(seconds):
    """
    Decorator to add cooldown to commands (per user).
    
    Usage:
        @cooldown(60)
        def limited_command(bot, message, args):
            bot.send_message(['This command has cooldown!'])
    """
    cooldowns = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(bot, message, *args, **kwargs):
            import time
            user_id = message.sender.id
            current_time = time.time()
            
            if user_id in cooldowns:
                time_left = cooldowns[user_id] - current_time
                if time_left > 0:
                    bot.send_message([f'請等待 {int(time_left)} 秒後再使用此指令。'])
                    return
            
            cooldowns[user_id] = current_time + seconds
            return func(bot, message, *args, **kwargs)
        return wrapper
    return decorator
