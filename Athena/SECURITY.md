# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 8.x     | :white_check_mark: |
| 7.x     | :white_check_mark: |
| < 7.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Project Athena, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainer directly or use GitHub's private vulnerability reporting feature
3. Include a clear description of the vulnerability and steps to reproduce

## What to Expect

- Acknowledgment within 48 hours
- Status update within 7 days
- If accepted, a fix will be prioritized based on severity

## Scope

This security policy applies to:

- The Athena framework code and templates
- Documentation that could lead to security issues if followed incorrectly

This project does not handle sensitive user data directly, but we take all security concerns seriously.

## ⚠️ Supabase Key Security

> [!CAUTION]
> **Never use the `SUPABASE_SERVICE_ROLE_KEY` in client-side code or `.env` files that may be committed.**

The `athena` SDK only requires the **`SUPABASE_ANON_KEY`** for normal operation. The Service Role Key grants root-level database access and should only be used in server-side admin scripts with proper Row-Level Security (RLS) disabled.

| Key Type | Use Case | Risk Level |
|----------|----------|------------|
| `SUPABASE_ANON_KEY` | Client-side SDK, search, embeddings | ✅ Safe |
| `SUPABASE_SERVICE_ROLE_KEY` | Admin scripts, migrations | ⚠️ High (never commit) |
