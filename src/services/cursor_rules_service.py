"""
Service to generate .cursorrules file from project data
"""
import asyncio
from typing import Dict, Any, Optional
from src.services.claude_service import ClaudeService
from src.utils.prompts import CURSOR_RULES_PROMPT


class CursorRulesService:
    """Generates .cursorrules file content from project information"""
    
    def __init__(self):
        self.claude_service = ClaudeService()
    
    async def generate_cursor_rules(
        self,
        project_data: Dict[str, Any],
        task_breakdown: Optional[Dict[str, Any]] = None,
        trd: Optional[str] = None
    ) -> str:
        """
        Generate .cursorrules file content from project data
        
        Args:
            project_data: Project data dictionary with tech stack info
            task_breakdown: Optional task breakdown dictionary for context
            trd: Optional TRD/PRD document for context
            
        Returns:
            String content of .cursorrules file in markdown format
        """
        # Extract relevant fields
        app_name = project_data.get("appName", "Project")
        frontend_stack = project_data.get("frontendStack", "Not specified")
        backend_stack = project_data.get("backendStack", "Not specified")
        programming_language = project_data.get("programmingLanguage", "Not specified")
        database = project_data.get("database", "Not specified")
        design_style = project_data.get("designStyle", "Not specified")
        
        # Build additional context
        additional_context_parts = []
        
        if project_data.get("problemSolved"):
            additional_context_parts.append(f"Problem: {project_data.get('problemSolved')}")
        
        if project_data.get("coreFeatures"):
            additional_context_parts.append(f"Core Features: {project_data.get('coreFeatures')}")
        
        if project_data.get("apiIntegrations"):
            additional_context_parts.append(f"API Integrations: {project_data.get('apiIntegrations')}")
        
        if project_data.get("authentication"):
            additional_context_parts.append(f"Authentication: {project_data.get('authentication')}")
        
        if project_data.get("rolesPermissions"):
            additional_context_parts.append(f"Roles & Permissions: {project_data.get('rolesPermissions')}")
        
        if project_data.get("theme"):
            additional_context_parts.append(f"Theme: {project_data.get('theme')}")
        
        if project_data.get("constraints"):
            additional_context_parts.append(f"Constraints: {project_data.get('constraints')}")
        
        # Add task breakdown context if provided
        if task_breakdown:
            total_tasks = task_breakdown.get("total_tasks", 0)
            total_hours = task_breakdown.get("estimated_total_hours", 0)
            phases_count = len(task_breakdown.get("phases", []))
            additional_context_parts.append(f"\nTask Breakdown Summary: {total_tasks} tasks across {phases_count} phases, estimated {total_hours} hours")
        
        # Add TRD context if provided (truncated for brevity)
        if trd:
            trd_summary = trd[:500] + "..." if len(trd) > 500 else trd
            additional_context_parts.append(f"\nTRD Summary: {trd_summary}")
        
        additional_context = "\n".join(additional_context_parts) if additional_context_parts else "None specified"
        
        # Format prompt
        prompt = CURSOR_RULES_PROMPT.format(
            app_name=app_name,
            frontend_stack=frontend_stack,
            backend_stack=backend_stack,
            programming_language=programming_language,
            database=database,
            design_style=design_style,
            additional_context=additional_context
        )
        
        try:
            # Generate cursor rules using Claude
            max_output_tokens = 4096
            
            message = await asyncio.to_thread(
                self.claude_service.client.messages.create,
                model=self.claude_service.model,
                max_tokens=max_output_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = message.content[0].text.strip()
            
            # Remove any markdown code blocks if Claude wraps it
            if content.startswith("```"):
                # Find the end of code block
                lines = content.split('\n')
                if lines[0].startswith("```"):
                    # Remove first line (``` or ```markdown)
                    lines = lines[1:]
                # Remove last line if it's ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = '\n'.join(lines).strip()
            
            return content
            
        except Exception as e:
            raise Exception(f"Claude API error generating cursor rules: {str(e)}")
    
    def generate_from_brief(
        self,
        project_data: Dict[str, Any]
    ) -> str:
        """
        Generate .cursorrules from project brief data (sync wrapper)
        
        Args:
            project_data: Project data dictionary
            
        Returns:
            String content of .cursorrules file
        """
        # Validate required fields are present (at least some tech stack info)
        if not any([
            project_data.get("frontendStack"),
            project_data.get("backendStack"),
            project_data.get("programmingLanguage")
        ]):
            raise ValueError("At least one tech stack field (frontendStack, backendStack, or programmingLanguage) is required")
        
        return asyncio.run(self.generate_cursor_rules(project_data))

