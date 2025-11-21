"""
Service to execute the complete workflow: functional requirements -> TRD -> time/cost estimates
"""
import os
import json
import asyncio
import httpx
from typing import Dict, Any, Optional
from src.services.openai_service import AzureOpenAIService
from src.services.claude_service import ClaudeService


class WorkflowService:
    """Executes the complete workflow and sends results to backend"""
    
    def __init__(self):
        self.azure_openai_service = AzureOpenAIService()
        self.claude_service = ClaudeService()
        backend_base_url = os.getenv("BACKEND_ENDPOINT_URL", "")
        # Append /api/v1/projects endpoint to base URL
        self.backend_endpoint = f"{backend_base_url.rstrip('/')}/api/v1/projects" if backend_base_url else ""
    
    async def execute_workflow(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete workflow:
        1. Generate functional requirements
        2. Generate TRD (PRD)
        3. Generate time and cost estimates in parallel
        4. Send to backend endpoint
        
        Args:
            collected_data: Dictionary of collected data from WebSocket
            
        Returns:
            Dictionary with workflow results and status
        """
        try:
            # Step 1: Generate functional requirements (sequential - must complete before step 2)
            print("🔄 Step 1: Generating functional requirements...")
            functional_requirements = await asyncio.to_thread(
                self.azure_openai_service.generate_functional_requirements,
                app_name=collected_data.get("appName"),
                problem_solved=collected_data.get("problemSolved"),
                core_features=collected_data.get("coreFeatures"),
                frontend_stack=collected_data.get("frontendStack"),
                backend_stack=collected_data.get("backendStack"),
                programming_language=collected_data.get("programmingLanguage"),
                database=collected_data.get("database"),
                api_integrations=collected_data.get("apiIntegrations"),
                authentication=collected_data.get("authentication"),
                roles_permissions=collected_data.get("rolesPermissions"),
                design_style=collected_data.get("designStyle"),
                theme=collected_data.get("theme"),
                exclusions=collected_data.get("exclusions"),
                comparable_apps=collected_data.get("comparableApps"),
                constraints=collected_data.get("constraints")
            )
            print(f"✅ Functional requirements generated ({len(functional_requirements)} chars)")
            
            # Step 2: Generate TRD (PRD) from functional requirements (sequential - after step 1 completes)
            print("🔄 Step 2: Generating TRD/PRD...")
            trd = await asyncio.to_thread(
                self.claude_service.generate_prd,
                functional_requirements
            )
            print(f"✅ TRD/PRD generated ({len(trd)} chars)")
            
            # Combine tech stack for estimates
            tech_stack_list = []
            if collected_data.get("frontendStack"):
                tech_stack_list.append(collected_data.get("frontendStack"))
            if collected_data.get("backendStack"):
                tech_stack_list.append(collected_data.get("backendStack"))
            if collected_data.get("programmingLanguage"):
                tech_stack_list.append(collected_data.get("programmingLanguage"))
            if collected_data.get("database"):
                tech_stack_list.append(collected_data.get("database"))
            tech_stack_str = ", ".join(tech_stack_list) if tech_stack_list else "Not specified"
            
            num_developers = collected_data.get("num_developers")
            if num_developers:
                try:
                    num_developers = int(num_developers)
                except (ValueError, TypeError):
                    num_developers = None
            
            # Step 3 & 4: Generate time and cost estimates in parallel (only these two run together)
            print("🔄 Step 3 & 4: Generating time and cost estimates in parallel...")
            time_estimates, cost_estimates = await asyncio.gather(
                asyncio.to_thread(
                    self.claude_service.generate_time_estimates,
                    trd,
                    num_developers,
                    tech_stack_str
                ),
                asyncio.to_thread(
                    self.claude_service.generate_cost_estimates,
                    trd,
                    num_developers,
                    tech_stack_str
                )
            )
            
            # Step 5: Send to backend endpoint
            print("🔄 Step 5: Sending to backend endpoint...")
            backend_status = await self._send_to_backend(trd, time_estimates, cost_estimates)
            if backend_status.get("sent"):
                print(f"✅ Successfully sent to backend (Status: {backend_status.get('status_code')})")
            else:
                print(f"⚠️  Backend send failed: {backend_status.get('message')}")
            
            return {
                "success": True,
                "trd": trd,
                "time_estimate": time_estimates,
                "cost_estimate": cost_estimates,
                "backend_status": backend_status
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "trd": None,
                "time_estimate": None,
                "cost_estimate": None,
                "backend_status": None
            }
    
    async def _send_to_backend(self, trd: str, time_estimate: Dict[str, Any], cost_estimate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send TRD, time estimate, and cost estimate to backend endpoint
        
        Args:
            trd: TRD/PRD string
            time_estimate: Time estimates dictionary
            cost_estimate: Cost estimates dictionary
            
        Returns:
            Dictionary with backend response status
        """
        if not self.backend_endpoint:
            return {
                "sent": False,
                "message": "Backend endpoint URL not configured (BACKEND_ENDPOINT_URL)"
            }
        
        try:
            payload = {
                "trd": trd,
                "estimated_time": time_estimate,
                "estimated_cost": cost_estimate
            }
            
            print(f"   📤 Sending to: {self.backend_endpoint}")
            print(f"   📦 Payload size: trd={len(trd)} chars, estimated_time={len(json.dumps(time_estimate))} bytes, estimated_cost={len(json.dumps(cost_estimate))} bytes")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.backend_endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                return {
                    "sent": True,
                    "status_code": response.status_code,
                    "message": "Successfully sent to backend"
                }
                
        except httpx.TimeoutException:
            return {
                "sent": False,
                "message": "Backend request timed out"
            }
        except httpx.HTTPStatusError as e:
            return {
                "sent": False,
                "status_code": e.response.status_code,
                "message": f"Backend returned error: {e.response.text}"
            }
        except Exception as e:
            return {
                "sent": False,
                "message": f"Error sending to backend: {str(e)}"
            }

