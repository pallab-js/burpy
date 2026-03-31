"""
Macro automation for recording and replaying sequences of HTTP requests
"""

import json
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import requests


class MacroStep:
    """Represents a single step in a macro"""
    
    def __init__(self, name: str, method: str, url: str, 
                 headers: Optional[Dict[str, str]] = None,
                 data: Optional[str] = None,
                 delay: float = 0.0,
                 extractors: Optional[List[Dict]] = None):
        self.name = name
        self.method = method
        self.url = url
        self.headers = headers or {}
        self.data = data
        self.delay = delay
        self.extractors = extractors or []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'method': self.method,
            'url': self.url,
            'headers': self.headers,
            'data': self.data,
            'delay': self.delay,
            'extractors': self.extractors
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroStep':
        return cls(
            name=data['name'],
            method=data['method'],
            url=data['url'],
            headers=data.get('headers'),
            data=data.get('data'),
            delay=data.get('delay', 0.0),
            extractors=data.get('extractors', [])
        )


class Macro:
    """A sequence of HTTP requests to be replayed"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.steps: List[MacroStep] = []
        self.variables: Dict[str, str] = {}
        self.created_at = datetime.now().isoformat()
        self.last_run = None
        self.run_count = 0
        
    def add_step(self, step: MacroStep) -> None:
        """Add a step to the macro"""
        self.steps.append(step)
        
    def set_variable(self, key: str, value: str) -> None:
        """Set a macro variable"""
        self.variables[key] = value
        
    def get_variable(self, key: str) -> Optional[str]:
        """Get a macro variable"""
        return self.variables.get(key)
        
    def _interpolate(self, text: str) -> str:
        """Replace {{variable}} placeholders with values"""
        if not text:
            return text
        for key, value in self.variables.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        return text
        
    def _extract(self, response: requests.Response, extractors: List[Dict]) -> Dict[str, str]:
        """Extract values from response"""
        results = {}
        for extractor in extractors:
            extract_type = extractor.get('type', 'regex')
            pattern = extractor.get('pattern', '')
            variable = extractor.get('variable', '')
            
            if extract_type == 'regex':
                import re
                match = re.search(pattern, response.text)
                if match:
                    results[variable] = match.group(1) if match.groups() else match.group(0)
            elif extract_type == 'json':
                import json
                try:
                    data = json.loads(response.text)
                    for key in extractor.get('path', '').split('.'):
                        data = data.get(key, {})
                    results[variable] = str(data)
                except:
                    pass
            elif extract_type == 'header':
                results[variable] = response.headers.get(pattern, '')
                
        return results
        
    def run(self, session: Optional[requests.Session] = None, 
            verbose: bool = False) -> Dict[str, Any]:
        """Execute the macro"""
        if session is None:
            session = requests.Session()
            session.verify = False
            
        results = {
            'macro': self.name,
            'started_at': datetime.now().isoformat(),
            'steps': [],
            'success': True
        }
        
        self.run_count += 1
        self.last_run = datetime.now().isoformat()
        
        for i, step in enumerate(self.steps):
            step_result = {
                'step': step.name,
                'method': step.method,
                'url': step.url,
                'success': False,
                'response': None
            }
            
            if verbose:
                print(f"[+] Running step: {step.name}")
                
            try:
                url = self._interpolate(step.url)
                headers = {k: self._interpolate(v) for k, v in step.headers.items()}
                data = self._interpolate(step.data) if step.data else None
                
                response = session.request(
                    method=step.method,
                    url=url,
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                step_result['status_code'] = response.status_code
                step_result['response_length'] = len(response.text)
                
                if step.extractors:
                    extracted = self._extract(response, step.extractors)
                    for key, value in extracted.items():
                        self.set_variable(key, value)
                        if verbose:
                            print(f"    [+] Extracted {key} = {value}")
                            
                step_result['success'] = True
                step_result['response'] = response.text[:500]
                
            except Exception as e:
                step_result['error'] = str(e)
                results['success'] = False
                
            results['steps'].append(step_result)
            
            if step.delay > 0:
                time.sleep(step.delay)
                
        results['completed_at'] = datetime.now().isoformat()
        return results
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'steps': [step.to_dict() for step in self.steps],
            'variables': self.variables,
            'created_at': self.created_at,
            'last_run': self.last_run,
            'run_count': self.run_count
        }
        
    def save(self, filepath: str) -> bool:
        """Save macro to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"[-] Error saving macro: {e}")
            return False
            
    @classmethod
    def load(cls, filepath: str) -> Optional['Macro']:
        """Load macro from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            macro = cls(data['name'], data.get('description', ''))
            macro.variables = data.get('variables', {})
            macro.created_at = data.get('created_at', datetime.now().isoformat())
            macro.last_run = data.get('last_run')
            macro.run_count = data.get('run_count', 0)
            for step_data in data.get('steps', []):
                macro.steps.append(MacroStep.from_dict(step_data))
            return macro
        except Exception as e:
            print(f"[-] Error loading macro: {e}")
            return None


class MacroCollection:
    """Collection of multiple macros"""
    
    def __init__(self):
        self._macros: Dict[str, Macro] = {}
        
    def add_macro(self, macro: Macro) -> None:
        """Add a macro to collection"""
        self._macros[macro.name] = macro
        
    def get_macro(self, name: str) -> Optional[Macro]:
        """Get macro by name"""
        return self._macros.get(name)
        
    def delete_macro(self, name: str) -> bool:
        """Delete a macro"""
        if name in self._macros:
            del self._macros[name]
            return True
        return False
        
    def list_macros(self) -> List[str]:
        """List all macro names"""
        return list(self._macros.keys())
        
    def save_all(self, directory: str = "macros") -> None:
        """Save all macros to directory"""
        import os
        os.makedirs(directory, exist_ok=True)
        for name, macro in self._macros.items():
            filepath = os.path.join(directory, f"{name}.json")
            macro.save(filepath)
            
    def load_all(self, directory: str = "macros") -> int:
        """Load all macros from directory"""
        import os
        loaded = 0
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith('.json'):
                    macro = Macro.load(os.path.join(directory, filename))
                    if macro:
                        self._macros[macro.name] = macro
                        loaded += 1
        return loaded