"""
Core HTTP proxy functionality for intercepting and modifying requests/responses
"""

import socket
import threading
import time
import ssl
import os
import tempfile
from urllib.parse import urlparse, urlunparse
import requests
from typing import Optional, Dict, Any, Callable, List, Tuple
import json


class HTTPProxy:
    """HTTP proxy server for intercepting web traffic"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080, 
                 ssl_cert: Optional[str] = None, ssl_key: Optional[str] = None):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.request_handlers: List[Callable] = []
        self.response_handlers: List[Callable] = []
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self._ssl_context = None
        self._ca_cert_path = None
        self._ca_key_path = None
        self._connect_timeout = 10
        self._request_timeout = 30
        self.client_headers = {}
        
    def add_request_handler(self, handler: Callable[[Dict], Optional[Dict]]):
        """Add a request handler function"""
        self.request_handlers.append(handler)
        
    def add_response_handler(self, handler: Callable[[str], Optional[str]]):
        """Add a response handler function"""
        self.response_handlers.append(handler)
        
    def set_ssl_certificates(self, cert_path: str, key_path: str):
        """Set SSL certificate paths for HTTPS interception"""
        self.ssl_cert = cert_path
        self.ssl_key = key_path
        
    def generate_ca_certificates(self):
        """Generate CA certificates for HTTPS MITM"""
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import datetime
        
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Burpy"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Burpy Proxy"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Burpy CA"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).sign(key, hashes.SHA256())
        
        temp_dir = tempfile.mkdtemp()
        cert_path = os.path.join(temp_dir, "ca.crt")
        key_path = os.path.join(temp_dir, "ca.key")
        
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        self._ca_cert_path = cert_path
        self._ca_key_path = key_path
        return cert_path, key_path
        
    def start(self):
        """Start the proxy server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)
        self.running = True
        
        print(f"[+] Proxy server started on {self.host}:{self.port}")
        
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_socket.settimeout(None)
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr)
                )
                thread.daemon = True
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[-] Error accepting connection: {e}")
                    
    def stop(self):
        """Stop the proxy server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("[+] Proxy server stopped")
        
    def _read_request_data(self, client_socket: socket.socket) -> str:
        """Read complete HTTP request with dynamic buffer"""
        chunks = []
        while True:
            chunk = client_socket.recv(8192)
            if not chunk:
                break
            chunks.append(chunk.decode('utf-8', errors='ignore'))
            
            if '\r\n\r\n' in ''.join(chunks):
                break
        
        # Check if we have Content-Length header
        full_data = ''.join(chunks)
        
        if 'Content-Length:' in full_data:
            header_end = full_data.find('\r\n\r\n')
            if header_end != -1:
                headers_part = full_data[:header_end]
                body_start = header_end + 4
                
                for line in headers_part.split('\r\n'):
                    if line.lower().startswith('content-length:'):
                        content_length = int(line.split(':')[1].strip())
                        body_present = len(full_data) - body_start
                        
                        if body_present < content_length:
                            remaining = client_socket.recv(content_length - body_present)
                            full_data += remaining.decode('utf-8', errors='ignore')
                        break
        
        return full_data
        
    def _handle_connect(self, client_socket: socket.socket, host: str, port: int) -> bool:
        """Handle HTTPS CONNECT tunneling"""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.settimeout(self._connect_timeout)
            server_socket.connect((host, port))
            
            client_socket.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            
            # Wrap both sockets with SSL
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            client_ssl = context.wrap_socket(client_socket, server_side=False)
            server_ssl = context.wrap_socket(server_socket, server_side=True)
            
            # Tunnel data bidirectionally
            self._tunnel_ssl(client_ssl, server_ssl)
            
            return True
            
        except Exception as e:
            print(f"[-] CONNECT tunnel error: {e}")
            return False
            
    def _tunnel_ssl(self, client_ssl, server_ssl):
        """Tunnel SSL data between client and server"""
        def forward(source, destination):
            try:
                while True:
                    data = source.recv(8192)
                    if not data:
                        break
                    destination.sendall(data)
            except:
                pass
            finally:
                source.close()
                destination.close()
        
        thread1 = threading.Thread(target=forward, args=(client_ssl, server_ssl))
        thread2 = threading.Thread(target=forward, args=(server_ssl, client_ssl))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        
    def _handle_client(self, client_socket: socket.socket, addr: tuple):
        """Handle client connection"""
        try:
            # Dynamic buffer reading for complete request
            request_data = self._read_request_data(client_socket)
            
            if not request_data:
                return
                
            # Parse the request
            request = self._parse_request(request_data)
            if not request:
                return
            
            # Check for CONNECT method (HTTPS tunneling)
            if request.get('method') == 'CONNECT':
                host_port = request.get('url', '').split(':')
                host = host_port[0]
                port = int(host_port[1]) if len(host_port) > 1 else 443
                self._handle_connect(client_socket, host, port)
                return
            
            # Store headers for session management
            self.client_headers = request.get('headers', {})
            
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
            
            # Build full URL with query string
            full_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            if parsed_url.query:
                full_url = f"{full_url}?{parsed_url.query}"
            
            # Prepare headers for requests library
            headers = dict(request['headers'])
            headers.pop('Host', None)  # Let requests handle Host header
            
            # Make the request
            session = requests.Session()
            
            response = session.request(
                method=request['method'],
                url=full_url,
                headers=headers,
                data=request['body'] if request['body'] else None,
                allow_redirects=False,
                verify=False,
                timeout=self._request_timeout
            )
            
            # Format response
            response_text = f"{request['version']} {response.status_code} {response.reason}\r\n"
            
            # Include Set-Cookie headers
            for key, value in response.headers.items():
                response_text += f"{key}: {value}\r\n"
                
            response_text += "\r\n"
            response_text += response.text
            
            return response_text
            
        except requests.exceptions.Timeout:
            print(f"[-] Request timeout: {request.get('url')}")
            return "HTTP/1.1 504 Gateway Timeout\r\n\r\n"
        except requests.exceptions.ConnectionError as e:
            print(f"[-] Connection error: {e}")
            return "HTTP/1.1 502 Bad Gateway\r\n\r\n"
        except Exception as e:
            print(f"[-] Error forwarding request: {e}")
            return None