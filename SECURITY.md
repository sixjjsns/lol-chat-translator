# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public issue.
Instead, contact the maintainer privately.

## Security considerations

- API keys are stored locally (weak obfuscation in a user-only file), never in source, logs, or git.
- The `.gitignore` excludes `.credential`, `config.json`, `.env`, and logs.
- Logs are sanitized to avoid leaking Authorization headers, API keys, or chat text.

## Supported versions

Only the latest release is supported for security updates.
