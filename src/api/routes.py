"""
FastAPI routes for workflow generation
"""
from fastapi import APIRouter, HTTPException
from concurrent.futures import ThreadPoolExecutor
from src.api.models import GenerateRequest, GenerateResponse
from src.services.openai_service import AzureOpenAIService
from src.services.claude_service import ClaudeService

router = APIRouter()
azure_openai_service = AzureOpenAIService()
claude_service = ClaudeService()


@router.post("/generate", response_model=GenerateResponse)
async def generate_workflow(request: GenerateRequest):
    """
    Main workflow endpoint that:
    1. Generates functional requirements from description
    2. Generates PRD from functional requirements
    3. Generates time and cost estimates in parallel from PRD
    """
    try:
        # Step 1: Generate functional requirements
        functional_requirements = azure_openai_service.generate_functional_requirements(
            app_name=request.appName,
            problem_solved=request.problemSolved,
            core_features=request.coreFeatures,
            frontend_stack=request.frontendStack,
            backend_stack=request.backendStack,
            programming_language=request.programmingLanguage,
            database=request.database,
            api_integrations=request.apiIntegrations,
            authentication=request.authentication,
            roles_permissions=request.rolesPermissions,
            design_style=request.designStyle,
            theme=request.theme,
            exclusions=request.exclusions,
            comparable_apps=request.comparableApps,
            constraints=request.constraints
        )
        
        # Step 2: Generate PRD from functional requirements
        prd = claude_service.generate_prd(functional_requirements)
        
        # Combine frontend and backend stacks for estimates
        tech_stack_list = []
        if request.frontendStack:
            tech_stack_list.append(request.frontendStack)
        if request.backendStack:
            tech_stack_list.append(request.backendStack)
        if request.programmingLanguage:
            tech_stack_list.append(request.programmingLanguage)
        if request.database:
            tech_stack_list.append(request.database)
        tech_stack_str = ", ".join(tech_stack_list) if tech_stack_list else "Not specified"
        
        # Step 3 & 4: Generate time and cost estimates in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            time_future = executor.submit(
                claude_service.generate_time_estimates,
                prd,
                request.num_developers,
                tech_stack_str
            )
            cost_future = executor.submit(
                claude_service.generate_cost_estimates,
                prd,
                request.num_developers,
                tech_stack_str
            )
            
            # Wait for both to complete
            time_estimates = time_future.result()
            cost_estimates = cost_future.result()
        
        return GenerateResponse(
            functional_requirements=functional_requirements,
            prd=prd,
            time_estimates=time_estimates,
            cost_estimates=cost_estimates
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow generation failed: {str(e)}")

