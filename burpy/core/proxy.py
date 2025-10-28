"""
Core HTTP proxy functionality for intercepting and modifying requests/responses
"""

import socket
import threading
import time
import ssl
from urllib.parse import urlparse
import requests
from typing import Optional, Dict, Any, Callable
import json


class HTTPProxy:
    """HTTP proxy server for intercepting web traffic"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.request_handlers = []
        self.response_handlers = []
        
    def add_request_handler(self, handler: Callable):
        """Add a request handler function"""
        self.request_handlers.append(handler)
        
    def add_response_handler(self, handler: Callable):
        """Add a response handler function"""
        self.response_handlers.append(handler)
        
    def start(self):
        """Start the proxy server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"[+] Proxy server started on {self.host}:{self.port}")
        
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr)
                )
                thread.daemon = True
                thread.start()
            except Exception as e:
                if self.running:
                    print(f"[-] Error accepting connection: {e}")
                    
    def stop(self):
        """Stop the proxy server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("[+] Proxy server stopped")
        
    def _handle_client(self, client_socket: socket.socket, addr: tuple):
        """Handle client connection"""
        try:
            # Receive the request
            request_data = client_socket.recv(4096).decode('utf-8', errors='ignore')
            
            if not request_data:
                return
                
            # Parse the request
            request = self._parse_request(request_data)
            if not request:
                return
                
            # Apply request handlers
            for handler in self.request_handlers:
                try:
                    request = handler(request) or request
                except Exception as e:
                    print(f"[-] Request handler error: {e}")
                    
            # Forward the request
            response_data = self._forward_request(request)
            
            if response_data:
                # Apply response handlers
                for handler in self.response_handlers:
                    try:
                        response_data = handler(response_data) or response_data
                    except Exception as e:
                        print(f"[-] Response handler error: {e}")
                        
                # Send response back to client
                client_socket.send(response_data.encode('utf-8', errors='ignore'))
                
        except Exception as e:
            print(f"[-] Error handling client {addr}: {e}")
        finally:
            client_socket.close()
            
    def _parse_request(self, request_data: str) -> Optional[Dict[str, Any]]:
        """Parse HTTP request"""
        try:
            lines = request_data.split('\r\n')
            if not lines:
                return None
                
            # Parse request line
            request_line = lines[0].split()
            if len(request_line) < 3:
                return None
                
            method, url, version = request_line
            
            # Parse headers
            headers = {}
            body_start = 0
            for i, line in enumerate(lines[1:], 1):
                if line == '':
                    body_start = i + 1
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip()] = value.strip()
                    
            # Parse body
            body = '\r\n'.join(lines[body_start:]) if body_start < len(lines) else ''
            
            return {
                'method': method,
                'url': url,
                'version': version,
                'headers': headers,
                'body': body,
                'raw': request_data
            }
        except Exception as e:
            print(f"[-] Error parsing request: {e}")
            return None
            
    def _forward_request(self, request: Dict[str, Any]) -> Optional[str]:
        """Forward request to target server"""
        try:
            # Parse URL
            if request['url'].startswith('http'):
                parsed_url = urlparse(request['url'])
            else:
                # Assume HTTP if no scheme
                parsed_url = urlparse(f"http://{request['url']}")
                
            # Prepare headers for requests library
            headers = dict(request['headers'])
            headers.pop('Host', None)  # Let requests handle Host header
            
            # Make the request
            response = requests.request(
                method=request['method'],
                url=f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}",
                headers=headers,
                data=request['body'] if request['body'] else None,
                allow_redirects=False,
                verify=False,
                timeout=30
            )
            
            # Format response
            response_text = f"{request['version']} {response.status_code} {response.reason}\r\n"
            
            for key, value in response.headers.items():
                response_text += f"{key}: {value}\r\n"
                
            response_text += "\r\n"
            response_text += response.text
            
            return response_text
            
        except Exception as e:
            print(f"[-] Error forwarding request: {e}")
            return None