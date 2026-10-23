# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

---

## Reporting a Vulnerability

We take the security of **AI Startup Co-Founder Team** seriously. If you discover a vulnerability or security concern, please follow responsible disclosure practices:

1. **Do not create a public GitHub issue.**
2. Send an email describing the vulnerability, affected components, and steps to reproduce to the repository maintainers or use GitHub's private vulnerability reporting feature.
3. Include relevant proof-of-concept payloads or logs.

---

## Security Hardening in this Project

- **In-Memory Streaming**: All downloads (PDF, PPTX, Markdown, CSV) are generated strictly in ephemeral RAM buffers (`io.BytesIO`) and streamed via chunked transfer encoding. No sensitive venture documentation is persisted to disk on downloads.
- **Spreadsheet DDE Injection Defense**: Cells in CSV exports are sanitized to neutralize formula prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`).
- **XML Entity Escaping**: Dynamic inputs to ReportLab PDF generation are escaped to prevent XML injection and SSRF.
- **Strict Content Security**: Mermaid.js flowcharts render under `securityLevel: 'strict'`.
- **Path Traversal Guards**: File export handlers strictly validate canonical paths against boundary directories.
