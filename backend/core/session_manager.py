import json
import os
import time
import uuid
from typing import List, Dict

class SessionManager:
    def __init__(self, storage_file: str = "conversations.json"):
        self.storage_file = storage_file
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, "w") as f:
                json.dump([], f)

    def _load_conversations(self) -> List[Dict]:
        try:
            with open(self.storage_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_conversations(self, conversations: List[Dict]):
        with open(self.storage_file, "w") as f:
            json.dump(conversations, f, indent=2)

    def create_conversation(self, user_id: str, title: str = "New Chat") -> Dict:
        """Creates a new conversation metadata entry."""
        conv_id = str(uuid.uuid4())
        new_conv = {
            "id": conv_id,
            "user_id": user_id,
            "title": title,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        conversations = self._load_conversations()
        conversations.insert(0, new_conv) # Append to start
        self._save_conversations(conversations)
        return new_conv

    def get_user_conversations(self, user_id: str) -> List[Dict]:
        """Returns all conversations for a user, sorted by updated_at desc."""
        conversations = self._load_conversations()
        user_convs = [c for c in conversations if c.get("user_id") == user_id]
        return sorted(user_convs, key=lambda x: x.get("updated_at", 0), reverse=True)

    def update_conversation_title(self, conversation_id: str, title: str):
        conversations = self._load_conversations()
        for conv in conversations:
            if conv["id"] == conversation_id:
                conv["title"] = title
                conv["updated_at"] = time.time()
                break
        self._save_conversations(conversations)
    
    def update_timestamp(self, conversation_id: str):
         conversations = self._load_conversations()
         for conv in conversations:
             if conv["id"] == conversation_id:
                 conv["updated_at"] = time.time()
                 break
         self._save_conversations(conversations)

    def get_conversation(self, conversation_id: str) -> Dict:
        conversations = self._load_conversations()
        for conv in conversations:
            if conv["id"] == conversation_id:
                return conv
        return None

    def delete_conversation(self, conversation_id: str):
        """Deletes a conversation from metadata storage."""
        conversations = self._load_conversations()
        updated_convs = [c for c in conversations if c["id"] != conversation_id]
        if len(conversations) != len(updated_convs):
            self._save_conversations(updated_convs)
            return True
        return False
