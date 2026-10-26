# Hotel Kong Arthur project guidance

Use GitHub Spec Kit's spec-driven workflow for project changes: constitution → specify → clarify → plan → tasks → implement → converge. Read the current project artifacts before changing implementation.

For architecture or acceptance-criteria reviews, also read and follow `project-skills/hotel-architecture-review/SKILL.md`.

## Assignment requirements

- Keep the backend in three clear layers: REST/API presentation, business logic, and data access.
- Use REST with JSON, an OpenAPI contract, and Swagger UI available in Docker.
- Use MySQL. The complete system must start with one `docker compose up` command.
- Provide a browser interface for creating, editing, and deleting bookings through the backend.
- Support current data updates through the API; sample CSV data must not be the only source of truth.
- Provide hotel analytics for guest countries, revenue by room type and season, revenue by country, top revenue room types and countries, annual hotel revenue, and one additional useful KPI.
- Provide bar analytics for Helene Christine: annual total sales, revenue per drink, and cocktail-versus-coffee share.
- Maintain `README.md` with a system architecture diagram, `CONTRIBUTE.md`, and the OpenAPI contract.
- Give each user story acceptance criteria and check implementation against them during converge.

## Review and contribution

For reviews, trace a representative browser request through the API, business logic, data-access layer, and MySQL. Check that the API contract matches the implementation and that the dashboard can get its data from the API. Report findings with file paths and concrete evidence.

Make small, meaningful commits for work actually completed. Use the configured Git author identity. Each group member must make commits for their own contribution; do not attribute work to another person.
