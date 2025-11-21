"""
Anthropic Claude service for PRD generation
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv
from src.utils.prompts import TIME_ESTIMATION_PROMPT
from src.utils.prompts import COST_ESTIMATION_PROMPT
from src.utils.prompts import PRD_GENERATION_PROMPT
import json

load_dotenv()

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
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            
            # Parse JSON
            return json.loads(content)
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
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            
            # Parse JSON
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse cost estimates JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")

