"""
Service to validate user responses using LLM
"""
from src.services.openai_service import AzureOpenAIService
from typing import Optional, Tuple

class ResponseValidator:
    """Validates user responses to questions"""
    
    def __init__(self):
        self.llm = AzureOpenAIService()
    
    async def is_response_satisfactory(self, question: str, response: str, field: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a response is satisfactory
        
        Returns:
            (is_satisfactory, follow_up_question_if_needed)
        """
        validation_prompt = f"""You are validating a user's response to a question.

Question: {question}
User's Response: {response}
Field: {field}

Determine if the response is satisfactory. A satisfactory response should:
1. Be relevant to the question
2. Provide meaningful information (not just "yes", "no", "maybe", "I don't know", etc.)
3. Be specific enough to be useful
4. Not be empty or too vague

Respond in JSON format:
{{
    "satisfactory": true/false,
    "follow_up": "optional follow-up question if not satisfactory, or null if satisfactory"
}}

Only respond with valid JSON, no additional text."""

        try:
            # Use the LLM to validate
            result = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that validates user responses. Always respond with valid JSON only."},
                    {"role": "user", "content": validation_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            import json
            response_text = result.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            validation = json.loads(response_text)
            
            is_satisfactory = validation.get("satisfactory", False)
            follow_up = validation.get("follow_up")
            
            return is_satisfactory, follow_up
            
        except Exception as e:
            # If validation fails, assume response is satisfactory to avoid blocking
            print(f"Validation error: {str(e)}")
            return True, None

