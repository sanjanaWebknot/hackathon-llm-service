"""
Azure OpenAI service for generating functional requirements
"""
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class AzureOpenAIService:
    def __init__(self):
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        # Default to gpt-4o-mini if not specified
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        
        if not api_key:
            raise ValueError(
                "AZURE_OPENAI_API_KEY environment variable is not set. "
                "Please add it to your .env file."
            )
        
        if not azure_endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT environment variable is not set. "
                "Please add it to your .env file. "
                "Format: https://your-resource.openai.azure.com/"
            )
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=azure_endpoint
        )
        
        # Use the deployment name as the model name
        self.model = deployment_name
        print(f"Initialized Azure OpenAI service with model: {self.model} (GPT-4o Mini)")
    
    def generate_functional_requirements(
        self,
        app_name: str = None,
        problem_solved: str = None,
        core_features: str = None,
        frontend_stack: str = None,
        backend_stack: str = None,
        programming_language: str = None,
        database: str = None,
        api_integrations: str = None,
        authentication: str = None,
        roles_permissions: str = None,
        design_style: str = None,
        theme: str = None,
        exclusions: str = None,
        comparable_apps: str = None,
        constraints: str = None
    ) -> str:
        """
        Generate concise functional requirements from application details
        
        Args:
            app_name: Name of the application
            problem_solved: Problem the app solves
            core_features: Core features (string)
            frontend_stack: Frontend technology stack
            backend_stack: Backend technology stack
            programming_language: Primary programming language
            database: Database choice
            api_integrations: API integrations (string)
            authentication: Authentication method
            roles_permissions: Roles and permissions
            design_style: Design style preference
            theme: Theme preferences
            exclusions: Things not to build (string)
            comparable_apps: Comparable existing apps
            constraints: Project constraints
            
        Returns:
            Functional requirements as markdown string
        """
        from src.utils.prompts import FUNCTIONAL_REQUIREMENTS_PROMPT
        
        prompt = FUNCTIONAL_REQUIREMENTS_PROMPT.format(
            app_name=app_name or "Not specified",
            problem_solved=problem_solved or "Not specified",
            core_features=core_features or "Not specified",
            frontend_stack=frontend_stack or "Not specified",
            backend_stack=backend_stack or "Not specified",
            programming_language=programming_language or "Not specified",
            database=database or "Not specified",
            api_integrations=api_integrations or "None",
            authentication=authentication or "Not specified",
            roles_permissions=roles_permissions or "Not specified",
            design_style=design_style or "Not specified",
            theme=theme or "Not specified",
            exclusions=exclusions or "None",
            comparable_apps=comparable_apps or "None",
            constraints=constraints or "None"
        )
        
        # Add system instruction to the prompt
        full_prompt = "You are an expert technical writer specializing in creating clear and concise functional requirements.\n\n" + prompt
        
        import time
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert technical writer specializing in creating clear and concise functional requirements."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                return response.choices[0].message.content.strip()
            except Exception as e:
                error_str = str(e)
                # Check if it's a quota/rate limit error
                if "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        print(f"Rate limit hit. Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        raise Exception(f"Azure OpenAI rate limit exceeded after {max_retries} attempts: {str(e)}")
                else:
                    raise Exception(f"Azure OpenAI error: {str(e)}")
        
        raise Exception("Failed to generate content after retries")

