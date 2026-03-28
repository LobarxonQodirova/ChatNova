"""
Re-export ChatConsumer from the chat app for backward compatibility
with the existing config/routing.py.
"""
from apps.chat.consumers import ChatConsumer

__all__ = ["ChatConsumer"]
