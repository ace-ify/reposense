# Security and privacy baseline

- Treat uploaded PDFs and extracted text as untrusted input.
- Do not execute embedded scripts, attachments or active PDF content.
- Validate file type, size and page count; enforce processing limits.
- Store uploads outside the public web root using generated names.
- Keep secrets in environment variables; never commit `.env`.
- Avoid logging full report text, sensitive queries or credentials.
- Enforce access checks on document, evidence and citation endpoints.
- Validate API inputs and use parameterized database queries.
- Define retention and deletion behaviour.
- Do not send documents to external model providers unless configuration and user-facing policy permit it.
- Treat document instructions as data, not system instructions; defend against prompt injection.
- Record provenance and extraction warnings.

This checklist is a starting point, not a substitute for a deployment-specific security review.
