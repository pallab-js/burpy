"""
WebSocket testing support for intercepting and manipulating WebSocket traffic
"""

import json
import threading
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import requests


class WebSocketClient:
    """WebSocket client for testing"""
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._callbacks: List[Callable] = []
        
    def add_message_handler(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add a callback for incoming messages"""
        self._callbacks.append(callback)
        
    def record_message(self, direction: str, data: str, metadata: Optional[Dict] = None) -> None:
        """Record a WebSocket message"""
        with self._lock:
            message = {
                'timestamp': datetime.now().isoformat(),
                'direction': direction,  # 'sent' or 'received'
                'data': data,
                'metadata': metadata or {}
            }
            self.messages.append(message)
            
            for callback in self._callbacks:
                try:
                    callback(message)
                except Exception as e:
                    pass
                    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recorded messages"""
        with self._lock:
            if limit:
                return self.messages[-limit:]
            return self.messages.copy()
            
    def clear_messages(self) -> None:
        """Clear all recorded messages"""
        with self._lock:
            self.messages = []


class GraphQLTester:
    """GraphQL vulnerability testing"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        
    def detect_introspection(self, url: str) -> Optional[Dict[str, Any]]:
        """Detect if GraphQL introspection is enabled"""
        introspection_query = """
        {
            __schema {
                types {
                    name
                }
            }
        }
        """
        
        endpoints = [
            url,
            f"{url.rstrip('/')}/graphql",
            f"{url.rstrip('/')}/api/graphql",
            f"{url.rstrip('/')}/v1/graphql"
        ]
        
        for endpoint in endpoints:
            try:
                response = self.session.post(
                    endpoint,
                    json={'query': introspection_query},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and '__schema' in data.get('data', {}):
                        return {
                            'endpoint': endpoint,
                            'introspection_enabled': True,
                            'types': data['data']['__schema'].get('types', [])
                        }
            except:
                continue
                
        return {'introspection_enabled': False}
        
    def test_field_suggestions(self, url: str) -> Optional[Dict[str, Any]]:
        """Test for field suggestions (potential info leak)"""
        query = """
        {
            suggested
        }
        """
        
        try:
            response = self.session.post(url, json={'query': query}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'errors' not in data:
                    return {
                        'field_suggestions': True,
                        'message': 'Field suggestions may reveal schema'
                    }
        except:
            pass
            
        return {'field_suggestions': False}
        
    def test_batch_queries(self, url: str) -> Optional[Dict[str, Any]]:
        """Test for batched query vulnerability"""
        batch_query = [
            {'query': '{ __schema { types { name } } }'},
            {'query': '{ __typename }'}
        ]
        
        try:
            response = self.session.post(url, json=batch_query, timeout=10)
            if response.status_code == 200:
                return {
                    'batch_queries': True,
                    'data': response.json()
                }
        except:
            pass
            
        return {'batch_queries': False}
        
    def test_aggregate_queries(self, url: str) -> Dict[str, Any]:
        """Test for aggregate query DoS vulnerability"""
        results = {}
        
        expensive_queries = [
            """
            {
                users {
                    posts {
                        comments {
                            author {
                                posts {
                                    comments {
                                        author { ... }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            """,
            """
            query {
                __schema {
                    types {
                        fields {
                            type { fields { type { fields } } }
                        }
                    }
                }
            }
            """
        ]
        
        for i, query in enumerate(expensive_queries):
            start_time = time.time()
            try:
                response = self.session.post(url, json={'query': query}, timeout=5)
                elapsed = time.time() - start_time
                results[f'query_{i+1}'] = {
                    'status': response.status_code,
                    'time': elapsed,
                    'potential_dos': elapsed > 2
                }
            except Exception as e:
                results[f'query_{i+1}'] = {'error': str(e)}
                
        return results
        
    def test_mutations(self, url: str) -> Dict[str, Any]:
        """Test for dangerous mutations"""
        results = {}
        
        test_mutations = [
            ('delete', '{ deleteUser(id: 1) { success } }'),
            ('update', '{ updateUser(id: 1, input: {}) { success } }'),
            ('create', '{ createUser(input: {}) { id } }')
        ]
        
        for name, mutation in test_mutations:
            try:
                response = self.session.post(url, json={'query': mutation}, timeout=10)
                results[name] = {
                    'allowed': response.status_code != 405,
                    'response': response.text[:200]
                }
            except Exception as e:
                results[name] = {'error': str(e)}
                
        return results
        
    def scan(self, url: str) -> List[Dict[str, Any]]:
        """Perform comprehensive GraphQL security scan"""
        results = []
        
        print(f"[+] Scanning GraphQL endpoint: {url}")
        
        introspection = self.detect_introspection(url)
        if introspection and introspection.get('introspection_enabled'):
            results.append({
                'type': 'info',
                'title': 'GraphQL Introspection Enabled',
                'description': 'Schema introspection is enabled, revealing API structure',
                'severity': 'low',
                'endpoint': introspection.get('endpoint')
            })
            
            if introspection.get('types'):
                results.append({
                    'type': 'info',
                    'title': 'GraphQL Types Discovered',
                    'description': f"Found {len(introspection['types'])} types",
                    'severity': 'info',
                    'types': introspection['types'][:10]
                })
                
        field_suggestions = self.test_field_suggestions(url)
        if field_suggestions and field_suggestions.get('field_suggestions'):
            results.append({
                'type': 'info',
                'title': 'Field Suggestions Enabled',
                'description': field_suggestions.get('message', ''),
                'severity': 'low'
            })
            
        batch = self.test_batch_queries(url)
        if batch and batch.get('batch_queries'):
            results.append({
                'type': 'vulnerability',
                'title': 'Batch Queries Enabled',
                'description': 'Batch queries could be used for enumeration',
                'severity': 'medium'
            })
            
        dos_results = self.test_aggregate_queries(url)
        for query_name, result in dos_results.items():
            if result.get('potential_dos'):
                results.append({
                    'type': 'vulnerability',
                    'title': f'Potential DoS: {query_name}',
                    'description': 'Complex nested query could cause DoS',
                    'severity': 'high'
                })
                
        mutation_results = self.test_mutations(url)
        for mutation_name, result in mutation_results.items():
            if result.get('allowed') and 'error' not in result:
                results.append({
                    'type': 'info',
                    'title': f'Mutation {mutation_name} Available',
                    'description': f'Mutation endpoint responds to {mutation_name}',
                    'severity': 'info'
                })
                
        return results