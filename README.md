# Burpy

A lightweight CLI-based web security testing tool similar to Burp Suite, designed to run on any average PC without requiring cloud services, Docker, or complex deployment.

## Features

- **HTTP Proxy**: Intercept and modify HTTP/HTTPS traffic
- **Vulnerability Scanner**: Automated scanning for common web vulnerabilities
- **Request Repeater**: Manual testing and request modification
- **Intruder**: Automated fuzzing and brute force attacks
- **History Logger**: Track and search request/response history
- **Cross-platform**: Works on Windows, macOS, and Linux

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/burpy.git
cd burpy
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Burpy:
```bash
pip install -e .
```

### Direct Usage

You can also run Burpy directly without installation:

```bash
python -m burpy
```

## Quick Start

### 1. Start the Proxy Server

```bash
burpy proxy --host 127.0.0.1 --port 8080 --verbose
```

Configure your browser to use `127.0.0.1:8080` as HTTP proxy.

### 2. Scan for Vulnerabilities

```bash
burpy scan https://example.com --verbose
```

### 3. Use the Repeater

```bash
burpy repeat https://example.com/api/users --method POST --data '{"username":"admin"}'
```

### 4. Fuzz Parameters

```bash
burpy fuzz https://example.com/search --parameter q --wordlist wordlist.txt
```

### 5. View History

```bash
burpy history --limit 50
```

## Commands

### Proxy Commands

- `burpy proxy` - Start HTTP proxy server
- `--host HOST` - Proxy host (default: 127.0.0.1)
- `--port PORT` - Proxy port (default: 8080)
- `--verbose` - Enable verbose output

### Scanner Commands

- `burpy scan URL` - Scan URL for vulnerabilities
- `--output FILE` - Save results to file
- `--verbose` - Show detailed results

### Repeater Commands

- `burpy repeat URL` - Send HTTP request
- `--method METHOD` - HTTP method (default: GET)
- `--header "key:value"` - Add HTTP header
- `--data DATA` - Request body data

### Intruder Commands

- `burpy fuzz URL PARAMETER` - Fuzz parameter
- `--wordlist FILE` - Custom wordlist file
- `--threads N` - Number of threads (default: 10)

### History Commands

- `burpy history` - Show request history
- `burpy search QUERY` - Search history
- `--limit N` - Limit number of results

## Configuration

Burpy creates a configuration file (`burpy_config.json`) in the current directory. You can modify settings like:

- Proxy host and port
- Scanner timeout and threads
- Intruder settings
- Output preferences

## Security Features

### Vulnerability Scanner

- SQL Injection detection
- Cross-Site Scripting (XSS) testing
- Directory traversal checks
- Sensitive file discovery
- HTTP method enumeration
- Security header analysis

### Intruder Module

- Parameter fuzzing
- Authentication brute forcing
- Directory brute forcing
- SQL injection testing

## Examples

### Basic Web Application Testing

1. Start proxy and configure browser
2. Browse the target application
3. Review captured requests in history
4. Use repeater to modify and resend requests
5. Run vulnerability scanner on interesting endpoints
6. Use intruder for automated testing

### API Testing

```bash
# Test API endpoint
burpy repeat https://api.example.com/users --method GET --header "Authorization: Bearer token123"

# Fuzz API parameters
burpy fuzz https://api.example.com/search --parameter q --wordlist api_wordlist.txt

# Scan API for vulnerabilities
burpy scan https://api.example.com/users --verbose
```

## Requirements

- Python 3.7+
- Internet connection for target testing
- Browser for proxy testing

## Dependencies

- `requests` - HTTP library
- `click` - CLI framework
- `colorama` - Colored terminal output
- `pyyaml` - Configuration files
- `cryptography` - SSL/TLS support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and authorized testing purposes only. Only use it on systems you own or have explicit permission to test. The authors are not responsible for any misuse of this tool.

## Roadmap

- [ ] HTTPS proxy support
- [ ] Web interface
- [ ] Plugin system
- [ ] More vulnerability checks
- [ ] Report generation
- [ ] Session management
- [ ] Advanced fuzzing techniques