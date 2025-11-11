"""
Data models for Messenger entities
"""
from datetime import datetime


class MessengerUser:
    """Represents a Messenger user"""
    
    def __init__(self, name, avatar, id):
        self.name = name
        self.avatar = avatar
        self.id = id

    def __str__(self):
        return f"{self.name} ({self.id})"

    def __repr__(self):
        return f"MessengerUser(name={self.name}, avatar={self.avatar}, id={self.id})"
    
    def to_dict(self):
        return {
            "name": self.name,
            "avatar": self.avatar,
            "id": self.id
        }
    
    def is_self(self):
        return self.id == 0

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name"),
            avatar=data.get("avatar"),
            id=data.get("id")
        )


class MessengerMessage:
    """Represents a Messenger message"""
    
    def __init__(self, sender: MessengerUser, message, time=None, reply=None):
        self.sender = sender
        self.message = message
        self.time = time if time is not None else datetime.now().timestamp()
        self.reply = reply

    def __str__(self):
        reply_str = f" (reply to {self.reply.sender} : {self.reply.message})" if self.reply else ""
        return f"{self.sender} : {self.message} at {self.time}{reply_str}"

    def __repr__(self):
        return f"MessengerMessage(sender={repr(self.sender)}, message={self.message}, time={self.time}, reply={repr(self.reply)})"
    
    def to_dict(self):
        return {
            "sender": self.sender.to_dict(),
            "message": self.message,
            "time": self.time,
            "reply": self.reply.to_dict() if self.reply else None
        }

    @classmethod
    def from_dict(cls, data):
        sender = MessengerUser.from_dict(data["sender"])
        message = data["message"]
        time_val = data.get("time", datetime.now().timestamp())
        reply = cls.from_dict(data["reply"]) if data.get("reply") else None
        return cls(sender, message, time_val, reply)
