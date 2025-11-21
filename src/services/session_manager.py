"""
Session manager for WebSocket conversations
"""
from typing import Dict, Optional, Any
from datetime import datetime
import uuid


class SessionState:
    """Represents the state of a WebSocket session"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.data: Dict[str, Optional[str]] = {
            "appName": None,
            "problemSolved": None,
            "coreFeatures": None,
            "frontendStack": None,
            "backendStack": None,
            "programmingLanguage": None,
            "database": None,
            "apiIntegrations": None,
            "authentication": None,
            "rolesPermissions": None,
            "designStyle": None,
            "theme": None,
            "exclusions": None,
            "comparableApps": None,
            "constraints": None,
            "num_developers": None,
        }
        self.current_question: Optional[str] = None
        self.follow_up_count: Dict[str, int] = {}  # Track follow-ups per field
        self.skipped_fields: set = set()  # Track permanently skipped fields
        self.completed = False


class SessionManager:
    """Manages WebSocket sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionState] = {}
    
    def create_session(self) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = SessionState(session_id)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def update_field(self, session_id: str, field: str, value: str):
        """Update a field in the session"""
        if session_id in self.sessions:
            self.sessions[session_id].data[field] = value
    
    def increment_follow_up(self, session_id: str, field: str):
        """Increment follow-up count for a field"""
        if session_id in self.sessions:
            if field not in self.sessions[session_id].follow_up_count:
                self.sessions[session_id].follow_up_count[field] = 0
            self.sessions[session_id].follow_up_count[field] += 1
    
    def get_follow_up_count(self, session_id: str, field: str) -> int:
        """Get follow-up count for a field"""
        if session_id in self.sessions:
            return self.sessions[session_id].follow_up_count.get(field, 0)
        return 0
    
    def mark_field_skipped(self, session_id: str, field: str):
        """Permanently mark a field as skipped"""
        if session_id in self.sessions:
            self.sessions[session_id].skipped_fields.add(field)
            # Set a placeholder value so it's not considered empty
            self.sessions[session_id].data[field] = ""
    
    def is_field_skipped(self, session_id: str, field: str) -> bool:
        """Check if a field has been permanently skipped"""
        if session_id in self.sessions:
            return field in self.sessions[session_id].skipped_fields
        return False
    
    def get_next_empty_field(self, session_id: str) -> Optional[str]:
        """Get the next empty field that needs to be filled"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Priority order for questions - ALL fields must be answered
        priority_fields = [
            "appName",
            "problemSolved",
            "coreFeatures",
            "num_developers",
            "frontendStack",
            "backendStack",
            "programmingLanguage",
            "database",
            "apiIntegrations",
            "authentication",
            "rolesPermissions",
            "designStyle",
            "theme",
            "exclusions",
            "comparableApps",
            "constraints",
        ]
        
        for field in priority_fields:
            if session.data[field] is None:
                # Only skip if we've done one follow-up AND still couldn't get a response
                # But we'll still try to ask again if it's the only remaining field
                follow_up_count = self.get_follow_up_count(session_id, field)
                if follow_up_count >= 1:
                    # Check if there are other empty fields first
                    other_empty = [f for f in priority_fields if f != field and session.data[f] is None]
                    if other_empty:
                        continue  # Skip this one, try others first
                    # This is the last empty field, try one more time
                    if follow_up_count >= 2:
                        continue  # Already tried twice, skip
                return field
        
        return None
    
    def is_complete(self, session_id: str) -> bool:
        """Check if all required fields are filled (only first 3 are required)"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Only first 3 fields are required
        required_fields = [
            "appName",
            "problemSolved",
            "coreFeatures",
        ]
        
        for field in required_fields:
            value = session.data.get(field)
            if not value or value == "":
                return False
        
        return True
    
    def get_data(self, session_id: str) -> Dict[str, Any]:
        """Get all session data as a dict"""
        if session_id not in self.sessions:
            return {}
        
        session = self.sessions[session_id]
        return session.data.copy()
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]


# Global session manager instance
session_manager = SessionManager()

