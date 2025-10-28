"""
Main CLI interface for Burpy
"""

import click
import sys
from colorama import init, Fore, Style
from burpy.core.proxy import HTTPProxy
from burpy.scanner.vulnerability_scanner import VulnerabilityScanner
from burpy.tools.repeater import RequestRepeater
from burpy.tools.intruder import Intruder
from burpy.history.logger import HistoryLogger
from burpy.config.settings import Config

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Global instances
config = Config()
history_logger = HistoryLogger()
proxy = None
scanner = VulnerabilityScanner()
repeater = RequestRepeater()
intruder = Intruder()


def print_banner():
    """Print Burpy banner"""
    banner = f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                        BURPY v1.0.0                         ║
║              CLI-based Web Security Testing Tool            ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
"""
    print(banner)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Burpy - CLI-based web security testing tool"""
    print_banner()


@cli.command()
@click.option('--host', default='127.0.0.1', help='Proxy host')
@click.option('--port', default=8080, help='Proxy port')
@click.option('--verbose', is_flag=True, help='Verbose output')
def proxy_cmd(host, port, verbose):
    """Start HTTP proxy server"""
    global proxy
    
    try:
        proxy = HTTPProxy(host, port)
        
        # Add request handler for logging
        def log_request(request):
            if verbose:
                print(f"{Fore.YELLOW}[REQUEST] {request['method']} {request['url']}{Style.RESET_ALL}")
            history_logger.log_request(request)
            return request
            
        # Add response handler for logging
        def log_response(response):
            if verbose:
                print(f"{Fore.GREEN}[RESPONSE] {response[:100]}...{Style.RESET_ALL}")
            return response
            
        proxy.add_request_handler(log_request)
        proxy.add_response_handler(log_response)
        
        print(f"{Fore.GREEN}[+] Starting proxy on {host}:{port}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Configure your browser to use {host}:{port} as HTTP proxy{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Press Ctrl+C to stop{Style.RESET_ALL}")
        
        proxy.start()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Stopping proxy...{Style.RESET_ALL}")
        if proxy:
            proxy.stop()
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('url')
@click.option('--output', '-o', help='Output file for results')
@click.option('--verbose', is_flag=True, help='Verbose output')
def scan(url, output, verbose):
    """Scan URL for vulnerabilities"""
    try:
        print(f"{Fore.CYAN}[+] Scanning {url}...{Style.RESET_ALL}")
        results = scanner.scan_url(url)
        
        if verbose:
            for result in results:
                severity_color = {
                    'high': Fore.RED,
                    'medium': Fore.YELLOW,
                    'low': Fore.BLUE,
                    'info': Fore.CYAN
                }.get(result['severity'], Fore.WHITE)
                
                print(f"{severity_color}[{result['severity'].upper()}] {result['title']}{Style.RESET_ALL}")
                print(f"  {result['description']}")
                if 'url' in result:
                    print(f"  URL: {result['url']}")
                print()
        
        # Save results if output file specified
        if output:
            import json
            with open(output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"{Fore.GREEN}[+] Results saved to {output}{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('url')
@click.option('--method', default='GET', help='HTTP method')
@click.option('--header', multiple=True, help='HTTP headers (format: key:value)')
@click.option('--data', help='Request body data')
def repeat(url, method, header, data):
    """Send HTTP request using repeater"""
    try:
        headers = {}
        for h in header:
            if ':' in h:
                key, value = h.split(':', 1)
                headers[key.strip()] = value.strip()
                
        print(f"{Fore.CYAN}[+] Sending {method} request to {url}...{Style.RESET_ALL}")
        response = repeater.send_request(method, url, headers, data)
        
        print(repeater.format_response(response))
        
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('url')
@click.argument('parameter')
@click.option('--wordlist', help='Wordlist file for fuzzing')
@click.option('--threads', default=10, help='Number of threads')
def fuzz(url, parameter, wordlist, threads):
    """Fuzz a parameter with wordlist"""
    try:
        if wordlist and os.path.exists(wordlist):
            with open(wordlist, 'r') as f:
                wordlist_data = [line.strip() for line in f if line.strip()]
        else:
            # Default wordlist
            wordlist_data = [
                'admin', 'test', 'login', 'user', 'password',
                'id', 'page', 'file', 'dir', 'backup'
            ]
            
        intruder.max_threads = threads
        print(f"{Fore.CYAN}[+] Fuzzing parameter '{parameter}' on {url}...{Style.RESET_ALL}")
        results = intruder.fuzz_parameter(url, parameter, wordlist_data)
        
        for result in results:
            if result['success']:
                status_color = Fore.GREEN if result['status_code'] == 200 else Fore.YELLOW
                print(f"{status_color}[{result['status_code']}] {result['payload']} - {result['response_length']} bytes{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[ERROR] {result['payload']} - {result['error']}{Style.RESET_ALL}")
                
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.option('--limit', default=20, help='Number of recent requests to show')
def history(limit):
    """Show request history"""
    try:
        history_entries = history_logger.get_history(limit)
        
        if not history_entries:
            print(f"{Fore.YELLOW}[!] No history found{Style.RESET_ALL}")
            return
            
        print(f"{Fore.CYAN}[+] Showing last {len(history_entries)} requests:{Style.RESET_ALL}\n")
        
        for entry in history_entries:
            request = entry['request']
            print(f"{Fore.BLUE}[{entry['id']}] {request['method']} {request['url']}{Style.RESET_ALL}")
            print(f"  Time: {entry['timestamp']}")
            if request.get('body'):
                print(f"  Body: {request['body'][:100]}...")
            print()
            
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('query')
def search(query):
    """Search request history"""
    try:
        results = history_logger.search_history(query)
        
        if not results:
            print(f"{Fore.YELLOW}[!] No results found for '{query}'{Style.RESET_ALL}")
            return
            
        print(f"{Fore.CYAN}[+] Found {len(results)} results for '{query}':{Style.RESET_ALL}\n")
        
        for entry in results:
            request = entry['request']
            print(f"{Fore.BLUE}[{entry['id']}] {request['method']} {request['url']}{Style.RESET_ALL}")
            print(f"  Time: {entry['timestamp']}")
            print()
            
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {e}{Style.RESET_ALL}")


if __name__ == '__main__':
    cli()