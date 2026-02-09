import json
import os
import uuid
from typing import Any, Optional, List
from google.adk.sessions.base_session_service import BaseSessionService, ListSessionsResponse, GetSessionConfig
from google.adk.sessions.session import Session

class PersistentSessionService(BaseSessionService):
    def __init__(self, storage_path="sessions.json"):
        self.storage_path = storage_path
        self._sessions = {}
        self._load_sessions()

    def _load_sessions(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for key, s_dict in data.items():
                        try:
                            self._sessions[key] = Session.model_validate(s_dict)
                        except Exception as e:
                            print(f"Warning: Failed to load session {key}: {e}")
            except Exception as e:
                print(f"Error loading sessions: {e}")

    def _save_sessions(self):
        try:
            data = {k: v.model_dump(mode='json') for k, v in self._sessions.items()}
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        sid = session_id or str(uuid.uuid4())
        session = Session(
            id=sid,
            app_name=app_name,
            user_id=user_id,
            state=state or {}
        )
        key = f"{user_id}:{sid}"
        self._sessions[key] = session
        self._save_sessions()
        return session

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        key = f"{user_id}:{session_id}"
        return self._sessions.get(key)

    async def list_sessions(
        self, 
        *, 
        app_name: str, 
        user_id: Optional[str] = None
    ) -> ListSessionsResponse:
        results = []
        for session in self._sessions.values():
            if user_id:
                if session.user_id == user_id:
                    results.append(session)
            else:
                results.append(session)
        return ListSessionsResponse(sessions=results)

    async def delete_session(
        self, 
        *, 
        app_name: str, 
        user_id: str, 
        session_id: str
    ) -> None:
        key = f"{user_id}:{session_id}"
        if key in self._sessions:
            del self._sessions[key]
            self._save_sessions()

    # Backwards compatibility / Helper methods
    async def clear_session(self, user_id: str, session_id: str, **kwargs):
        await self.delete_session(app_name="rite_unified", user_id=user_id, session_id=session_id)

    async def save_session(self, user_id: str, session_id: str, history: list, **kwargs):
        """Historical save_session method for internal use if needed."""
        # For now, we assume the Runner handles event appending via append_event (which is implemented in Base class)
        # But if we need to manually update:
        key = f"{user_id}:{session_id}"
        if key in self._sessions:
            # We don't have a direct 'history' field in Session, it has 'events'
            # This method might be deprecated in the new flow, but we keep it for now
            pass

