import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from performance.locust.utils.auth_helper import get_auth_token, encrypt_password
except ImportError:
    print("Warning: auth_helper import failed, will attempt direct import")
    try:
        import importlib.util
        auth_helper_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "performance", "locust", "utils", "auth_helper.py"
        )
        spec = importlib.util.spec_from_file_location("auth_helper", auth_helper_path)
        auth_helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auth_helper)
        get_auth_token = auth_helper.get_auth_token
        encrypt_password = auth_helper.encrypt_password
    except Exception as e:
        print(f"Failed to import auth_helper: {e}")
        get_auth_token = None
        encrypt_password = None


class SecurityScanner:
    def __init__(self, base_url: str, api_url: str = None, api_username: str = None, api_password: str = None, 
                 api_client_id: str = None, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.api_url = api_url.rstrip("/") if api_url else base_url.rstrip("/")
        self.session = requests.Session()
        self.session.verify = False
        self.session.timeout = timeout
        self.session.headers.update({
            "User-Agent": "SecurityScanner/1.0"
        })
        self.api_username = api_username
        self.api_password = api_password
        self.api_client_id = api_client_id
        self.vulnerabilities: List[Dict[str, Any]] = []
        self.scan_results: Dict[str, Any] = {
            "scan_start": None,
            "scan_end": None,
            "scan_duration": None,
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "vulnerabilities": [],
            "warnings": [],
            "info": []
        }
        self.auth_token = None
        self.auth_headers = {}
    
    def login(self):
        if self.api_username and self.api_password:
            try:
                print(f"[*] Attempting login with username: {self.api_username}")
                encrypted_pwd = self.api_password
                try:
                    import base64
                    base64.b64decode(self.api_password)
                    print("[*] Password appears to be already encrypted, using as-is")
                except:
                    if encrypt_password and self.api_client_id:
                        try:
                            encrypted_pwd = encrypt_password(self.api_password, self.api_client_id)
                            print("[*] Password encrypted successfully")
                        except Exception as e:
                            print(f"[!] Password encryption failed, using plain password: {e}")
                
                auth_url = f"{self.api_url}/auth/login"
                response = self.session.post(auth_url, json={
                    "username": self.api_username,
                    "password": encrypted_pwd,
                    "clientId": self.api_client_id,
                    "grant_type": "password",
                    "grantType": "password"
                })
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.auth_token = data.get("access_token", data.get("token"))
                        if not self.auth_token and "data" in data:
                            self.auth_token = data["data"].get("access_token", data["data"].get("token"))
                        if self.auth_token:
                            self.auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
                            self.session.headers.update(self.auth_headers)
                            print("[+] Login successful")
                            return True
                        else:
                            print("[-] Login failed: No token received")
                            print(f"    Response: {response.text[:200]}")
                    except Exception as e:
                        print(f"[-] Failed to parse response: {e}")
                else:
                    print(f"[-] Login failed: Status {response.status_code}")
                    print(f"    Response: {response.text[:200]}")
            except Exception as e:
                print(f"[-] Login error: {e}")
        else:
            print("[!] Skipping login - missing credentials")
        return False
    
    def scan_sql_injection(self, endpoints: List[str]):
        print("\n[*] Starting SQL Injection scan...")
        sql_payloads = [
            "' OR '1'='1", "' OR 1=1--", "' AND '1'='1",
            "' UNION SELECT 1,2,3--", "'; DROP TABLE users--",
            "1'; WAITFOR DELAY '0:0:5'--", "' OR SLEEP(5)--"
        ]
        
        for endpoint in endpoints:
            for payload in sql_payloads:
                try:
                    url = f"{self.base_url}{endpoint}"
                    if "?" in url:
                        url += f"&test={payload}"
                    else:
                        url += f"?test={payload}"
                    
                    start_time = time.time()
                    response = self.session.get(url)
                    elapsed_time = time.time() - start_time
                    
                    is_vulnerable = False
                    indicators = [
                        "error in your SQL syntax", "mysql_fetch", "pg_fetch",
                        "ORA-", "SQL Server", "unclosed quotation mark",
                        "syntax error", "Query failed"
                    ]
                    
                    for indicator in indicators:
                        if indicator.lower() in response.text.lower():
                            is_vulnerable = True
                            break
                    
                    if elapsed_time > 4:
                        is_vulnerable = True
                    
                    if is_vulnerable:
                        self.vulnerabilities.append({
                            "type": "SQL Injection",
                            "severity": "HIGH",
                            "endpoint": endpoint,
                            "payload": payload,
                            "response_code": response.status_code,
                            "evidence": response.text[:500]
                        })
                        print(f"  [!] SQL Injection found at {endpoint}")
                    
                    self.scan_results["total_checks"] += 1
                    if not is_vulnerable:
                        self.scan_results["passed_checks"] += 1
                    else:
                        self.scan_results["failed_checks"] += 1
                        
                except Exception as e:
                    print(f"  [-] Error scanning {endpoint}: {e}")
    
    def scan_xss(self, endpoints: List[str]):
        print("\n[*] Starting XSS scan...")
        xss_payloads = [
            "<script>alert(1)</script>", "<img src=x onerror=alert(1)>",
            "<svg/onload=alert(1)>", "<body onload=alert(1)>",
            "\";alert(1);//", "';alert(1);//"
        ]
        
        for endpoint in endpoints:
            for payload in xss_payloads:
                try:
                    url = f"{self.base_url}{endpoint}"
                    if "?" in url:
                        url += f"&test={payload}"
                    else:
                        url += f"?test={payload}"
                    
                    response = self.session.get(url)
                    
                    if payload in response.text:
                        self.vulnerabilities.append({
                            "type": "XSS",
                            "severity": "MEDIUM",
                            "endpoint": endpoint,
                            "payload": payload,
                            "response_code": response.status_code,
                            "evidence": "Payload reflected in response"
                        })
                        print(f"  [!] XSS found at {endpoint}")
                    
                    self.scan_results["total_checks"] += 1
                    if payload not in response.text:
                        self.scan_results["passed_checks"] += 1
                    else:
                        self.scan_results["failed_checks"] += 1
                        
                except Exception as e:
                    print(f"  [-] Error scanning {endpoint}: {e}")
    
    def scan_path_traversal(self, endpoints: List[str]):
        print("\n[*] Starting Path Traversal scan...")
        path_payloads = [
            "../../etc/passwd", "../../../etc/passwd",
            "../../windows/system32/config/sam",
            "../../../windows/system32/config/sam",
            "../../etc/hosts", "../../../etc/hosts",
            "../../proc/version", "../../../proc/version"
        ]
        
        for endpoint in endpoints:
            for payload in path_payloads:
                try:
                    url = f"{self.base_url}{endpoint}"
                    if "?" in url:
                        url += f"&file={payload}"
                    else:
                        url += f"?file={payload}"
                    
                    response = self.session.get(url)
                    
                    if "root:" in response.text or "windows/system32" in response.text.lower() or \
                       "Linux version" in response.text or "localhost" in response.text:
                        self.vulnerabilities.append({
                            "type": "Path Traversal",
                            "severity": "HIGH",
                            "endpoint": endpoint,
                            "payload": payload,
                            "response_code": response.status_code,
                            "evidence": response.text[:500]
                        })
                        print(f"  [!] Path Traversal found at {endpoint}")
                    
                    self.scan_results["total_checks"] += 1
                    if not ("root:" in response.text or "windows/system32" in response.text.lower() or \
                            "Linux version" in response.text):
                        self.scan_results["passed_checks"] += 1
                    else:
                        self.scan_results["failed_checks"] += 1
                        
                except Exception as e:
                    print(f"  [-] Error scanning {endpoint}: {e}")
    
    def scan_security_headers(self):
        print("\n[*] Checking Security Headers...")
        required_headers = {
            "Strict-Transport-Security": "HSTS not set",
            "Content-Security-Policy": "CSP not set",
            "X-Content-Type-Options": "X-Content-Type-Options not set",
            "X-Frame-Options": "X-Frame-Options not set",
            "X-XSS-Protection": "X-XSS-Protection not set"
        }
        
        try:
            response = self.session.get(self.base_url)
            missing_headers = []
            
            for header, warning in required_headers.items():
                if header.lower() not in [h.lower() for h in response.headers.keys()]:
                    missing_headers.append(warning)
                    self.scan_results["warnings"].append({
                        "type": "Security Header Missing",
                        "header": header,
                        "description": warning
                    })
            
            if missing_headers:
                print(f"  [!] Missing security headers: {', '.join(missing_headers)}")
            else:
                print("  [+] All security headers present")
            
            self.scan_results["total_checks"] += 1
            if not missing_headers:
                self.scan_results["passed_checks"] += 1
            else:
                self.scan_results["failed_checks"] += 1
                
        except Exception as e:
            print(f"  [-] Error checking headers: {e}")
    
    def scan_cors(self):
        print("\n[*] Checking CORS Configuration...")
        try:
            response = self.session.options(self.base_url)
            
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin", ""),
                "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials", ""),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods", "")
            }
            
            if cors_headers["Access-Control-Allow-Origin"] == "*" and \
               cors_headers["Access-Control-Allow-Credentials"] == "true":
                self.vulnerabilities.append({
                    "type": "CORS Misconfiguration",
                    "severity": "MEDIUM",
                    "endpoint": "/",
                    "payload": "Preflight request",
                    "response_code": response.status_code,
                    "evidence": f"Origin: {cors_headers['Access-Control-Allow-Origin']}, Credentials: {cors_headers['Access-Control-Allow-Credentials']}"
                })
                print("  [!] CORS misconfiguration: Wildcard origin with credentials allowed")
            
            self.scan_results["total_checks"] += 1
            if not (cors_headers["Access-Control-Allow-Origin"] == "*" and \
                    cors_headers["Access-Control-Allow-Credentials"] == "true"):
                self.scan_results["passed_checks"] += 1
            else:
                self.scan_results["failed_checks"] += 1
                
        except Exception as e:
            print(f"  [-] Error checking CORS: {e}")
    
    def scan_directory_listing(self, endpoints: List[str]):
        print("\n[*] Checking Directory Listing...")
        dir_payloads = ["/", "/api/", "/docs/", "/static/", "/public/"]
        
        for payload in dir_payloads:
            try:
                url = f"{self.base_url}{payload}"
                response = self.session.get(url)
                
                if "Index of" in response.text or "<title>Directory listing" in response.text:
                    self.vulnerabilities.append({
                        "type": "Directory Listing",
                        "severity": "LOW",
                        "endpoint": payload,
                        "payload": payload,
                        "response_code": response.status_code,
                        "evidence": "Directory listing enabled"
                    })
                    print(f"  [!] Directory listing enabled at {payload}")
                
                self.scan_results["total_checks"] += 1
                if not ("Index of" in response.text or "<title>Directory listing" in response.text):
                    self.scan_results["passed_checks"] += 1
                else:
                    self.scan_results["failed_checks"] += 1
                    
            except Exception as e:
                print(f"  [-] Error checking {payload}: {e}")
    
    def scan_sensitive_info_leak(self):
        print("\n[*] Checking Sensitive Information Leak...")
        sensitive_paths = {
            "/.git/config": ["[core]", "repositoryformatversion"],
            "/.git/HEAD": ["ref:", "HEAD"],
            "/.svn/entries": ["dir", "file"],
            "/config.ini": ["[", "="],
            "/.env": ["=", "_"],
            "/.env.example": ["=", "_"],
            "/swagger.json": ["swagger", "openapi", "\"paths\""],
            "/openapi.json": ["openapi", "\"paths\""],
            "/api-docs": ["swagger", "openapi", "\"paths\""]
        }
        
        for path, indicators in sensitive_paths.items():
            try:
                url = f"{self.base_url}{path}"
                response = self.session.get(url)
                
                is_sensitive = False
                if response.status_code == 200 and len(response.text) > 0:
                    for indicator in indicators:
                        if indicator.lower() in response.text.lower():
                            is_sensitive = True
                            break
                
                if is_sensitive:
                    self.vulnerabilities.append({
                        "type": "Sensitive Information Leak",
                        "severity": "MEDIUM",
                        "endpoint": path,
                        "payload": path,
                        "response_code": response.status_code,
                        "evidence": f"Content length: {len(response.text)} bytes"
                    })
                    print(f"  [!] Sensitive file accessible: {path}")
                
                self.scan_results["total_checks"] += 1
                if not is_sensitive:
                    self.scan_results["passed_checks"] += 1
                else:
                    self.scan_results["failed_checks"] += 1
                    
            except Exception as e:
                print(f"  [-] Error checking {path}: {e}")
    
    def scan_unauthorized_access(self, protected_endpoints: List[str]):
        print("\n[*] Checking Unauthorized Access...")
        if not self.auth_token:
            print("  [!] Skipping unauthorized access check - not logged in")
            return
        
        original_headers = dict(self.session.headers)
        self.session.headers.pop("Authorization", None)
        
        for endpoint in protected_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = self.session.get(url)
                
                is_vulnerable = False
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "code" in data and data["code"] == 401:
                            is_vulnerable = False
                        elif "data" in data or "records" in data:
                            is_vulnerable = True
                    except:
                        if len(response.text) > 100:
                            is_vulnerable = True
                
                if is_vulnerable:
                    self.vulnerabilities.append({
                        "type": "Unauthorized Access",
                        "severity": "HIGH",
                        "endpoint": endpoint,
                        "payload": "No auth header",
                        "response_code": response.status_code,
                        "evidence": "Access granted without authentication"
                    })
                    print(f"  [!] Unauthorized access possible at {endpoint}")
                
                self.scan_results["total_checks"] += 1
                if not is_vulnerable:
                    self.scan_results["passed_checks"] += 1
                else:
                    self.scan_results["failed_checks"] += 1
                    
            except Exception as e:
                print(f"  [-] Error checking {endpoint}: {e}")
        
        self.session.headers.update(original_headers)
    
    def run(self):
        print(f"\n{'='*60}")
        print(f"[*] Starting Security Scan on {self.base_url}")
        print(f"{'='*60}")
        
        self.scan_results["scan_start"] = datetime.now().isoformat()
        start_time = time.time()
        
        endpoints_to_scan = [
            "/auth/login", "/crm/customer/page", "/crm/business/page",
            "/crm/clue/page", "/crm/contact/page", "/sys/user/page"
        ]
        
        protected_endpoints = [
            "/crm/customer/page", "/crm/business/page", "/crm/clue/page"
        ]
        
        self.login()
        
        self.scan_security_headers()
        self.scan_cors()
        self.scan_directory_listing(endpoints_to_scan)
        self.scan_sensitive_info_leak()
        self.scan_sql_injection(endpoints_to_scan)
        self.scan_xss(endpoints_to_scan)
        self.scan_path_traversal(endpoints_to_scan)
        self.scan_unauthorized_access(protected_endpoints)
        
        end_time = time.time()
        self.scan_results["scan_end"] = datetime.now().isoformat()
        self.scan_results["scan_duration"] = round(end_time - start_time, 2)
        self.scan_results["vulnerabilities"] = self.vulnerabilities
        
        print(f"\n{'='*60}")
        print("[*] Scan Complete")
        print(f"{'='*60}")
        print(f"Total Checks: {self.scan_results['total_checks']}")
        print(f"Passed: {self.scan_results['passed_checks']}")
        print(f"Failed: {self.scan_results['failed_checks']}")
        print(f"Vulnerabilities Found: {len(self.vulnerabilities)}")
        print(f"Duration: {self.scan_results['scan_duration']}s")
        
        if self.vulnerabilities:
            print("\n[!] Vulnerabilities Found:")
            for v in self.vulnerabilities:
                print(f"  - [{v['severity']}] {v['type']} at {v['endpoint']}")
        
        return self.scan_results


def generate_html_report(results: Dict[str, Any], output_path: str):
    vuln_table = ""
    if results['vulnerabilities']:
        rows = []
        for v in results['vulnerabilities']:
            rows.append(f"""<tr>
                <td>{v['type']}</td>
                <td class="severity-{v['severity'].lower()}">{v['severity']}</td>
                <td>{v['endpoint']}</td>
                <td>{v['payload']}</td>
                <td>{v['response_code']}</td>
                <td class="evidence">{v['evidence']}</td>
            </tr>""")
        vuln_table = f"""<table>
            <tr><th>类型</th><th>严重程度</th><th>端点</th><th>载荷</th><th>响应码</th><th>证据</th></tr>
            {''.join(rows)}
        </table>"""
    else:
        vuln_table = '<p style="color: #2e7d32; font-weight: bold;">未发现安全漏洞</p>'
    
    warnings_list = ""
    if results['warnings']:
        warnings_list = '<ul>' + ''.join([f'<li>{w["description"]}</li>' for w in results['warnings']]) + '</ul>'
    else:
        warnings_list = '<p>无警告信息</p>'
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>安全测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .summary-box {{ flex: 1; padding: 15px; border-radius: 8px; text-align: center; }}
        .total {{ background: #e8f5e9; color: #2e7d32; }}
        .passed {{ background: #e3f2fd; color: #1565c0; }}
        .failed {{ background: #ffebee; color: #c62828; }}
        .vuln {{ background: #fff3e0; color: #ef6c00; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
        .severity-high {{ color: #c62828; font-weight: bold; }}
        .severity-medium {{ color: #ef6c00; }}
        .severity-low {{ color: #1565c0; }}
        .evidence {{ font-family: monospace; font-size: 12px; max-height: 100px; overflow-y: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>安全测试报告</h1>
        <p style="text-align: center; color: #666;">扫描时间: {results['scan_start']}</p>
        
        <div class="summary">
            <div class="summary-box total">
                <h3>总检查项</h3>
                <p style="font-size: 24px;">{results['total_checks']}</p>
            </div>
            <div class="summary-box passed">
                <h3>通过</h3>
                <p style="font-size: 24px;">{results['passed_checks']}</p>
            </div>
            <div class="summary-box failed">
                <h3>失败</h3>
                <p style="font-size: 24px;">{results['failed_checks']}</p>
            </div>
            <div class="summary-box vuln">
                <h3>漏洞数</h3>
                <p style="font-size: 24px;">{len(results['vulnerabilities'])}</p>
            </div>
        </div>
        
        <h2>漏洞详情</h2>
        {vuln_table}
        
        <h2>警告信息</h2>
        {warnings_list}
        
        <p style="text-align: center; color: #666; margin-top: 20px;">扫描耗时: {results['scan_duration']}秒</p>
    </div>
</body>
</html>"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"[+] HTML report generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Security Scanner')
    parser.add_argument('--host', required=True, help='Target host URL')
    parser.add_argument('--api-url', help='API base URL (default: same as host)')
    parser.add_argument('--username', help='API username')
    parser.add_argument('--password', help='API password')
    parser.add_argument('--client-id', help='API client ID')
    parser.add_argument('--output', help='Output directory for reports')
    args = parser.parse_args()
    
    scanner = SecurityScanner(
        base_url=args.host,
        api_url=args.api_url,
        api_username=args.username,
        api_password=args.password,
        api_client_id=args.client_id
    )
    
    results = scanner.run()
    
    if args.output:
        html_path = os.path.join(args.output, 'security_report.html')
        generate_html_report(results, html_path)
        
        json_path = os.path.join(args.output, 'security_results.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[+] JSON results saved: {json_path}")
    
    exit(0)


if __name__ == "__main__":
    main()