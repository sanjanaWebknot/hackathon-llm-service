"""
Service to generate questions dynamically using OpenAI
"""
from src.services.openai_service import AzureOpenAIService
from typing import Optional, Dict, Any


class QuestionService:
    """Generates questions for data collection using OpenAI and manages question flow"""
    
    ALL_FIELDS = [
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
    
    # Field descriptions for context
    FIELD_DESCRIPTIONS = {
        "appName": "the name of the application",
        "problemSolved": "what problem the application solves",
        "coreFeatures": "the core features and functionalities",
        "num_developers": "the number of developers working on the project",
        "frontendStack": "frontend technologies and frameworks",
        "backendStack": "backend technologies and frameworks",
        "programmingLanguage": "the primary programming language",
        "database": "the database system to be used",
        "apiIntegrations": "external APIs and services to integrate",
        "authentication": "user authentication methods",
        "rolesPermissions": "user roles and permission system",
        "designStyle": "the design style and aesthetic",
        "theme": "theme preferences (dark mode, light mode, etc.)",
        "exclusions": "features that should NOT be included",
        "comparableApps": "similar existing applications for reference",
        "constraints": "constraints and requirements (budget, timeline, compliance, etc.)",
    }
    
    def __init__(self):
        self.llm = AzureOpenAIService()
    
    def get_next_field_to_ask(self, collected_data: Dict[str, Any], skipped_fields: set = None) -> Optional[str]:
        """
        Determine which field to ask about next based on what's already been collected
        
        Args:
            collected_data: Dictionary of already collected data
            skipped_fields: Set of fields that have been permanently skipped (never ask these again)
            
        Returns:
            Field name to ask about next, or None if all non-skipped fields are collected
        """
        skipped_fields = skipped_fields or set()
        
        # Find empty fields (excluding skipped ones)
        empty_fields = [
            field for field in self.ALL_FIELDS 
            if field not in skipped_fields and (not collected_data.get(field) or collected_data.get(field) == "")
        ]
        
        if not empty_fields:
            return None  # All non-skipped fields collected
        
        # Use OpenAI to determine the best next question based on context
        return self._determine_best_next_field(empty_fields, collected_data)
    
    def _determine_best_next_field(self, empty_fields: list, collected_data: Dict[str, Any]) -> str:
        """
        Use OpenAI to intelligently determine which field to ask about next
        
        Args:
            empty_fields: List of fields that haven't been collected yet
            collected_data: Already collected data for context
            
        Returns:
            The best field to ask about next
        """
        # Build context of what's been collected
        collected_info = []
        for field, value in collected_data.items():
            if value:
                field_desc = self.FIELD_DESCRIPTIONS.get(field, field)
                collected_info.append(f"- {field_desc}: {value}")
        
        context_str = "\n".join(collected_info) if collected_info else "No information collected yet."
        
        # Build list of remaining fields with descriptions
        remaining_fields = []
        for field in empty_fields:
            desc = self.FIELD_DESCRIPTIONS.get(field, field)
            remaining_fields.append(f"{field}: {desc}")
        
        remaining_str = "\n".join(remaining_fields)
        
        prompt = f"""You are helping collect information about a software project. 

Information already collected:
{context_str}

Remaining fields to collect:
{remaining_str}

Based on what's already been collected, determine which field should be asked about NEXT. Consider:
1. Logical flow - what makes sense to ask next?
2. Dependencies - some fields depend on others
3. Priority - core information first, then details
4. Natural conversation flow

Respond with ONLY the field name (e.g., "appName" or "frontendStack"), nothing else."""

        try:
            result = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that determines the best order to ask questions. Always respond with just the field name."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=50
            )
            
            suggested_field = result.choices[0].message.content.strip().strip('"').strip("'")
            
            # Validate the suggested field is in our list
            if suggested_field in empty_fields:
                return suggested_field
            
            # Fallback to first empty field if suggestion is invalid
            return empty_fields[0]
            
        except Exception as e:
            print(f"Error determining next field: {str(e)}")
            # Fallback: return first empty field
            return empty_fields[0] if empty_fields else None
    
    def is_complete(self, collected_data: Dict[str, Any], skipped_fields: set = None) -> bool:
        """
        Check if all fields have been collected or skipped (only first 3 are required)
        
        Args:
            collected_data: Dictionary of collected data
            skipped_fields: Set of fields that have been permanently skipped
            
        Returns:
            True if all fields are either collected or skipped, False otherwise
        """
        skipped_fields = skipped_fields or set()
        
        # First 3 fields are required - must be filled (cannot be skipped)
        required_fields = ["appName", "problemSolved", "coreFeatures"]
        
        for field in required_fields:
            value = collected_data.get(field)
            if not value or value == "":
                return False  # Required fields must be filled
        
        # Check if all non-required fields are either filled or skipped
        for field in self.ALL_FIELDS:
            if field in required_fields:
                continue  # Already checked above
            value = collected_data.get(field)
            if (not value or value == "") and field not in skipped_fields:
                return False  # This field is not filled and not skipped
        
        return True  # All fields are either filled or skipped
    
    async def generate_question(self, field: str, context: dict = None) -> str:
        """
        Generate a question for a specific field
        
        Args:
            field: The field name to generate a question for
            context: Optional context about what's already been collected
            
        Returns:
            A question string
        """
        # Base question templates as fallback (short and precise)
        base_questions = {
            "appName": "What is your app name?",
            "problemSolved": "What problem does it solve?",
            "coreFeatures": "What are the core features?",
            "num_developers": "How many developers?",
            "frontendStack": "What frontend stack?",
            "backendStack": "What backend stack?",
            "programmingLanguage": "What programming language?",
            "database": "What database?",
            "apiIntegrations": "What API integrations?",
            "authentication": "How will users authenticate?",
            "rolesPermissions": "What roles and permissions?",
            "designStyle": "What design style?",
            "theme": "What theme preferences?",
            "exclusions": "What should NOT be included?",
            "comparableApps": "Any similar existing apps?",
            "constraints": "Any constraints or requirements?",
        }
        
        # Build context string
        context_str = ""
        if context:
            filled_fields = {k: v for k, v in context.items() if v is not None}
            if filled_fields:
                context_str = f"\n\nContext - Information already collected:\n"
                for key, value in filled_fields.items():
                    context_str += f"- {key}: {value}\n"
        
        prompt = f"""Generate a short, clear, and precise question to ask a user about their software project.

Field to ask about: {field}
{context_str}

The question should:
1. Be short and direct (one sentence, max 15 words)
2. Be clear about what information is needed
3. NO examples or additional explanations
4. Be precise and to the point

Generate ONLY the question text, no additional explanation or formatting."""

        try:
            result = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates clear, friendly questions for collecting project information. Always respond with just the question text, no additional formatting."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            question = result.choices[0].message.content.strip()
            
            # Remove quotes if present
            if question.startswith('"') and question.endswith('"'):
                question = question[1:-1]
            elif question.startswith("'") and question.endswith("'"):
                question = question[1:-1]
            
            return question
            
        except Exception as e:
            # Fallback to base question if LLM fails
            print(f"Error generating question for {field}: {str(e)}")
            return base_questions.get(field, f"Please provide information about {field}.")
    
    async def generate_follow_up_question(self, original_question: str, user_response: str, field: str) -> str:
        """
        Generate a follow-up question when the initial response is unsatisfactory
        
        Args:
            original_question: The original question that was asked
            user_response: The user's response that was deemed unsatisfactory
            field: The field name
            
        Returns:
            A follow-up question string
        """
        prompt = f"""The user was asked: "{original_question}"

They responded: "{user_response}"

This response was not satisfactory - it was too vague or incomplete.

Generate a short, direct follow-up question that:
1. Asks for more specific details
2. Is concise (one sentence, max 15 words)
3. NO examples or explanations
4. Be precise and to the point

Generate ONLY the follow-up question text, no additional explanation."""

        try:
            result = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates friendly follow-up questions. Always respond with just the question text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            follow_up = result.choices[0].message.content.strip()
            
            # Remove quotes if present
            if follow_up.startswith('"') and follow_up.endswith('"'):
                follow_up = follow_up[1:-1]
            elif follow_up.startswith("'") and follow_up.endswith("'"):
                follow_up = follow_up[1:-1]
            
            return follow_up
            
        except Exception as e:
            # Fallback follow-up
            print(f"Error generating follow-up for {field}: {str(e)}")
            return f"Please provide more details about {field}."

