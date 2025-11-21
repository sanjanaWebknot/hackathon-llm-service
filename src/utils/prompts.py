"""
Prompt templates for AI workflow generation
"""

FUNCTIONAL_REQUIREMENTS_PROMPT = """I would like to create concise functional requirements for the following application:

**App Name:** {app_name}

**Problem Solved:** {problem_solved}

**Core Features:**
{core_features}

**Frontend Stack:** {frontend_stack}

**Backend Stack:** {backend_stack}

**Programming Language:** {programming_language}

**Database:** {database}

**API Integrations:** {api_integrations}

**Authentication:** {authentication}

**Roles & Permissions:** {roles_permissions}

**Design Style:** {design_style}

**Theme:** {theme}

**Exclusions (Things NOT to Build):** {exclusions}

**Comparable/Existing Apps:** {comparable_apps}

**Constraints:** {constraints}

Please research the comparable apps if provided and consider their features and functionality when creating the requirements.

Output as markdown code.

Go through these in detail and ensure there's nothing in there that you don't want.

Keep it as precise as possible."""

PRD_GENERATION_PROMPT = """You are an expert technical product manager specializing in feature development and creating comprehensive product requirements documents (PRDs). Your task is to generate a detailed and well-structured PRD based on the following functional requirements:

<functional_requirements>
{functional_requirements}
</functional_requirements>

Follow these steps to create the PRD:

1. Begin with a brief overview explaining the project and the purpose of the document.

2. Use sentence case for all headings except for the title of the document, which should be in title case.

3. Organize your PRD into the following sections:

   a. Introduction

   b. Product Overview

   c. Goals and Objectives

   d. Target Audience

   e. Features and Requirements

   f. User Stories and Acceptance Criteria

   g. Technical Requirements / Stack

   h. Design and User Interface

4. For each section, provide detailed and relevant information based on the functional requirements. Ensure that you:

   - Use clear and concise language

   - Provide specific details and metrics where required

   - Maintain consistency throughout the document

   - Address all points mentioned in each section

5. When creating user stories and acceptance criteria:

   - List ALL necessary user stories including primary, alternative, and edge-case scenarios

   - Assign a unique requirement ID (e.g., ST-101) to each user story for direct traceability

   - Include at least one user story specifically for secure access or authentication if the application requires user identification

   - Include at least one user story specifically for Database modelling if the application requires a database

   - Ensure no potential user interaction is omitted

   - Make sure each user story is testable

6. Format your PRD professionally:

   - Use consistent styles

   - Include numbered sections and subsections

   - Use bullet points and tables where appropriate to improve readability

   - Ensure proper spacing and alignment throughout the document

7. Review your PRD to ensure all aspects of the project are covered comprehensively and that there are no contradictions or ambiguities.

Present your final PRD within <PRD> tags. Begin with the title of the document in title case, followed by each section with its corresponding content. Use appropriate subheadings within each section as needed.

Remember to tailor the content to the specific project described in the functional requirements, providing detailed and relevant information for each section based on the given context."""

TIME_ESTIMATION_PROMPT = """You are an expert project manager and technical lead. Based on the following Product Requirements Document (PRD), generate a detailed time estimation breakdown.

<PRD>
{prd}
</PRD>

<project_metadata>
Number of Developers: {num_developers}
Tech Stack: {tech_stack}
</project_metadata>

Generate a JSON response with the following structure:
{{
  "frontend": {{
    "tasks": [
      {{
        "task_name": "string",
        "description": "string",
        "estimated_hours": number,
        "complexity": "low|medium|high"
      }}
    ],
    "total_hours": number
  }},
  "backend": {{
    "tasks": [
      {{
        "task_name": "string",
        "description": "string",
        "estimated_hours": number,
        "complexity": "low|medium|high"
      }}
    ],
    "total_hours": number
  }},
  "ai_tasks": {{
    "tasks": [
      {{
        "task_name": "string",
        "description": "string",
        "estimated_hours": number,
        "complexity": "low|medium|high"
      }}
    ],
    "total_hours": number
  }},
  "total_project_hours": number,
  "estimated_weeks": number
}}

Break down tasks by technology stack components. Be realistic and consider:
- Setup and configuration time
- Development time per feature
- Testing and debugging
- Code review and refactoring
- Documentation

Return ONLY valid JSON, no markdown formatting or additional text."""

COST_ESTIMATION_PROMPT = """You are an expert project manager and technical lead. Based on the following Product Requirements Document (PRD), generate a detailed cost estimation breakdown.

<PRD>
{prd}
</PRD>

<project_metadata>
Number of Developers: {num_developers}
Tech Stack: {tech_stack}
</project_metadata>

Generate a JSON response with the following structure:
{{
  "frontend": {{
    "tasks": [
      {{
        "task_name": "string",
        "description": "string",
        "estimated_hours": number,
        "hourly_rate": number,
        "total_cost": number,
        "complexity": "low|medium|high"
      }}
    ],
    "total_hours": number,
    "total_cost": number
  }},
  "backend": {{
    "tasks": [
      {{
        "task_name": "string",
        "description": "string",
        "estimated_hours": number,
        "hourly_rate": number,
        "total_cost": number,
        "complexity": "low|medium|high"
      }}
    ],
    "total_hours": number,
    "total_cost": number
  }},
  "ai_tasks": {{
    "tasks": [
      {{
        "task_name": "string",
        "description": "string",
        "estimated_hours": number,
        "hourly_rate": number,
        "total_cost": number,
        "complexity": "low|medium|high"
      }}
    ],
    "total_hours": number,
    "total_cost": number
  }},
  "infrastructure": {{
    "items": [
      {{
        "item_name": "string",
        "description": "string",
        "monthly_cost": number,
        "estimated_months": number,
        "total_cost": number
      }}
    ],
    "total_cost": number
  }},
  "total_project_cost": number,
  "estimated_weeks": number
}}

Consider:
- Developer hourly rates (vary by role: frontend, backend, AI/ML)
- Infrastructure costs (hosting, databases, APIs, etc.)
- Third-party service costs
- Buffer for unexpected costs (add 15-20% contingency)

Use reasonable hourly rates based on typical market rates for the tech stack.

Return ONLY valid JSON, no markdown formatting or additional text."""

