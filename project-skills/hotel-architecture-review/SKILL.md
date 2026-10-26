---
name: "hotel-architecture-review"
description: "Review Hotel Kong Arthur project changes against the assignment, architecture, API, analytics, Docker, documentation, and contribution requirements."
compatibility: "Use in the Hotel Kong Arthur project workspace."
metadata:
  author: "project-team"
---

# Hotel Kong Arthur architecture review

Use this skill when reviewing a feature, a pull request, the project structure, or the final Converge status.

## Source of truth

- Read the assignment PDF and SWA follow-up questions in the project root when their details are relevant.
- Read the current Spec Kit constitution, feature specification, plan, and tasks before evaluating implementation.
- Treat confirmed decisions in those artifacts as the current project contract. Call out conflicts between assignment requirements and project artifacts.

## Review requirements

- Keep the backend in three clear layers: presentation/API, business logic, and data access.
- Expose REST endpoints using JSON and maintain an OpenAPI contract with Swagger UI available in Docker.
- Use MySQL and make the complete prototype start with one `docker compose up` command.
- Provide a browser interface that creates, edits, and deletes bookings through the backend API.
- Support current data updates through the API; CSV samples must not be the only source of truth.
- Cover guest countries, hotel revenue by room type and season, revenue by country, highest-revenue room types and countries, annual hotel revenue, and one additional KPI.
- Support occupancy and customer-satisfaction KPIs when suitable source data and definitions are available.
- Cover Helene Christine's annual bar sales, revenue per drink, and cocktail-versus-coffee share.
- Maintain `README.md` with an architecture diagram, `CONTRIBUTE.md`, and the API contract.
- Keep user stories small and valuable, and verify their acceptance criteria during Converge.

## Review procedure

1. Identify the changed behavior and the user story or task it supports.
2. Trace a representative request through the browser, API/presentation layer, business logic, data access, and MySQL where applicable.
3. Check that each responsibility belongs in the intended layer and that OpenAPI matches the endpoint behavior.
4. Check where KPI calculations live and whether Tableau can obtain the required current data from the API.
5. Compare the change with its acceptance criteria and the relevant Docker, README, and contribution requirements.
6. Record findings with file paths and concrete evidence. Mark each requirement implemented, incomplete, or unresolved; add follow-up tasks for gaps.
7. Explain architecture tradeoffs in plain language so the group can present and defend them.

## Git contribution guidance

- Each group member must make commits for their own contribution.
