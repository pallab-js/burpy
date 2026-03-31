"""
Main CLI interface for Burpy
"""

import click
import sys
import os
import json
import warnings
import urllib3
from colorama import init, Fore, Style
from burpy.core.proxy import HTTPProxy
from burpy.scanner.vulnerability_scanner import VulnerabilityScanner
from burpy.tools.repeater import RequestRepeater
from burpy.tools.intruder import Intruder
from burpy.tools.websocket import GraphQLTester
from burpy.history.logger import HistoryLogger
from burpy.history.session import SessionManager, SessionManagerCollection
from burpy.tools.macro import Macro, MacroCollection
from burpy.cli.export import ReportExporter
from burpy.cli.formatter import OutputFormatter, format_output
from burpy.config.settings import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

init(autoreset=True)

config = Config()
history_logger = HistoryLogger()
proxy = None
scanner = VulnerabilityScanner()
repeater = RequestRepeater()
intruder = Intruder()


def print_banner():
    banner = f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                        BURPY v1.1.0                         ║
║           CLI-based Web Security Testing Tool               ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
    """
    print(banner)


@click.group()
@click.version_option(version="1.1.0")
@click.option('--quiet', '-q', is_flag=True, help='Suppress banner and reduce output')
def cli(quiet):
    """Burpy - CLI-based web security testing tool"""
    if not quiet:
        print_banner()


@cli.command()
@click.option('--host', default='127.0.0.1', help='Proxy host address')
@click.option('--port', default=8080, help='Proxy port number')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def proxy_cmd(host, port, verbose):
    """Start HTTP/HTTPS intercepting proxy server"""
    global proxy
    
    try:
        proxy = HTTPProxy(host, port)
        
        def log_request(request):
            if verbose:
                msg = f"{Fore.YELLOW}[REQUEST] {request['method']} {request['url']}{Style.RESET_ALL}"
                click.echo(msg)
            history_logger.log_request(request)
            return request
            
        def log_response(response):
            if verbose:
                msg = f"{Fore.GREEN}[RESPONSE] {response[:100]}...{Style.RESET_ALL}"
                click.echo(msg)
            return response
            
        proxy.add_request_handler(log_request)
        proxy.add_response_handler(log_response)
        
        click.echo(format_output('proxy', None, host=host, port=port))
        
        proxy.start()
        
    except KeyboardInterrupt:
        click.echo(f"\n{Fore.YELLOW}[!] Stopping proxy...{Style.RESET_ALL}")
        if proxy:
            proxy.stop()
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('url')
@click.option('--output', '-o', help='Save results to file')
@click.option('--format', '-f', type=click.Choice(['json', 'html', 'csv']), default='json', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed findings')
def scan(url, output, format, verbose):
    """Scan URL for web vulnerabilities (SQLi, XSS, etc.)"""
    try:
        click.echo(f"{Fore.CYAN}ℹ Scanning {url}...{Style.RESET_ALL}")
        
        results = scanner.scan_url(url)
        
        if verbose:
            click.echo(format_output('scan', results, target=url))
        else:
            by_severity = {'high': 0, 'medium': 0, 'low': 0, 'info': 0}
            for r in results:
                sev = r.get('severity', 'info')
                by_severity[sev] = by_severity.get(sev, 0) + 1
            
            click.echo(f"\n{Fore.CYAN}Scan Complete:{Style.RESET_ALL}")
            click.echo(f"  {Fore.RED}High: {by_severity['high']}{Style.RESET_ALL}")
            click.echo(f"  {Fore.YELLOW}Medium: {by_severity['medium']}{Style.RESET_ALL}")
            click.echo(f"  {Fore.BLUE}Low: {by_severity['low']}{Style.RESET_ALL}")
            click.echo(f"  {Fore.CYAN}Info: {by_severity['info']}{Style.RESET_ALL}")
        
        if output:
            if format == 'json':
                ReportExporter.export_json(results, output)
            elif format == 'html':
                ReportExporter.export_html(results, output)
            elif format == 'csv':
                ReportExporter.export_csv(results, output)
            click.echo(f"{Fore.GREEN}✓ Results saved to {output}{Style.RESET_ALL}")
            
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('url')
@click.option('--method', '-m', default='GET', help='HTTP method (GET, POST, PUT, etc.)')
@click.option('--header', '-H', multiple=True, help='HTTP header (key:value)')
@click.option('--data', '-d', help='Request body data')
@click.option('--json', 'json_data', is_flag=True, help='Send data as JSON')
def repeat(url, method, header, data, json_data):
    """Send HTTP request and view response (Repeater)"""
    try:
        headers = {}
        for h in header:
            if ':' in h:
                key, value = h.split(':', 1)
                headers[key.strip()] = value.strip()
        
        if json_data:
            headers['Content-Type'] = 'application/json'
        
        click.echo(f"{Fore.CYAN}ℹ Sending {method} request to {url}{Style.RESET_ALL}")
        
        response = repeater.send_request(method, url, headers, data)
        
        click.echo(format_output('repeater', response, url=url, method=method))
        
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('url')
@click.argument('parameter')
@click.option('--wordlist', '-w', help='Wordlist file path')
@click.option('--threads', '-t', default=10, help='Number of parallel threads')
@click.option('--delay', '-d', default=0.0, type=float, help='Delay between requests (seconds)')
def fuzz(url, parameter, wordlist, threads, delay):
    """Fuzz a parameter with wordlist (Intruder)"""
    try:
        if wordlist and os.path.exists(wordlist):
            with open(wordlist, 'r') as f:
                wordlist_data = [line.strip() for line in f if line.strip()]
        else:
            wordlist_data = [
                'admin', 'test', 'login', 'user', 'password',
                'id', 'page', 'file', 'dir', 'backup', 'config'
            ]
        
        intruder.max_threads = threads
        intruder.set_delay(delay)
        
        click.echo(f"{Fore.CYAN}ℹ Fuzzing parameter '{parameter}' on {url}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}ℹ Payloads: {len(wordlist_data)} | Threads: {threads} | Delay: {delay}s{Style.RESET_ALL}")
        
        results = intruder.fuzz_parameter(url, parameter, wordlist_data)
        
        click.echo(format_output('fuzz', results, target=url, parameter=parameter))
        
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.option('--limit', '-n', default=20, help='Number of recent requests to show')
@click.option('--full', is_flag=True, help='Show full request details')
def history(limit, full):
    """Show request history"""
    try:
        history_entries = history_logger.get_history(limit)
        
        if not history_entries:
            click.echo(f"{Fore.YELLOW}⚠ No history found{Style.RESET_ALL}")
            return
        
        click.echo(format_output('history', history_entries, limit=limit))
        
        if full:
            for entry in history_entries[-5:]:
                request = entry.get('request', {})
                click.echo(f"\n{Fore.CYAN}Request #{entry['id']}:{Style.RESET_ALL}")
                click.echo(f"  {json.dumps(request, indent=2)[:500]}")
                
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('query')
def search(query):
    """Search request history by URL, method, or content"""
    try:
        results = history_logger.search_history(query)
        
        if not results:
            click.echo(f"{Fore.YELLOW}⚠ No results found for '{query}'{Style.RESET_ALL}")
            return
        
        click.echo(f"{Fore.CYAN}ℹ Found {len(results)} results for '{query}':{Style.RESET_ALL}\n")
        
        for entry in results:
            request = entry.get('request', {})
            method = request.get('method', 'GET')
            method_color = {'GET': Fore.GREEN, 'POST': Fore.CYAN, 'PUT': Fore.YELLOW, 'DELETE': Fore.RED}.get(method.upper(), Fore.WHITE)
            
            click.echo(f"{Fore.BLUE}[{entry['id']}] {method_color}{method}{Style.RESET_ALL} {request.get('url', '')}")
            click.echo(f"  {Fore.BLUE}Time:{Style.RESET_ALL} {entry.get('timestamp', '')}")
            
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('url')
@click.option('--format', '-f', type=click.Choice(['json', 'sarif', 'csv', 'html', 'markdown', 'junit']), default='json')
@click.option('--output', '-o', help='Output file path')
def export(url, format, output):
    """Scan and export results in CI/CD friendly formats"""
    try:
        scanner = VulnerabilityScanner()
        
        click.echo(f"{Fore.CYAN}ℹ Scanning {url}...{Style.RESET_ALL}")
        results = scanner.scan_url(url)
        
        if not output:
            output = f"burpy_report.{format}"
            
        success = False
        if format == 'json':
            success = ReportExporter.export_json(results, output)
        elif format == 'sarif':
            success = ReportExporter.export_sarif(results, output)
        elif format == 'csv':
            success = ReportExporter.export_csv(results, output)
        elif format == 'html':
            success = ReportExporter.export_html(results, output)
        elif format == 'markdown':
            success = ReportExporter.export_markdown(results, output)
        elif format == 'junit':
            success = ReportExporter.export_junit(results, output)
        
        if success:
            click.echo(f"{Fore.GREEN}✓ Report saved to {output}{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.RED}✗ Failed to save report{Style.RESET_ALL}")
            
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('url')
def graphql(url):
    """Scan GraphQL endpoint for vulnerabilities"""
    try:
        tester = GraphQLTester()
        
        click.echo(f"{Fore.CYAN}ℹ Testing GraphQL endpoint: {url}{Style.RESET_ALL}")
        results = tester.scan(url)
        
        click.echo(format_output('graphql', results, endpoint=url))
        
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('name')
@click.option('--run', is_flag=True, help='Run the macro')
@click.option('--add-step', nargs=3, help='Add step: <method> <url> <name>')
def macro(name, run, add_step):
    """Create and manage request macros"""
    try:
        collection = MacroCollection()
        collection.load_all()
        
        macro_obj = collection.get_macro(name)
        
        if run and macro_obj:
            click.echo(f"{Fore.CYAN}ℹ Running macro: {name}{Style.RESET_ALL}")
            result = macro_obj.run()
            click.echo(format_output('macro', result))
        elif add_step and macro_obj:
            method, url, step_name = add_step
            from burpy.tools.macro import MacroStep
            step = MacroStep(step_name, method, url)
            macro_obj.add_step(step)
            collection.save_all()
            click.echo(f"{Fore.GREEN}✓ Added step to macro '{name}'{Style.RESET_ALL}")
        elif macro_obj:
            click.echo(f"{Fore.CYAN}Macro '{name}' exists with {len(macro_obj.steps)} steps{Style.RESET_ALL}")
            for i, step in enumerate(macro_obj.steps, 1):
                click.echo(f"  {i}. {step.method} {step.url} ({step.name})")
        else:
            new_macro = Macro(name)
            collection.add_macro(new_macro)
            collection.save_all()
            click.echo(f"{Fore.GREEN}✓ Created new macro: {name}{Style.RESET_ALL}")
            
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.option('--format', '-f', type=click.Choice(['har', 'json']), default='har')
@click.option('--output', '-o', help='Output file path')
def history_export(format, output):
    """Export request history to file"""
    try:
        if not output:
            output = f"burpy_history.{format}"
        
        if format == 'har':
            success = history_logger.export_har(output)
        else:
            if not output.endswith('.json'):
                output += '.json'
            history_logger.export_history(output)
            success = True
        
        if success:
            click.echo(f"{Fore.GREEN}✓ History exported to {output}{Style.RESET_ALL}")
            
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
@click.argument('url')
@click.option('--parameter', '-p', help='Parameter to fuzz')
@click.option('--wordlist', '-w', help='Wordlist file')
@click.option('--delay', '-d', default=0.0, type=float, help='Delay between requests')
@click.option('--threads', '-t', default=10, help='Number of threads')
def attack(url, parameter, wordlist, delay, threads):
    """Run automated attack with rate limiting (Brute Force/Dir Scan)"""
    try:
        intruder.max_threads = threads
        intruder.set_delay(delay)
        
        if wordlist and os.path.exists(wordlist):
            with open(wordlist, 'r') as f:
                wordlist_data = [line.strip() for line in f if line.strip()]
        else:
            wordlist_data = ['admin', 'test', 'root', 'password', '123456', 'login']
        
        click.echo(f"{Fore.CYAN}ℹ Starting attack on {url}{Style.RESET_ALL}")
        click.echo(f"{Fore.YELLOW}  Delay: {delay}s | Threads: {threads} | Payloads: {len(wordlist_data)}{Style.RESET_ALL}")
        
        if parameter:
            results = intruder.fuzz_parameter(url, parameter, wordlist_data)
            
            success_count = sum(1 for r in results if r.get('success') and r.get('status_code', 0) < 400)
            click.echo(f"\n{Fore.GREEN}✓ Completed: {success_count}/{len(results)} successful responses{Style.RESET_ALL}")
            
            for r in results[:20]:
                if r.get('success'):
                    status = r.get('status_code', 0)
                    if status < 300:
                        click.echo(f"  [{Fore.GREEN}{status}{Style.RESET_ALL}] {r.get('payload', '')}")
                    elif status < 400:
                        click.echo(f"  [{Fore.CYAN}{status}{Style.RESET_ALL}] {r.get('payload', '')}")
        else:
            results = intruder.directory_brute_force(url, wordlist_data)
            
            found = [r for r in results if r.get('success') and r.get('status_code', 0) in [200, 301, 302]]
            click.echo(f"\n{Fore.GREEN}✓ Found {len(found)} directories/pages{Style.RESET_ALL}")
            
            for r in found[:20]:
                click.echo(f"  [{Fore.GREEN}{r.get('status_code')}{Style.RESET_ALL}] {r.get('path', '')}")
        
    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
def info():
    """Show Burpy tool information and options"""
    info_text = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                     BURPY TOOL INFORMATION                      ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.WHITE}Commands:{Style.RESET_ALL}
  {Fore.GREEN}proxy{Style.RESET_ALL}                  Start HTTP/HTTPS intercepting proxy
  {Fore.GREEN}scan{Style.RESET_ALL}    <url>         Scan for web vulnerabilities
  {Fore.GREEN}repeat{Style.RESET_ALL}  <url>        Send custom HTTP requests
  {Fore.GREEN}fuzz{Style.RESET_ALL}     <url> <param>  Fuzz parameter with wordlist
  {Fore.GREEN}attack{Style.RESET_ALL}   <url>        Automated attack (fuzz/dir scan)
  {Fore.GREEN}graphql{Style.RESET_ALL}  <url>        Test GraphQL security
  {Fore.GREEN}history{Style.RESET_ALL}               View request history
  {Fore.GREEN}search{Style.RESET_ALL}  <query>      Search history
  {Fore.GREEN}macro{Style.RESET_ALL}    <name>       Manage request macros
  {Fore.GREEN}export{Style.RESET_ALL}   <url>        Scan and export (CI/CD)
  {Fore.GREEN}history-export{Style.RESET_ALL}        Export history to file

{Fore.WHITE}Options:{Style.RESET_ALL}
  --help                Show this help message
  --version            Show version
  -v, --verbose        Verbose output
  -o, --output         Output file
  -H, --header         Custom HTTP header
  -d, --data           Request body
  -w, --wordlist       Wordlist file
  -t, --threads        Number of threads
  -f, --format         Output format (json/csv/html/sarif/etc)

{Fore.WHITE}Examples:{Style.RESET_ALL}
  {Fore.CYAN}burpy scan https://example.com --verbose{Style.RESET_ALL}
  {Fore.CYAN}burpy repeat https://api.example.com -m POST -H "Auth: Bearer token"{Style.RESET_ALL}
  {Fore.CYAN}burpy fuzz https://site.com search -w wordlist.txt -t 20{Style.RESET_ALL}
  {Fore.CYAN}burpy export https://site.com -f sarif -o results.sarif{Style.RESET_ALL}
    """
    click.echo(info_text)


if __name__ == '__main__':
    cli()