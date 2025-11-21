# AI Workflow Generator

A FastAPI-based service that generates functional requirements, PRD (Product Requirements Document), time estimates, and cost estimates from application descriptions.

## Features

- **Functional Requirements Generation**: Uses Azure OpenAI to create concise functional requirements
- **PRD Generation**: Uses Claude 3.7 Sonnet to generate comprehensive Product Requirements Documents
- **Time Estimation**: Generates detailed time breakdowns for frontend, backend, and AI tasks
- **Cost Estimation**: Generates cost estimates with hourly rates and infrastructure costs
- **Parallel Processing**: Time and cost estimates are generated in parallel for efficiency
- **Task Breakdown**: Generates structured task breakdowns organized into phases
- **Cursor Rules Generation**: Creates `.cursorrules` files for Cursor AI based on project tech stack
- **MCP Server**: Model Context Protocol server for integration with AI assistants
- **WebSocket Support**: Interactive guided question flow for data collection

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```

3. Add your API keys to `.env`:
```
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Running the Server

### FastAPI Server (WebSocket + REST API)

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### MCP Server (Model Context Protocol)

```bash
python mcp_server.py
```

The MCP server runs via stdio and can be integrated with MCP-compatible clients like Claude Desktop.

See [MCP_USAGE.md](MCP_USAGE.md) for detailed usage instructions.

## API Endpoints

### POST `/api/generate`

Main workflow endpoint that generates all outputs in sequence.

**Request Body:**
```json
{
  "description": "Application description string",
  "num_developers": 3,
  "tech_stack": ["React", "Node.js", "PostgreSQL", "OpenAI API"]
}
```

**Response:**
```json
{
  "functional_requirements": "Markdown string...",
  "prd": "Markdown string...",
  "time_estimates": {
    "frontend": {...},
    "backend": {...},
    "ai_tasks": {...},
    "total_project_hours": 400,
    "estimated_weeks": 8
  },
  "cost_estimates": {
    "frontend": {...},
    "backend": {...},
    "ai_tasks": {...},
    "infrastructure": {...},
    "total_project_cost": 50000,
    "estimated_weeks": 8
  }
}
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
.
├── main.py                      # FastAPI app entry point
├── mcp_server.py                # MCP server entry point
├── requirements.txt             # Python dependencies
├── .env.example                # Environment variables template
├── MCP_USAGE.md                # MCP server usage guide
├── PROJECT_BRIEF_TEMPLATE.md   # Example filled project brief
├── src/
│   ├── api/
│   │   ├── routes.py           # API route handlers
│   │   ├── models.py           # Pydantic models
│   │   └── websocket_routes.py # WebSocket endpoints
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── server.py           # MCP server implementation
│   ├── services/
│   │   ├── openai_service.py          # Azure OpenAI integration
│   │   ├── claude_service.py          # Anthropic Claude integration
│   │   ├── workflow_service.py        # Main workflow orchestration
│   │   ├── question_service.py        # Question generation
│   │   ├── session_manager.py         # WebSocket session management
│   │   ├── response_validator.py      # Response validation
│   │   ├── template_service.py        # Project brief template generation
│   │   ├── brief_parser.py            # Markdown brief parser
│   │   ├── task_breakdown_service.py  # Task breakdown generation
│   │   └── cursor_rules_service.py    # Cursor rules generation
│   └── utils/
│       └── prompts.py          # Prompt templates
└── README.md
```

## Workflow

### Via WebSocket (Interactive Flow)

1. Client connects to `/ws/collect` endpoint
2. Server asks questions interactively based on context
3. Client responds with answers
4. System validates responses and asks follow-ups if needed
5. Once all required fields are collected, workflow executes automatically
6. Results (TRD, time estimates, cost estimates) are returned

### Via MCP Server (Brief-Based Flow)

1. User reads project brief template: `project-brief://template`
2. User fills out the markdown template with project information
3. User calls MCP tools:
   - `generate_project_documents` - Generates TRD, time and cost estimates
   - `generate_task_breakdown` - Creates detailed task breakdown
   - `generate_cursor_rules` - Generates `.cursorrules` file

### Via REST API

1. Frontend sends description, number of developers, and tech stack
2. System generates functional requirements (Azure OpenAI)
3. System generates PRD from functional requirements (Claude)
4. System generates time and cost estimates in parallel (Claude)
5. All results are returned in a single response

## Usage Examples

### MCP Server

See [MCP_USAGE.md](MCP_USAGE.md) for detailed MCP server usage.

### WebSocket Flow

See `test_websocket_flow.py` for example WebSocket client implementation.

### Project Brief Template

See [PROJECT_BRIEF_TEMPLATE.md](PROJECT_BRIEF_TEMPLATE.md) for an example filled project brief.

