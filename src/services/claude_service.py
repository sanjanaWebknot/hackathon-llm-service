"""
Anthropic Claude service for PRD generation
"""
import os
import re
from anthropic import Anthropic
from dotenv import load_dotenv
from src.utils.prompts import TIME_ESTIMATION_PROMPT
from src.utils.prompts import COST_ESTIMATION_PROMPT
# from src.utils.prompts import PRD_GENERATION_PROMPT
import json

load_dotenv()


def clean_and_parse_json(content: str) -> dict:
    """
    Clean and parse JSON content that may have formatting issues
    
    Args:
        content: Raw JSON string that may be malformed
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        Exception: If JSON cannot be parsed after cleaning attempts
    """
    original_content = content
    
    # Remove markdown code blocks if present
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    
    if content.endswith("```"):
        content = content[:-3]
    
    content = content.strip()
    
    # Try to find JSON object in the content (in case there's extra text)
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        content = json_match.group(0)
    
    # Try direct parsing first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Fix common issues
    # 1. Remove trailing commas before closing braces/brackets
    content = re.sub(r',(\s*[}\]])', r'\1', content)
    
    # 2. Try parsing again
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # 3. Fix single quotes - replace single quotes with double quotes
    # This handles the common case where LLMs use single quotes instead of double
    # We'll be careful to only replace quotes that are clearly JSON syntax
    # Pattern: single quotes around keys and string values
    # Match: 'key': or : 'value' or 'key': 'value'
    def fix_single_quotes(text):
        # Replace 'key': with "key":
        text = re.sub(r"'([^']+)':", r'"\1":', text)
        # Replace : 'value' with : "value" (but not if already double-quoted)
        text = re.sub(r":\s*'([^']*)'([,}\]]|\s*$)", r': "\1"\2', text)
        # Replace standalone 'value' (for array values)
        text = re.sub(r"'\s*([^']*)\s*'([,}\]]|\s*$)", r'"\1"\2', text)
        return text
    
    # Try with single quote fix
    try:
        content_fixed = fix_single_quotes(content)
        return json.loads(content_fixed)
    except (json.JSONDecodeError, Exception):
        pass
    
    # 4. Last resort: simple single quote replacement (may break apostrophes in strings)
    # Only do this if the content clearly has single quotes as delimiters
    if "'" in content and '"' not in content:
        content_simple = content.replace("'", '"')
        try:
            return json.loads(content_simple)
        except json.JSONDecodeError:
            pass
    
    # 5. Extract just the JSON structure (first { to last })
    first_brace = content.find('{')
    last_brace = content.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            extracted = content[first_brace:last_brace + 1]
            extracted = re.sub(r',(\s*[}\]])', r'\1', extracted)
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass
    
    # If all else fails, raise an error with the problematic content
    error_preview = original_content[:1000] if len(original_content) > 1000 else original_content
    # Also try to show where the error might be
    try:
        # Try one more time to get the exact error location
        json.loads(content)
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON: {str(e)}. Content around error (char {e.pos}): {content[max(0, e.pos-50):e.pos+50]}"
        raise Exception(error_msg)
    
    raise Exception(f"Failed to parse JSON after cleaning attempts. Content preview: {error_preview}...")

class ClaudeService:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
        self.client = Anthropic(api_key=api_key)
        # Use a more standard Claude model name
        # Try claude-3-5-sonnet-20241022 or claude-3-opus-20240229
        self.model = "claude-3-haiku-20240307"  # Claude 3.5 Sonnet (more stable)
        print(f"Initialized Claude service with model: {self.model}")
    
    def generate_prd(self, functional_requirements: str) -> str:
        """
        Generate PRD from functional requirements
        
        Args:
            functional_requirements: Functional requirements markdown string
            
        Returns:
            PRD as markdown string
        """
        from src.utils.prompts import PRD_GENERATION_PROMPT
        
        prompt = PRD_GENERATION_PROMPT.format(
            functional_requirements=functional_requirements
        )
        
        try:
            # Claude Haiku has max 4096 tokens, Sonnet/Opus can handle more
            # Use 4096 to be safe for all models
            max_output_tokens = 4096 if "haiku" in self.model.lower() else 8000
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_output_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract PRD from response (handle <PRD> tags if present)
            content = message.content[0].text.strip()
            
            # Remove <PRD> tags if present
            if content.startswith("<PRD>") and content.endswith("</PRD>"):
                content = content[5:-6].strip()
            elif content.startswith("<PRD>"):
                content = content[5:].strip()
            elif content.endswith("</PRD>"):
                content = content[:-6].strip()
            
            return content
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
    
    def generate_time_estimates(self, prd: str, num_developers: int, tech_stack: list) -> dict:
        """
        Generate time estimates from PRD
        
        Args:
            prd: PRD markdown string
            num_developers: Number of developers
            tech_stack: List of technologies
            
        Returns:
            Time estimates as JSON dict
        """
        
        
        prompt = TIME_ESTIMATION_PROMPT.format(
            prd=prd,
            num_developers=num_developers,
            tech_stack=", ".join(tech_stack) if isinstance(tech_stack, list) else tech_stack
        )
        
        try:
            # Max tokens for estimates (4000 is safe for all models including Haiku)
            max_output_tokens = 4000
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_output_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = message.content[0].text.strip()
            
            # Use robust JSON parser
            return clean_and_parse_json(content)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse time estimates JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
    
    def generate_cost_estimates(self, prd: str, num_developers: int, tech_stack: list) -> dict:
        """
        Generate cost estimates from PRD
        
        Args:
            prd: PRD markdown string
            num_developers: Number of developers
            tech_stack: List of technologies
            
        Returns:
            Cost estimates as JSON dict
        """
        
        
        prompt = COST_ESTIMATION_PROMPT.format(
            prd=prd,
            num_developers=num_developers,
            tech_stack=", ".join(tech_stack) if isinstance(tech_stack, list) else tech_stack
        )
        
        try:
            # Max tokens for estimates (4000 is safe for all models including Haiku)
            max_output_tokens = 4000
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_output_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = message.content[0].text.strip()
            
            # Use robust JSON parser
            return clean_and_parse_json(content)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse cost estimates JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")

