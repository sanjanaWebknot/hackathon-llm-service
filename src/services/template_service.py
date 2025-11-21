"""
Service to generate markdown template for project brief
"""
from src.services.question_service import QuestionService


class TemplateService:
    """Generates markdown template with all project questions"""
    
    REQUIRED_FIELDS = ["appName", "problemSolved", "coreFeatures"]
    
    def __init__(self):
        self.question_service = QuestionService()
    
    def generate_template(self) -> str:
        """
        Generate markdown template with all questions
        
        Returns:
            Markdown template string with all fields and questions
        """
        lines = [
            "# Project Brief",
            "",
            "Please fill out this template with information about your project.",
            "Fields marked with * are **required**.",
            "",
            "## Required Information",
            ""
        ]
        
        # Add required fields first
        for field in self.REQUIRED_FIELDS:
            desc = self.question_service.FIELD_DESCRIPTIONS.get(field, field)
            lines.append(f"### {self._format_field_name(field)} *")
            lines.append(f"**{desc}**")
            lines.append("")
            lines.append("**Answer:** ")
            lines.append("")
        
        lines.append("## Optional Information")
        lines.append("")
        
        # Add optional fields
        for field in self.question_service.ALL_FIELDS:
            if field not in self.REQUIRED_FIELDS:
                desc = self.question_service.FIELD_DESCRIPTIONS.get(field, field)
                lines.append(f"### {self._format_field_name(field)}")
                lines.append(f"**{desc}**")
                lines.append("")
                lines.append("**Answer:** _(optional)_")
                lines.append("")
        
        return "\n".join(lines)
    
    def _format_field_name(self, field: str) -> str:
        """Format field name for display (e.g., appName -> App Name)"""
        # Convert camelCase to Title Case
        import re
        # Split on capital letters and join with spaces
        formatted = re.sub(r'(?<!^)(?=[A-Z])', ' ', field)
        # Capitalize first letter of each word
        return ' '.join(word.capitalize() for word in formatted.split())
    
    def get_template_content(self) -> str:
        """Alias for generate_template for consistency"""
        return self.generate_template()

