"""
MCP Server implementation for project workflow tools
"""
import os
import json
import asyncio
from typing import Any, Sequence, Union
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
from src.services.template_service import TemplateService
from src.services.brief_parser import BriefParser
from src.services.workflow_service import WorkflowService
from src.services.task_breakdown_service import TaskBreakdownService
from src.services.cursor_rules_service import CursorRulesService


# Initialize services
template_service = TemplateService()
brief_parser = BriefParser()
workflow_service = WorkflowService()
task_breakdown_service = TaskBreakdownService()
cursor_rules_service = CursorRulesService()

# Create MCP server
app = Server("user-project-workflow")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources"""
    return [
        Resource(
            uri="project-brief://template",
            name="Project Brief Template",
            description="Markdown template with all project questions (3 required, 14 optional)",
            mimeType="text/markdown"
        )
    ]


@app.read_resource()
async def read_resource(uri: Union[str, Any]) -> str:
    """
    Read resource content
    
    Supports:
    - project-brief://template - Returns the template
    - file:///path/to/file.md - Reads from file system
    """
    # Convert URI to string if it's an AnyUrl object
    uri_str = str(uri)
    
    if uri_str == "project-brief://template":
        return template_service.generate_template()
    
    elif uri_str.startswith("file://"):
        # Extract file path
        file_path = uri_str.replace("file://", "")
        
        # Handle absolute paths (file:///path/to/file) and regular paths (file://path/to/file)
        if file_path.startswith("/"):
            # Absolute path: file:///absolute/path
            file_path = file_path  # Keep the leading slash
        else:
            # Relative path: resolve to absolute
            file_path = os.path.abspath(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    else:
        raise ValueError(f"Unsupported resource URI: {uri_str}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="generate_project_documents",
            description="Generate functional requirements, TRD/PRD, time estimates, and cost estimates from a filled project brief markdown file",
            inputSchema={
                "type": "object",
                "properties": {
                    "brief_uri": {
                        "type": "string",
                        "description": "URI to project brief markdown file (project-brief://template or file:///path/to/brief.md)"
                    }
                },
                "required": ["brief_uri"]
            }
        ),
        Tool(
            name="generate_task_breakdown",
            description="Generate a detailed task breakdown organized into phases from a TRD/PRD document. Requires either a TRD string or a project brief URI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trd": {
                        "type": "string",
                        "description": "TRD/PRD document as string (optional if brief_uri is provided)"
                    },
                    "brief_uri": {
                        "type": "string",
                        "description": "URI to project brief markdown file (optional if trd is provided, will generate TRD from brief)"
                    }
                }
            }
        ),
        Tool(
            name="generate_cursor_rules",
            description="Generate .cursorrules file content for Cursor AI based on project tech stack and configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "brief_uri": {
                        "type": "string",
                        "description": "URI to project brief markdown file (project-brief://template or file:///path/to/brief.md)"
                    }
                },
                "required": ["brief_uri"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool calls
    
    Returns list of TextContent with results
    """
    try:
        if name == "generate_project_documents":
            brief_uri = arguments.get("brief_uri")
            if not brief_uri:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "brief_uri is required"}, indent=2)
                )]
            
            # Read brief content
            brief_content = await read_resource(brief_uri)
            
            # Parse markdown
            project_data = brief_parser.parse_brief(brief_content)
            
            # Validate required fields
            is_valid, missing_fields = brief_parser.validate_required_fields(project_data)
            if not is_valid:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Missing required fields",
                        "missing_fields": missing_fields,
                        "required_fields": brief_parser.REQUIRED_FIELDS
                    }, indent=2)
                )]
            
            # Execute workflow
            workflow_result = await workflow_service.execute_workflow(project_data)
            
            if workflow_result["success"]:
                result = {
                    "success": True,
                    "trd": workflow_result["trd"],
                    "time_estimate": workflow_result["time_estimate"],
                    "cost_estimate": workflow_result["cost_estimate"],
                    "backend_status": workflow_result.get("backend_status")
                }
            else:
                result = {
                    "success": False,
                    "error": workflow_result.get("error", "Unknown error")
                }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "generate_task_breakdown":
            trd = arguments.get("trd")
            brief_uri = arguments.get("brief_uri")
            
            # If TRD provided, use it directly
            if trd:
                project_data = {}
                num_developers = arguments.get("num_developers")
                tech_stack = arguments.get("tech_stack")
            # If brief_uri provided, parse it and generate TRD first
            elif brief_uri:
                brief_content = await read_resource(brief_uri)
                project_data = brief_parser.parse_brief(brief_content)
                
                # Validate required fields
                is_valid, missing_fields = brief_parser.validate_required_fields(project_data)
                if not is_valid:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required fields in brief",
                            "missing_fields": missing_fields
                        }, indent=2)
                    )]
                
                # Generate TRD first
                workflow_result = await workflow_service.execute_workflow(project_data)
                if not workflow_result["success"]:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Failed to generate TRD",
                            "details": workflow_result.get("error")
                        }, indent=2)
                    )]
                
                trd = workflow_result["trd"]
                num_developers = None
                tech_stack = None
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Either 'trd' or 'brief_uri' must be provided"
                    }, indent=2)
                )]
            
            # Generate task breakdown
            task_breakdown = await task_breakdown_service.generate_task_breakdown(
                prd=trd,
                num_developers=num_developers,
                tech_stack=tech_stack,
                project_data=project_data if project_data else None
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(task_breakdown, indent=2)
            )]
        
        elif name == "generate_cursor_rules":
            brief_uri = arguments.get("brief_uri")
            if not brief_uri:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "brief_uri is required"}, indent=2)
                )]
            
            # Read brief content
            brief_content = await read_resource(brief_uri)
            
            # Parse markdown
            project_data = brief_parser.parse_brief(brief_content)
            
            # Validate that we have at least some tech stack info
            if not any([
                project_data.get("frontendStack"),
                project_data.get("backendStack"),
                project_data.get("programmingLanguage")
            ]):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "At least one tech stack field (frontendStack, backendStack, or programmingLanguage) is required"
                    }, indent=2)
                )]
            
            # Generate cursor rules
            cursor_rules = await cursor_rules_service.generate_cursor_rules(project_data)
            
            return [TextContent(
                type="text",
                text=cursor_rules
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
            )]
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "traceback": error_details
            }, indent=2)
        )]


async def main():
    """Main entry point for MCP server"""
    # Use stdio_server context manager to get read/write streams
    async with stdio_server() as (read_stream, write_stream):
        # Create initialization options
        initialization_options = app.create_initialization_options()
        
        # Run the server
        await app.run(
            read_stream,
            write_stream,
            initialization_options
        )


if __name__ == "__main__":
    asyncio.run(main())

