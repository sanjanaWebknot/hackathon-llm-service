# MCP Server Usage Guide

This guide explains how to use the Model Context Protocol (MCP) server for project workflow generation.

## Overview

The MCP server provides three main tools:
1. **generate_project_documents** - Generates TRD/PRD, time and cost estimates from a project brief
2. **generate_task_breakdown** - Creates a detailed task breakdown organized into phases
3. **generate_cursor_rules** - Generates a `.cursorrules` file for Cursor AI

## Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
ANTHROPIC_API_KEY=your_key
```

## Starting the MCP Server

### Standalone Mode (stdio)

The MCP server can run as a standalone process using stdio transport:

```bash
python mcp_server.py
```

### Integration with MCP Clients

To use with MCP-compatible clients (like Claude Desktop):

1. Add to your MCP configuration (e.g., Claude Desktop's `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "project-workflow": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server.py"]
    }
  }
}
```

## Resources

### Template Resource

The server provides a template resource that users can read:

**URI**: `project-brief://template`

This returns a markdown template with all 17 project questions (3 required, 14 optional).

## Tools

### 1. generate_project_documents

Generates functional requirements, TRD/PRD, time estimates, and cost estimates from a filled project brief.

**Input**:
```json
{
  "brief_uri": "file:///path/to/project-brief.md"
}
```

**Output**:
```json
{
  "success": true,
  "trd": "Generated TRD/PRD markdown...",
  "time_estimate": {
    "frontend": {...},
    "backend": {...},
    "total_project_hours": 120,
    "estimated_weeks": 8
  },
  "cost_estimate": {
    "frontend": {...},
    "backend": {...},
    "total_project_cost": 50000
  }
}
```

### 2. generate_task_breakdown

Generates a detailed task breakdown organized into phases from a TRD/PRD document.

**Input** (with TRD):
```json
{
  "trd": "TRD/PRD document content..."
}
```

**Input** (with brief URI):
```json
{
  "brief_uri": "file:///path/to/project-brief.md"
}
```

**Output**:
```json
{
  "phases": [
    {
      "name": "Phase 1: Setup",
      "description": "...",
      "tasks": [
        {
          "id": "task-1",
          "name": "Set up project structure",
          "description": "...",
          "dependencies": [],
          "estimated_hours": 4,
          "complexity": "medium",
          "assignee_type": "fullstack"
        }
      ],
      "estimated_hours": 20
    }
  ],
  "total_tasks": 15,
  "estimated_total_hours": 120,
  "estimated_weeks": 8
}
```

### 3. generate_cursor_rules

Generates a `.cursorrules` file content based on project tech stack.

**Input**:
```json
{
  "brief_uri": "file:///path/to/project-brief.md"
}
```

**Output**: Raw `.cursorrules` file content (markdown format)

## Workflow Example

### Step 1: Get the Template

```bash
# Read template resource
mcp read-resource project-brief://template > project-brief.md
```

### Step 2: Fill Out the Brief

Edit `project-brief.md` and fill in all required fields and any optional fields relevant to your project.

**Required fields**:
- App Name
- Problem Solved
- Core Features

**Optional fields**: See template for full list

### Step 3: Generate Project Documents

```bash
# Call tool with filled brief
mcp call-tool generate_project_documents '{"brief_uri": "file:///absolute/path/to/project-brief.md"}'
```

This will:
1. Parse the brief
2. Generate functional requirements
3. Generate TRD/PRD
4. Generate time and cost estimates

### Step 4: Generate Task Breakdown

```bash
# Option 1: Using the TRD from step 3
mcp call-tool generate_task_breakdown '{"trd": "...TRD content here..."}'

# Option 2: Using the brief (will generate TRD first)
mcp call-tool generate_task_breakdown '{"brief_uri": "file:///path/to/project-brief.md"}'
```

### Step 5: Generate Cursor Rules

```bash
mcp call-tool generate_cursor_rules '{"brief_uri": "file:///path/to/project-brief.md"}'
```

Save the output to `.cursorrules` in your project root.

## File URI Format

When referencing files, use absolute paths:

- ✅ Correct: `file:///Users/username/project-brief.md`
- ✅ Also works: `file:///Users/username/project-brief.md` (leading slash optional)
- ❌ Wrong: `file://project-brief.md` (relative paths not supported)

## Error Handling

If required fields are missing, tools will return an error:

```json
{
  "error": "Missing required fields",
  "missing_fields": ["appName"],
  "required_fields": ["appName", "problemSolved", "coreFeatures"]
}
```

## Tips

1. **Save outputs**: Always save TRD and task breakdown outputs for reference
2. **Iterate**: You can update the brief and re-run tools as needed
3. **Required vs Optional**: Only 3 fields are required, but more details yield better results
4. **Tech Stack**: Providing frontend/backend stack info is important for accurate estimates

## Troubleshooting

### MCP server not starting

- Check Python version (3.8+ required)
- Verify all dependencies are installed
- Check environment variables are set

### File not found errors

- Use absolute paths for file URIs
- Verify file exists and is readable
- Check file permissions

### Missing field errors

- Ensure all 3 required fields are filled
- Check field names match template exactly
- Verify markdown formatting is correct

## Integration with Existing WebSocket Flow

The MCP server complements the existing WebSocket interactive flow:

- **MCP**: Use when you have a filled brief document
- **WebSocket**: Use for interactive guided question flow

Both use the same underlying services and produce the same outputs.

