# Hotel Kong Arthur Analytics Platform Constitution

**Status: Draft for group review.** This draft translates the assignment's fixed requirements into project principles. The group should review and ratify it before treating it as final.

## Core principles

### I. Specification before implementation

Follow the assignment's Spec Kit workflow: Constitution → Specify → Clarify → Plan → Tasks → Implement → Converge. Describe user-facing behavior and acceptance criteria before implementing it. Keep each user story small and valuable, and use INVEST as a quality check.

### II. Three-layer backend

The backend must have distinct presentation, business-logic, and data-access layers. The presentation layer handles REST/JSON requests and responses. The business-logic layer owns domain rules and official KPI calculations. The data-access layer reads and writes persistent data. Keep responsibilities in their intended layer and document any exception in the plan.

### III. Contract-led REST API

Expose backend capabilities through a REST API with JSON. Maintain an OpenAPI specification as the API contract and provide Swagger UI in a Docker container. Keep the documented request and response schemas, status codes, and implemented endpoints aligned. The booking frontend, Tableau, and a future hotel booking system are API clients.

### IV. MySQL as operational source of truth

Use MySQL for operational hotel and bar data. CSV files from the assignment may inform an initial historical import or sample dataset; they must not be the only way to update current data. Persist booking changes through the API and protect data integrity in the business and data-access layers.

### V. Consistent analytics on current data

The API and dashboard must support the metrics named in the assignment, including occupancy and customer satisfaction where suitable source data exists. The backend business-logic layer is the default owner of official KPI definitions and calculations; Tableau presents and filters those results. Define and document calculation rules before implementation, including season boundaries, occupancy denominator, reporting year, satisfaction source, and revenue inclusions. Do not present estimated room rates as verified transaction data.

### VI. Reproducible containerized operation

The complete prototype must start with one `docker compose up` command. Document each service, its connection to other services, database readiness, and data persistence. Keep Swagger UI available as a containerized service. Tableau's connection method and whether Tableau itself runs outside Docker must be documented as an integration decision.

### VII. Explainable group contribution

Use AI as a development aid and review its output. Group members must understand and be able to explain the delivered system. Make small, meaningful commits as work progresses. Each member must commit their own contribution using their own configured Git identity; never attribute work to another member.

## Fixed assignment scope

- Hotel Kong Arthur has 214 rooms and eight room types; the assignment estimates maximum capacity at 428 guests.
- The hotel dashboard must cover guest countries, revenue, revenue by room type and season, revenue by country, the highest-earning room types and countries, annual hotel revenue, and one additional useful KPI.
- The system must support KPIs such as occupancy and customer satisfaction when the available data supports a meaningful calculation.
- The bar dashboard must cover Helene Christine's annual sales, revenue per drink, and the percentage split of cocktails and coffee. The assignment states 20 cocktails and 10 coffee types.
- The prototype frontend must create, edit, and delete bookings through the backend.
- The API contract must be OpenAPI and accessible through Swagger UI.
- The database must be MySQL; the system must use Docker and Docker Compose.

## Clarification rules

Treat the following as unresolved until the group records decisions in the specification or plan:

- Season date ranges and whether seasons vary by year.
- Occupancy formula, room availability rules, and treatment of out-of-service rooms.
- Which reporting year and timezone define “this year.”
- Which booking fields and guest-country source are available in the provided sample data.
- Whether satisfaction data is available, how it is scored, and which records belong in its calculation.
- Room-rate source and revenue inclusions, such as taxes, cancellations, refunds, and add-ons.
- Source and granularity of cocktail and coffee sales, including prices and transaction dates.
- How Tableau connects to and refreshes the REST/JSON analytics endpoints.

When evidence is missing, record a clarification instead of inventing production data or business rules.

## Governance

The assignment's fixed technology and delivery requirements take precedence over implementation convenience. Amend this constitution only through a documented group decision. During Converge, compare implementation and documentation with the constitution, feature specifications, plans, tasks, and acceptance criteria. Record incomplete or unresolved requirements as follow-up tasks.

**Version:** 0.1.0-draft | **Ratified:** Pending group review | **Last amended:** 2026-10-26
