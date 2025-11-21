"""
Service to generate task breakdown from PRD/TRD
"""
import json
import asyncio
from typing import Dict, Any, Optional
from src.services.claude_service import ClaudeService, clean_and_parse_json
from src.utils.prompts import TASK_BREAKDOWN_PROMPT


class TaskBreakdownService:
    """Generates structured task breakdown from PRD/TRD document"""
    
    def __init__(self):
        self.claude_service = ClaudeService()
    
    async def generate_task_breakdown(
        self,
        prd: str,
        num_developers: Optional[int] = None,
        tech_stack: Optional[str] = None,
        project_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate task breakdown from PRD/TRD
        
        Args:
            prd: PRD/TRD document as string
            num_developers: Number of developers (optional)
            tech_stack: Tech stack description (optional)
            project_data: Full project data dict (optional, for context)
            
        Returns:
            Dictionary with task breakdown structure
        """
        # Build tech stack string from project_data if available
        if not tech_stack and project_data:
            tech_stack_list = []
            if project_data.get("frontendStack"):
                tech_stack_list.append(project_data.get("frontendStack"))
            if project_data.get("backendStack"):
                tech_stack_list.append(project_data.get("backendStack"))
            if project_data.get("programmingLanguage"):
                tech_stack_list.append(project_data.get("programmingLanguage"))
            if project_data.get("database"):
                tech_stack_list.append(project_data.get("database"))
            tech_stack = ", ".join(tech_stack_list) if tech_stack_list else "Not specified"
        
        if not tech_stack:
            tech_stack = "Not specified"
        
        if not num_developers and project_data:
            num_developers = project_data.get("num_developers")
            if num_developers:
                try:
                    num_developers = int(num_developers)
                except (ValueError, TypeError):
                    num_developers = None
        
        # Format prompt
        prompt = TASK_BREAKDOWN_PROMPT.format(
            prd=prd,
            num_developers=num_developers or "Not specified",
            tech_stack=tech_stack
        )
        
        try:
            # Generate task breakdown using Claude
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
            
            # Use robust JSON parser
            task_breakdown = clean_and_parse_json(content)
            
            # Validate structure
            if "phases" not in task_breakdown:
                raise ValueError("Task breakdown missing 'phases' field")
            
            return task_breakdown
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse task breakdown JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Claude API error generating task breakdown: {str(e)}")
    
    def generate_from_project_data(
        self,
        project_data: Dict[str, Any],
        trd: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate task breakdown from project data (requires TRD)
        
        Args:
            project_data: Project data dictionary
            trd: TRD/PRD document (optional, will generate if not provided)
            
        Returns:
            Dictionary with task breakdown structure
        """
        # If TRD not provided, need to generate it first
        if not trd:
            # This would require running the workflow service first
            # For now, raise an error suggesting to provide TRD
            raise ValueError("TRD/PRD document is required. Please provide trd parameter or generate it first using WorkflowService.")
        
        # Extract tech stack info
        tech_stack_list = []
        if project_data.get("frontendStack"):
            tech_stack_list.append(project_data.get("frontendStack"))
        if project_data.get("backendStack"):
            tech_stack_list.append(project_data.get("backendStack"))
        if project_data.get("programmingLanguage"):
            tech_stack_list.append(project_data.get("programmingLanguage"))
        if project_data.get("database"):
            tech_stack_list.append(project_data.get("database"))
        tech_stack = ", ".join(tech_stack_list) if tech_stack_list else "Not specified"
        
        num_developers = project_data.get("num_developers")
        if num_developers:
            try:
                num_developers = int(num_developers)
            except (ValueError, TypeError):
                num_developers = None
        
        # Generate breakdown
        # Note: This is a sync wrapper, but underlying method is async
        import asyncio
        return asyncio.run(
            self.generate_task_breakdown(
                prd=trd,
                num_developers=num_developers,
                tech_stack=tech_stack,
                project_data=project_data
            )
        )

