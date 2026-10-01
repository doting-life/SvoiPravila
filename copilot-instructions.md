\# Svoi Pravila — Copilot Instructions

This repository contains the backend for the "Svoi Pravila" product.

Before making architectural or implementation changes, read these files in this order:

1\. docs/PROJECT\_CONTEXT.md  
2\. docs/ARCHITECTURE.md  
3\. README.md  
4\. IMPLEMENTATION\_STATUS.md  
5\. docs/MINIAPP\_API.md

Treat these documents as the current source of truth for architecture and product behavior.

Core architectural rule:

\- Workflow state and stage transitions are deterministic Python code.  
\- LLMs provide reasoning and generation inside stages.  
\- LLMs must not control workflow progression.  
\- Stages communicate through typed Pydantic artifacts.  
\- External systems are accessed through adapters/providers.  
\- Business logic must not depend directly on OpenAI, Telegram, Redis, or PostgreSQL SDKs.  
\- Preserve tenant isolation between users and relationships.  
\- Do not trust user\_id or relationship ownership supplied by clients.  
\- Telegram Mini App identity must come from validated Telegram initData.  
\- Do not persist raw private conversation text unless explicitly required by the architecture.  
\- Preserve retry/resume/checkpoint behavior.

Before implementing a task:

1\. Inspect the existing implementation.  
2\. Reuse existing abstractions rather than creating parallel architecture.  
3\. Identify affected artifacts, stages, repositories, adapters and tests.  
4\. Preserve backward compatibility unless the task explicitly requires a breaking change.  
5\. Add or update tests for all behavior changes.  
6\. Run the relevant test suite after implementation.  
7\. Do not silently change documented architecture. If a design change is necessary, update the corresponding Markdown/YAML specification.

Current implementation status is defined by IMPLEMENTATION\_STATUS.md.

When README, architecture documentation and implementation disagree:  
\- first inspect the actual code and tests,  
\- identify the inconsistency,  
\- do not guess,  
\- report it before performing a major architectural rewrite.  
