"""
Service to parse filled project brief markdown into structured data
"""
import re
from typing import Dict, Any, Optional
from src.services.question_service import QuestionService


class BriefParser:
    """Parses project brief markdown template into structured data"""
    
    # Map markdown headers to field names
    FIELD_MAPPING = {
        "app name": "appName",
        "problem solved": "problemSolved",
        "core features": "coreFeatures",
        "number of developers": "num_developers",
        "num developers": "num_developers",
        "frontend stack": "frontendStack",
        "backend stack": "backendStack",
        "programming language": "programmingLanguage",
        "database": "database",
        "api integrations": "apiIntegrations",
        "authentication": "authentication",
        "roles and permissions": "rolesPermissions",
        "roles permissions": "rolesPermissions",
        "design style": "designStyle",
        "theme": "theme",
        "exclusions": "exclusions",
        "comparable apps": "comparableApps",
        "comparable/existing apps": "comparableApps",
        "constraints": "constraints",
    }
    
    REQUIRED_FIELDS = ["appName", "problemSolved", "coreFeatures"]
    
    def __init__(self):
        self.question_service = QuestionService()
    
    def parse_brief(self, markdown_content: str) -> Dict[str, Any]:
        """
        Parse markdown brief into structured data
        
        Args:
            markdown_content: Markdown string with filled answers
            
        Returns:
            Dictionary with project data matching QuestionService.ALL_FIELDS format
        """
        data = {}
        
        # Normalize markdown content
        content = markdown_content.strip()
        
        # Split by headers (## or ###)
        # Use regex to find all headers and their content
        pattern = r'^##+\s+(.+?)$(.*?)(?=^##+|$)'
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            header = match.group(1).strip()
            content_section = match.group(2).strip() if match.group(2) else ""
            
            # Remove asterisk from required fields
            header = header.rstrip(' *').strip()
            
            # Find matching field
            field_name = self._match_field(header)
            if field_name:
                # Extract answer from content
                answer = self._extract_answer(content_section)
                if answer and answer.lower() not in ['_(optional)_', '(optional)', 'optional', '']:
                    data[field_name] = answer
                else:
                    data[field_name] = None
        
        # Also try alternative parsing: look for "**Answer:**" patterns
        # Check if we have valid data (not just None values)
        valid_data_count = sum(1 for v in data.values() if v is not None and v != "")
        if valid_data_count < 3:
            # Try alternative format
            alt_data = self._parse_alternative_format(content)
            # Merge alternative data, preferring non-None values
            for key, value in alt_data.items():
                if value and value != "":
                    data[key] = value
        
        return data
    
    def _parse_alternative_format(self, content: str) -> Dict[str, Any]:
        """Alternative parsing method for different markdown formats"""
        data = {}
        
        # Look for patterns like "### Header" followed by "**Answer:** value"
        pattern = r'^###\s+(.+?)$.*?^\*\*Answer:\*\*\s*(.+?)(?=^###|^##|$)'
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            header = match.group(1).strip().rstrip(' *')
            answer = match.group(2).strip()
            
            field_name = self._match_field(header)
            if field_name and answer and answer.lower() not in ['_(optional)_', '(optional)', 'optional', '']:
                data[field_name] = self._clean_answer(answer)
        
        return data
    
    def _match_field(self, header: str) -> Optional[str]:
        """Match markdown header to field name"""
        header_lower = header.lower().strip()
        
        # Direct match
        if header_lower in self.FIELD_MAPPING:
            return self.FIELD_MAPPING[header_lower]
        
        # Partial match
        for key, value in self.FIELD_MAPPING.items():
            if key in header_lower or header_lower in key:
                return value
        
        # Try camelCase conversion
        field_candidate = header.lower().replace(' ', '').replace('-', '')
        if field_candidate in self.question_service.ALL_FIELDS:
            return field_candidate
        
        return None
    
    def _extract_answer(self, content: str) -> str:
        """Extract answer from markdown content section"""
        if not content:
            return ""
        
        # Remove markdown formatting
        content = re.sub(r'^\*\*(.+?)\*\*$', r'\1', content, flags=re.MULTILINE)
        content = re.sub(r'^_(.+?)_$', r'\1', content, flags=re.MULTILINE)
        content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
        content = re.sub(r'_(.+?)_', r'\1', content)
        
        # Remove "Answer:" prefix if present
        content = re.sub(r'^\*\*Answer:\*\*\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'^Answer:\s*', '', content, flags=re.MULTILINE)
        
        # Remove "Your answer here" placeholders
        content = re.sub(r'_Your answer here[^_]*_', '', content)
        content = re.sub(r'\(optional\)', '', content, flags=re.IGNORECASE)
        content = re.sub(r'optional', '', content, flags=re.IGNORECASE)
        
        # Remove code blocks if present
        content = re.sub(r'```[\s\S]*?```', '', content)
        
        # Clean up whitespace
        content = content.strip()
        
        # Remove empty lines and excessive whitespace
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        content = '\n'.join(lines)
        
        return content
    
    def _clean_answer(self, answer: str) -> str:
        """Clean answer string"""
        # Remove markdown formatting
        answer = re.sub(r'\*\*(.+?)\*\*', r'\1', answer)
        answer = re.sub(r'_(.+?)_', r'\1', answer)
        answer = re.sub(r'`(.+?)`', r'\1', answer)
        
        # Remove placeholders
        answer = re.sub(r'\(optional\)', '', answer, flags=re.IGNORECASE)
        
        return answer.strip()
    
    def validate_required_fields(self, data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate that all required fields are present
        
        Args:
            data: Parsed project data dictionary
            
        Returns:
            Tuple of (is_valid, missing_fields)
        """
        missing_fields = []
        
        for field in self.REQUIRED_FIELDS:
            value = data.get(field)
            if not value or value == "" or value is None:
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields

