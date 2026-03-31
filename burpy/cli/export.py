"""
CI/CD Export functionality for generating scan reports in various formats
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class ReportExporter:
    """Export scan results in various formats for CI/CD integration"""
    
    @staticmethod
    def export_json(results: List[Dict[str, Any]], filepath: str) -> bool:
        """Export results as JSON"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'tool': 'Burpy',
                'version': '1.0.0',
                'total_findings': len(results),
                'results': results
            }
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            return True
        except Exception as e:
            print(f"[-] Error exporting JSON: {e}")
            return False
            
    @staticmethod
    def export_sarif(results: List[Dict[str, Any]], filepath: str) -> bool:
        """Export results as SARIF format for GitHub/GitLab integration"""
        sarif = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "Burpy",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/burpy/burpy"
                    }
                },
                "results": []
            }]
        }
        
        severity_map = {
            'high': 'error',
            'medium': 'warning', 
            'low': 'note',
            'info': 'note'
        }
        
        for result in results:
            sarif_run = sarif["runs"][0]
            sarif_run["results"].append({
                "ruleId": result.get('title', 'unknown'),
                "level": severity_map.get(result.get('severity', 'info'), 'note'),
                "message": {
                    "text": result.get('description', '')
                },
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": result.get('url', 'unknown')
                        }
                    }
                }]
            })
            
        try:
            with open(filepath, 'w') as f:
                json.dump(sarif, f, indent=2)
            return True
        except Exception as e:
            print(f"[-] Error exporting SARIF: {e}")
            return False
            
    @staticmethod
    def export_csv(results: List[Dict[str, Any]], filepath: str) -> bool:
        """Export results as CSV"""
        try:
            import csv
            if not results:
                return True
                
            fieldnames = ['type', 'title', 'description', 'severity', 'url']
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
            return True
        except Exception as e:
            print(f"[-] Error exporting CSV: {e}")
            return False
            
    @staticmethod
    def export_html(results: List[Dict[str, Any]], filepath: str) -> bool:
        """Export results as HTML report"""
        severity_colors = {
            'high': '#dc3545',
            'medium': '#ffc107',
            'low': '#17a2b8',
            'info': '#6c757d'
        }
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Burpy Security Scan Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
        .finding {{ margin: 10px 0; padding: 15px; border-left: 4px solid; background: #fff; }}
        .finding.high {{ border-color: #dc3545; }}
        .finding.medium {{ border-color: #ffc107; }}
        .finding.low {{ border-color: #17a2b8; }}
        .finding.info {{ border-color: #6c757d; }}
        .severity {{ font-weight: bold; text-transform: uppercase; }}
    </style>
</head>
<body>
    <h1>Burpy Security Scan Report</h1>
    <div class="summary">
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Findings:</strong> {len(results)}</p>
    </div>
"""
        
        for result in results:
            severity = result.get('severity', 'info')
            html += f"""
    <div class="finding {severity}">
        <span class="severity" style="color: {severity_colors.get(severity, '#666')}">{severity}</span>
        <h3>{result.get('title', 'Unknown')}</h3>
        <p>{result.get('description', '')}</p>
        {"<p><strong>URL:</strong> " + result.get('url', '') + "</p>" if result.get('url') else ""}
    </div>
"""
        
        html += """
</body>
</html>"""
        
        try:
            with open(filepath, 'w') as f:
                f.write(html)
            return True
        except Exception as e:
            print(f"[-] Error exporting HTML: {e}")
            return False
            
    @staticmethod
    def export_markdown(results: List[Dict[str, Any]], filepath: str) -> bool:
        """Export results as Markdown"""
        md = f"""# Burpy Security Scan Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Findings:** {len(results)}

"""
        
        by_severity = {'high': [], 'medium': [], 'low': [], 'info': []}
        for result in results:
            severity = result.get('severity', 'info')
            by_severity.setdefault(severity, []).append(result)
            
        for severity in ['high', 'medium', 'low', 'info']:
            if by_severity[severity]:
                md += f"## {severity.upper()} Severity\n\n"
                for result in by_severity[severity]:
                    md += f"### {result.get('title', 'Unknown')}\n\n"
                    md += f"{result.get('description', '')}\n\n"
                    if result.get('url'):
                        md += f"**URL:** {result['url']}\n\n"
                        
        try:
            with open(filepath, 'w') as f:
                f.write(md)
            return True
        except Exception as e:
            print(f"[-] Error exporting Markdown: {e}")
            return False
            
    @staticmethod
    def export_junit(results: List[Dict[str, Any]], filepath: str) -> bool:
        """Export results as JUnit XML for CI/CD pipelines"""
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<testsuite name="Burpy Security Scan" tests="{}">\n'.format(len(results))
        
        for result in results:
            severity = result.get('severity', 'info')
            test_class = 'SecurityScan'
            test_name = result.get('title', 'Unknown')
            
            failure = ''
            if severity in ['high', 'medium']:
                failure = f"""    <testcase classname="{test_class}" name="{test_name}">
    <failure message="{result.get('description', '')}">{result.get('description', '')}
URL: {result.get('url', 'N/A')}
</failure>
</testcase>
"""
            else:
                failure = f'    <testcase classname="{test_class}" name="{test_name}"/>\n'
                
            xml += failure
            
        xml += '</testsuite>\n'
        
        try:
            with open(filepath, 'w') as f:
                f.write(xml)
            return True
        except Exception as e:
            print(f"[-] Error exporting JUnit: {e}")
            return False


def generate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics from scan results"""
    summary = {
        'total': len(results),
        'by_severity': {},
        'by_type': {},
        'high_priority_urls': []
    }
    
    for result in results:
        severity = result.get('severity', 'info')
        summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
        
        result_type = result.get('type', 'unknown')
        summary['by_type'][result_type] = summary['by_type'].get(result_type, 0) + 1
        
        if severity == 'high' and result.get('url'):
            summary['high_priority_urls'].append(result['url'])
            
    return summary