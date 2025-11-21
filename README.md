# AI Workflow Generator

A FastAPI-based service that generates functional requirements, PRD (Product Requirements Document), time estimates, and cost estimates from application descriptions.

## Features

- **Functional Requirements Generation**: Uses Azure OpenAI to create concise functional requirements
- **PRD Generation**: Uses Claude 3.7 Sonnet to generate comprehensive Product Requirements Documents
- **Time Estimation**: Generates detailed time breakdowns for frontend, backend, and AI tasks
- **Cost Estimation**: Generates cost estimates with hourly rates and infrastructure costs
- **Parallel Processing**: Time and cost estimates are generated in parallel for efficiency

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

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

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
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── src/
│   ├── api/
│   │   ├── routes.py      # API route handlers
│   │   └── models.py      # Pydantic models
│   ├── services/
│   │   ├── openai_service.py    # Azure OpenAI integration
│   │   └── claude_service.py    # Anthropic Claude integration
│   └── utils/
│       └── prompts.py     # Prompt templates
└── README.md
```

## Workflow

1. Frontend sends description, number of developers, and tech stack
2. System generates functional requirements (Azure OpenAI)
3. System generates PRD from functional requirements (Claude)
4. System generates time and cost estimates in parallel (Claude)
5. All results are returned in a single response

