# Burpy 🛡️

A powerful, CLI-based web security testing tool inspired by Burp Suite and Caido. Designed for security professionals, developers, and penetration testers who need a lightweight, terminal-focused alternative for web application security testing.

![Python Version](https://img.shields.io/badge/Python-3.7+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## ⚡ Features

### Core Security Testing
- **HTTP/HTTPS Proxy** - Intercept and modify web traffic with CONNECT tunneling for HTTPS
- **Vulnerability Scanner** - Automated detection of SQLi, XSS, directory traversal, sensitive files
- **Request Repeater** - Manual testing with custom headers, methods, and body data
- **Intruder/Fuzzer** - Parameter fuzzing, directory brute-forcing, rate limiting support
- **GraphQL Security Scanner** - Introspection detection, batch queries, DoS testing

### Automation & Integration
- **Macro Automation** - Record and replay request sequences with variable extraction
- **CI/CD Export** - Generate reports in JSON, SARIF, CSV, HTML, Markdown, JUnit formats
- **Session Management** - Cookie handling, token management, authentication state

### CLI Experience
- **Professional Output** - Color-coded, well-structured results for technical and non-technical users
- **Multiple Export Formats** - Export scan results for GitHub, GitLab, Jenkins integration
- **Request History** - Track, search, and export all HTTP requests

## 🚀 Quick Start

```bash
# Installation
pip install -r requirements.txt
pip install -e .

# Or run directly
python -m burpy
```

## 📖 Commands

| Command | Description | Example |
|---------|-------------|---------|
| `proxy` | Start HTTP/HTTPS intercepting proxy | `burpy proxy --port 8080` |
| `scan` | Scan for web vulnerabilities | `burpy scan https://example.com -v` |
| `repeat` | Send custom HTTP requests | `burpy repeat https://api.example.com -m POST` |
| `fuzz` | Fuzz parameters with wordlist | `burpy fuzz https://site.com id -w list.txt` |
| `attack` | Automated attack with rate limiting | `burpy attack https://site.com -t 20` |
| `graphql` | Test GraphQL security | `burpy graphql https://api.example.com/graphql` |
| `history` | View request history | `burpy history --limit 50` |
| `export` | Export results (CI/CD formats) | `burpy export https://site.com -f sarif -o report.sarif` |
| `info` | Show help and options | `burpy info` |

## 🔧 Options

```bash
-q, --quiet      # Suppress banner
-v, --verbose    # Detailed output
-o, --output     # Output file
-H, --header     # Custom HTTP header
-d, --data       # Request body data
-w, --wordlist   # Wordlist file
-t, --threads    # Number of threads
-f, --format     # Output format (json/csv/html/sarif/markdown/junit)
```

## 💡 Examples

```bash
# Quick vulnerability scan
burpy scan https://example.com --verbose

# Custom request with authentication
burpy repeat https://api.site.com/users -m GET -H "Authorization: Bearer token"

# Parameter fuzzing
burpy fuzz https://site.com/search q -w wordlist.txt -t 20

# Export for CI/CD pipeline
burpy export https://site.com -f sarif -o results.sarif

# Start intercepting proxy
burpy proxy --host 127.0.0.1 --port 8080 --verbose

# GraphQL security testing
burpy graphql https://api.example.com/graphql
```

## 🛡️ Security Checks

### Vulnerability Scanner
- SQL Injection detection
- Cross-Site Scripting (XSS)
- Directory traversal
- Sensitive file discovery
- HTTP method enumeration
- Security header analysis

### GraphQL Testing
- Introspection enabled detection
- Batch query vulnerabilities
- DoS via aggregate queries
- Dangerous mutations

## 📦 Dependencies

- `requests` - HTTP library
- `click` - CLI framework
- `colorama` - Colored terminal output
- `cryptography` - SSL/TLS support

## ⚠️ Disclaimer

This tool is for **authorized security testing only**. Only use on systems you own or have explicit permission to test. The authors are not responsible for any misuse.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.