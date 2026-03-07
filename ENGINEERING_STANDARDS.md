# Engineering Standards (Repository-Wide)

This document defines the unified engineering and coding standards for this repository.
All contributors and automated code generators must follow these rules.

## 0. Guiding Principles

- **Consistency > Personal preference.**
- **No behavior changes unless required** to fix correctness bugs.
- Prefer **small, reviewable diffs**.
- Separate concerns:
  - **Python**: ingestion, analysis, async jobs.
  - **Java**: REST API + domain services.
  - **Frontend**: UI + API client.

## 1. Repository Structure Conventions

- Java service code lives under: `services/java-core/`
- Python services/workers live under: `services/` (or existing python service directories)
- Frontend lives under: `frontend/`

### Frontend design sources of truth
- `frontend/design/design-spec.md`
- `frontend/design/tokens.json`
- `frontend/design/ui/` (reference screenshots)

If there is any conflict:
1) UI screenshots (`frontend/design/ui/`) take priority for layout/visual structure
2) `design-spec.md` defines component rules/behavior
3) `tokens.json` defines values (colors/spacing/typography tokens)

## 2. Global Formatting & Tooling

- Prefer automated formatting over manual formatting.
- Add/maintain configuration files so local dev + CI can run consistent checks.

Where applicable:
- Avoid `print()` in services; use structured logging.
- Avoid duplicating business rules across layers (centralize mapping logic).

## 3. Java Standards (services/java-core)

### 3.1 Style & Conventions
- Follow **Google Java Style Guide**.
- Follow Spring Boot best practices:
  - Constructor injection
  - Clear layering: controller/service/repository/dto/entity
  - No business logic in controllers
- Do not expose JPA entities directly in API responses; use DTOs.

### 3.2 API conventions
- REST endpoints under `/api/*`
- Use UTC timestamps and ISO-8601 serialization.
- Use consistent error responses (if a global handler exists).

### 3.3 Logging
- Use SLF4J (`org.slf4j.Logger`).
- No `System.out.println`.

## 4. Python Standards (services/* python code)

### 4.1 Style & Conventions
- Follow **PEP 8** and **Google Python Style Guide**.
- Use `snake_case` for functions/variables and `PascalCase` for classes.
- Prefer type hints for public functions and key internal interfaces.

### 4.2 Logging
- Use Python `logging` module.
- No `print()` in production code paths.

### 4.3 Data modeling
- Prefer typed models (`dataclasses` or pydantic) for structured data.
- Avoid passing unstructured dicts across multiple layers without a defined schema.

## 5. Frontend Standards (frontend)

### 5.1 Language & structure
- TypeScript + React functional components (no class components).
- Keep components small and focused.
- Centralize cross-cutting logic in utilities (e.g., sentiment mapping).

### 5.2 Style tools
- Use ESLint + Prettier (or existing repo tooling).
- No inline styles (use Tailwind classes).
- No raw hex colors; use token-mapped Tailwind classes only.

### 5.3 Design system enforcement
- Do not invent new spacing/color values outside tokens.
- Tailwind theme must map tokens.json.
- Typography must follow design spec.

## 6. “Do Not” Rules

- Do not change database schemas unless explicitly required by a tracked issue.
- Do not rewrite working modules just to “make it nicer”.
- Do not introduce new frameworks without explicit approval.
- Do not alter UI layout beyond what is required to match `frontend/design/ui/`.

## 7. Definition of Done (Style Compliance)

A change set is considered style-compliant when:
- Java code is formatted and consistent with Google Java Style.
- Python code conforms to PEP8/Google style expectations and uses logging/type hints where required.
- Frontend code passes lint/format checks and respects design tokens/spec.
- No new warnings/errors are introduced in build/test steps.