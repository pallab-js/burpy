"""
Output formatter for professional CLI display
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from colorama import Fore, Style


class OutputFormatter:
    """Professional output formatting for CLI"""
    
    SEVERITY_COLORS = {
        'critical': Fore.MAGENTA,
        'high': Fore.RED,
        'medium': Fore.YELLOW,
        'low': Fore.BLUE,
        'info': Fore.CYAN,
        'error': Fore.RED
    }
    
    @staticmethod
    def separator(char: str = "─", length: int = 60) -> str:
        return f"{Fore.WHITE}{char * length}{Style.RESET_ALL}"
    
    @staticmethod
    def header(title: str, width: int = 60) -> str:
        padding = (width - len(title) - 2) // 2
        return f"\n{Fore.CYAN}{'═' * padding} {title} {'═' * padding}{Style.RESET_ALL}\n"
    
    @staticmethod
    def subheader(title: str) -> str:
        return f"\n{Fore.BLUE}▶ {title}{Style.RESET_ALL}\n"
    
    @staticmethod
    def success(message: str) -> str:
        return f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}"
    
    @staticmethod
    def error(message: str) -> str:
        return f"{Fore.RED}✗ {message}{Style.RESET_ALL}"
    
    @staticmethod
    def warning(message: str) -> str:
        return f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}"
    
    @staticmethod
    def info(message: str) -> str:
        return f"{Fore.CYAN}ℹ {message}{Style.RESET_ALL}"
    
    @staticmethod
    def label_value(label: str, value: str, indent: int = 2) -> str:
        return f"{' ' * indent}{Fore.WHITE}{label}:{Style.RESET_ALL} {value}"
    
    @staticmethod
    def table_row(columns: List[str], widths: List[int]) -> str:
        row = ""
        for col, width in zip(columns, widths):
            row += col.ljust(width + 2)
        return f"{Fore.WHITE}{row}{Style.RESET_ALL}"
    
    @staticmethod
    def format_scan_summary(results: List[Dict[str, Any]], target: str) -> str:
        """Format vulnerability scan results with summary"""
        output = []
        
        output.append(OutputFormatter.header("SECURITY SCAN REPORT"))
        
        by_severity = {'critical': [], 'high': [], 'medium': [], 'low': [], 'info': []}
        for r in results:
            sev = r.get('severity', 'info')
            if sev in by_severity:
                by_severity[sev].append(r)
            else:
                by_severity['info'].append(r)
        
        output.append(OutputFormatter.label_value("Target", target))
        output.append(OutputFormatter.label_value("Scan Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        output.append(OutputFormatter.label_value("Total Findings", str(len(results))))
        
        output.append("\n" + OutputFormatter.separator())
        
        output.append(f"\n{Fore.RED}SUMMARY:{Style.RESET_ALL}")
        output.append(f"  {Fore.MAGENTA}Critical: {len(by_severity['critical'])}{Style.RESET_ALL}")
        output.append(f"  {Fore.RED}High:     {len(by_severity['high'])}{Style.RESET_ALL}")
        output.append(f"  {Fore.YELLOW}Medium:   {len(by_severity['medium'])}{Style.RESET_ALL}")
        output.append(f"  {Fore.BLUE}Low:      {len(by_severity['low'])}{Style.RESET_ALL}")
        output.append(f"  {Fore.CYAN}Info:     {len(by_severity['info'])}{Style.RESET_ALL}")
        
        output.append("\n" + OutputFormatter.separator())
        
        output.append(f"\n{Fore.CYAN}DETAILED FINDINGS:{Style.RESET_ALL}")
        
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            if by_severity[severity]:
                output.append(f"\n{OutputFormatter.SEVERITY_COLORS[severity]}{severity.upper()}{Style.RESET_ALL}")
                output.append(OutputFormatter.separator("─", 40))
                
                for i, result in enumerate(by_severity[severity], 1):
                    output.append(f"\n  {i}. {Fore.WHITE}{result.get('title', 'Unknown')}{Style.RESET_ALL}")
                    output.append(f"     {result.get('description', '')}")
                    if result.get('url'):
                        output.append(f"     {Fore.BLUE}URL:{Style.RESET_ALL} {result['url']}")
                    if result.get('type'):
                        output.append(f"     {Fore.YELLOW}Type:{Style.RESET_ALL} {result['type']}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_fuzz_results(results: List[Dict[str, Any]], target: str, parameter: str) -> str:
        """Format fuzzing results"""
        output = []
        
        output.append(OutputFormatter.header("FUZZING RESULTS"))
        
        status_2xx = [r for r in results if r.get('success') and 200 <= r.get('status_code', 0) < 300]
        status_3xx = [r for r in results if r.get('success') and 300 <= r.get('status_code', 0) < 400]
        status_4xx = [r if r.get('success') else r for r in results if r.get('success') and 400 <= r.get('status_code', 0) < 500]
        status_5xx = [r for r in results if r.get('success') and 500 <= r.get('status_code', 0) < 600]
        errors = [r for r in results if not r.get('success')]
        
        output.append(OutputFormatter.label_value("Target", target))
        output.append(OutputFormatter.label_value("Parameter", parameter))
        output.append(OutputFormatter.label_value("Total Payloads", str(len(results))))
        
        output.append("\n" + OutputFormatter.separator())
        output.append(f"\n{Fore.CYAN}STATISTICS:{Style.RESET_ALL}")
        output.append(f"  {Fore.GREEN}2xx Success:  {len(status_2xx)}{Style.RESET_ALL}")
        output.append(f"  {Fore.CYAN}3xx Redirect: {len(status_3xx)}{Style.RESET_ALL}")
        output.append(f"  {Fore.YELLOW}4xx Client:   {len(status_4xx)}{Style.RESET_ALL}")
        output.append(f"  {Fore.RED}5xx Server:   {len(status_5xx)}{Style.RESET_ALL}")
        output.append(f"  {Fore.RED}Errors:      {len(errors)}{Style.RESET_ALL}")
        
        if status_2xx:
            output.append(f"\n{Fore.GREEN}INTERESTING RESULTS (2xx):{Style.RESET_ALL}")
            output.append(OutputFormatter.separator("─", 40))
            for r in status_2xx[:10]:
                output.append(f"  [{Fore.GREEN}{r.get('status_code')}{Style.RESET_ALL}] {r.get('payload', '')} ({r.get('response_length')} bytes)")
        
        if errors:
            output.append(f"\n{Fore.RED}ERRORS:{Style.RESET_ALL}")
            output.append(OutputFormatter.separator("─", 40))
            for r in errors[:5]:
                output.append(f"  {r.get('payload', '')}: {r.get('error', 'Unknown error')}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_history(entries: List[Dict[str, Any]], limit: int) -> str:
        """Format history entries"""
        output = []
        
        output.append(OutputFormatter.header("REQUEST HISTORY"))
        output.append(OutputFormatter.label_value("Total Requests", str(len(entries))))
        
        output.append("\n" + OutputFormatter.separator())
        
        headers = ["ID", "Method", "URL", "Time"]
        widths = [5, 8, 35, 12]
        
        output.append(OutputFormatter.table_row(
            [f"{Fore.CYAN}{h}{Style.RESET_ALL}" for h in headers],
            widths
        ))
        output.append(OutputFormatter.separator("─", 62))
        
        for entry in entries:
            request = entry.get('request', {})
            method = request.get('method', '')
            url = request.get('url', '')[:33]
            timestamp = entry.get('timestamp', '')[:10]
            
            method_color = {
                'GET': Fore.GREEN,
                'POST': Fore.CYAN,
                'PUT': Fore.YELLOW,
                'DELETE': Fore.RED,
                'PATCH': Fore.MAGENTA
            }.get(method.upper(), Fore.WHITE)
            
            output.append(OutputFormatter.table_row([
                f"{Fore.WHITE}{entry.get('id', '')}{Style.RESET_ALL}",
                f"{method_color}{method}{Style.RESET_ALL}",
                f"{Fore.WHITE}{url}{Style.RESET_ALL}",
                f"{Fore.BLUE}{timestamp}{Style.RESET_ALL}"
            ], widths))
        
        return "\n".join(output)
    
    @staticmethod
    def format_graphql_results(results: List[Dict[str, Any]], endpoint: str) -> str:
        """Format GraphQL scan results"""
        output = []
        
        output.append(OutputFormatter.header("GRAPHQL SECURITY SCAN"))
        
        output.append(OutputFormatter.label_value("Endpoint", endpoint))
        output.append(OutputFormatter.label_value("Findings", str(len(results))))
        
        output.append("\n" + OutputFormatter.separator())
        
        for i, result in enumerate(results, 1):
            severity = result.get('severity', 'info')
            color = OutputFormatter.SEVERITY_COLORS.get(severity, Fore.WHITE)
            
            output.append(f"\n{i}. {color}[{severity.upper()}]{Style.RESET_ALL} {result.get('title', '')}")
            output.append(f"   {result.get('description', '')}")
            
            if result.get('endpoint'):
                output.append(f"   {Fore.BLUE}Endpoint:{Style.RESET_ALL} {result['endpoint']}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_macro_result(result: Dict[str, Any]) -> str:
        """Format macro execution results"""
        output = []
        
        output.append(OutputFormatter.header("MACRO EXECUTION"))
        
        output.append(OutputFormatter.label_value("Macro", result.get('macro', '')))
        output.append(OutputFormatter.label_value("Started", result.get('started_at', '')))
        output.append(OutputFormatter.label_value("Completed", result.get('completed_at', '')))
        
        success_steps = [s for s in result.get('steps', []) if s.get('success')]
        failed_steps = [s for s in result.get('steps', []) if not s.get('success')]
        
        output.append(f"\n{Fore.GREEN}Success: {len(success_steps)}{Style.RESET_ALL}")
        output.append(f"{Fore.RED}Failed: {len(failed_steps)}{Style.RESET_ALL}")
        
        output.append("\n" + OutputFormatter.separator())
        output.append(f"\n{Fore.CYAN}STEP DETAILS:{Style.RESET_ALL}")
        
        for step in result.get('steps', []):
            status = OutputFormatter.success("OK") if step.get('success') else OutputFormatter.error("FAILED")
            output.append(f"\n  {status} {step.get('step', '')}")
            output.append(f"     Method: {step.get('method', '')} | URL: {step.get('url', '')[:50]}...")
            if step.get('status_code'):
                output.append(f"     Status: {step.get('status_code')}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_proxy_status(host: str, port: int) -> str:
        """Format proxy start status"""
        output = []
        
        output.append(OutputFormatter.header("PROXY SERVER"))
        output.append(OutputFormatter.label_value("Host", host))
        output.append(OutputFormatter.label_value("Port", str(port)))
        output.append(OutputFormatter.label_value("Status", f"{Fore.GREEN}RUNNING{Style.RESET_ALL}"))
        
        output.append("\n" + OutputFormatter.separator())
        output.append(f"\n{Fore.YELLOW}Instructions:{Style.RESET_ALL}")
        output.append(f"  1. Configure your browser to use {host}:{port} as HTTP proxy")
        output.append(f"  2. For HTTPS, accept the Burpy CA certificate")
        output.append(f"  3. Press Ctrl+C to stop the proxy")
        
        return "\n".join(output)
    
    @staticmethod
    def format_repeater_response(response: Dict[str, Any], url: str, method: str) -> str:
        """Format repeater response"""
        output = []
        
        output.append(OutputFormatter.header("HTTP RESPONSE"))
        
        if response.get('success'):
            output.append(OutputFormatter.label_value("URL", url))
            output.append(OutputFormatter.label_value("Method", method))
            output.append(OutputFormatter.label_value("Status", str(response.get('status_code', ''))))
            output.append(OutputFormatter.label_value("Time", f"{response.get('elapsed_time', 0):.3f}s"))
            
            output.append("\n" + OutputFormatter.separator())
            output.append(f"\n{Fore.CYAN}RESPONSE HEADERS:{Style.RESET_ALL}")
            for k, v in response.get('headers', {}).items():
                output.append(f"  {Fore.WHITE}{k}:{Style.RESET_ALL} {v}")
            
            output.append("\n" + OutputFormatter.separator())
            output.append(f"\n{Fore.CYAN}RESPONSE BODY:{Style.RESET_ALL}")
            output.append(f"{Fore.WHITE}{response.get('content', '')[:2000]}{Style.RESET_ALL}")
        else:
            output.append(OutputFormatter.error(f"Request failed: {response.get('error', 'Unknown error')}"))
        
        return "\n".join(output)


def format_output(command: str, data: Any, **kwargs) -> str:
    """Main formatting function"""
    formatter = OutputFormatter
    
    if command == 'scan':
        return formatter.format_scan_summary(data, kwargs.get('target', ''))
    elif command == 'fuzz':
        return formatter.format_fuzz_results(data, kwargs.get('target', ''), kwargs.get('parameter', ''))
    elif command == 'history':
        return formatter.format_history(data, kwargs.get('limit', 20))
    elif command == 'graphql':
        return formatter.format_graphql_results(data, kwargs.get('endpoint', ''))
    elif command == 'macro':
        return formatter.format_macro_result(data)
    elif command == 'proxy':
        return formatter.format_proxy_status(kwargs.get('host', ''), kwargs.get('port', 0))
    elif command == 'repeater':
        return formatter.format_repeater_response(data, kwargs.get('url', ''), kwargs.get('method', ''))
    else:
        return str(data)