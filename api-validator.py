#!/usr/bin/env python3
"""
API Validator for AgentArmy
Validates connectivity and health of all integrated APIs:
- Cerebras AI
- Tavily Search
- Azure OpenAI / Microsoft Foundry
- Custom endpoints
"""

import json
import sys
import os
import requests
import argparse
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class APIStatus(Enum):
    HEALTHY = "✓"
    DEGRADED = "⚠"
    UNHEALTHY = "✗"
    UNKNOWN = "?"

@dataclass
class APIValidationResult:
    name: str
    api_type: str
    status: str  # "✓", "⚠", "✗"
    status_code: Optional[int] = None
    latency_ms: Optional[float] = None
    message: str = ""
    details: Optional[Dict[str, Any]] = None

class APIValidator:
    def __init__(self, keyvault_name: Optional[str] = None):
        self.keyvault_name = keyvault_name
        self.results: List[APIValidationResult] = []
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment or Key Vault."""
        keys = {}

        # Try environment variables first
        keys['cerebras'] = os.getenv('CEREBRAS_API_KEY', '')
        keys['tavily'] = os.getenv('TAVILY_API_KEY', '')
        keys['foundry'] = os.getenv('FOUNDRY_API_KEY', '')
        keys['openai'] = os.getenv('OPENAI_API_KEY', '')

        # Try Key Vault if configured
        if self.keyvault_name:
            try:
                cerebras_key = subprocess.run(
                    f'az keyvault secret show --vault-name {self.keyvault_name} --name cerebras-api-key -o json',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if cerebras_key.returncode == 0:
                    data = json.loads(cerebras_key.stdout)
                    keys['cerebras'] = data.get('value', '')

                tavily_key = subprocess.run(
                    f'az keyvault secret show --vault-name {self.keyvault_name} --name tavily-api-key -o json',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if tavily_key.returncode == 0:
                    data = json.loads(tavily_key.stdout)
                    keys['tavily'] = data.get('value', '')
            except Exception as e:
                print(f"Warning: Could not fetch keys from Key Vault: {e}")

        return keys

    def validate_cerebras(self) -> APIValidationResult:
        """Validate Cerebras AI API connectivity."""
        print(f"\n{Colors.BOLD}🧠 Validating Cerebras API...{Colors.RESET}")

        api_key = self.api_keys.get('cerebras', '')
        if not api_key:
            result = APIValidationResult(
                name="Cerebras AI",
                api_type="LLM",
                status="✗",
                message="API key not found in environment or Key Vault"
            )
            print(f"  ✗ No API key configured")
            self.results.append(result)
            return result

        try:
            import time
            start_time = time.time()

            # Test with simple model list request
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            response = requests.get(
                'https://api.cerebras.ai/v1/models',
                headers=headers,
                timeout=10
            )

            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                status = APIStatus.HEALTHY.value
                message = f"{len(models)} models available"
                status_text = "✓"
            elif response.status_code == 401:
                status = APIStatus.UNHEALTHY.value
                message = "Authentication failed - invalid API key"
                status_text = "✗"
            elif response.status_code == 429:
                status = APIStatus.DEGRADED.value
                message = "Rate limited - quota exceeded"
                status_text = "⚠"
            else:
                status = APIStatus.DEGRADED.value
                message = f"HTTP {response.status_code}"
                status_text = "⚠"

            result = APIValidationResult(
                name="Cerebras AI",
                api_type="LLM",
                status=status_text,
                status_code=response.status_code,
                latency_ms=latency_ms,
                message=message,
                details={
                    'endpoint': 'https://api.cerebras.ai/v1',
                    'models_count': len(models) if response.status_code == 200 else None
                }
            )

            print(f"  {status_text} Cerebras API - {message} ({latency_ms:.0f}ms)")

        except requests.exceptions.Timeout:
            result = APIValidationResult(
                name="Cerebras AI",
                api_type="LLM",
                status="✗",
                message="Request timeout"
            )
            print(f"  ✗ Timeout connecting to Cerebras API")

        except requests.exceptions.ConnectionError as e:
            result = APIValidationResult(
                name="Cerebras AI",
                api_type="LLM",
                status="✗",
                message=f"Connection error: {str(e)[:100]}"
            )
            print(f"  ✗ Connection error to Cerebras API")

        except Exception as e:
            result = APIValidationResult(
                name="Cerebras AI",
                api_type="LLM",
                status="✗",
                message=f"Error: {str(e)[:100]}"
            )
            print(f"  ✗ Error validating Cerebras API: {str(e)[:50]}")

        self.results.append(result)
        return result

    def validate_tavily(self) -> APIValidationResult:
        """Validate Tavily Search API connectivity."""
        print(f"\n{Colors.BOLD}🔍 Validating Tavily Search API...{Colors.RESET}")

        api_key = self.api_keys.get('tavily', '')
        if not api_key:
            result = APIValidationResult(
                name="Tavily Search",
                api_type="Search",
                status="✗",
                message="API key not found in environment or Key Vault"
            )
            print(f"  ✗ No API key configured")
            self.results.append(result)
            return result

        try:
            import time
            start_time = time.time()

            # Test with simple search request
            payload = {
                "api_key": api_key,
                "query": "test",
                "include_answer": True,
                "max_results": 1
            }

            response = requests.post(
                'https://api.tavily.com/search',
                json=payload,
                timeout=10
            )

            latency_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                status = APIStatus.HEALTHY.value
                message = "Search API operational"
                status_text = "✓"
                results_count = len(data.get('results', []))
            elif response.status_code == 401:
                status = APIStatus.UNHEALTHY.value
                message = "Authentication failed - invalid API key"
                status_text = "✗"
                results_count = 0
            else:
                status = APIStatus.DEGRADED.value
                message = f"HTTP {response.status_code}"
                status_text = "⚠"
                results_count = 0

            result = APIValidationResult(
                name="Tavily Search",
                api_type="Search",
                status=status_text,
                status_code=response.status_code,
                latency_ms=latency_ms,
                message=message,
                details={
                    'endpoint': 'https://api.tavily.com/search',
                    'search_results': results_count if response.status_code == 200 else None
                }
            )

            print(f"  {status_text} Tavily API - {message} ({latency_ms:.0f}ms)")

        except requests.exceptions.Timeout:
            result = APIValidationResult(
                name="Tavily Search",
                api_type="Search",
                status="✗",
                message="Request timeout"
            )
            print(f"  ✗ Timeout connecting to Tavily API")

        except requests.exceptions.ConnectionError as e:
            result = APIValidationResult(
                name="Tavily Search",
                api_type="Search",
                status="✗",
                message=f"Connection error: {str(e)[:100]}"
            )
            print(f"  ✗ Connection error to Tavily API")

        except Exception as e:
            result = APIValidationResult(
                name="Tavily Search",
                api_type="Search",
                status="✗",
                message=f"Error: {str(e)[:100]}"
            )
            print(f"  ✗ Error validating Tavily API: {str(e)[:50]}")

        self.results.append(result)
        return result

    def validate_foundry(self) -> APIValidationResult:
        """Validate Microsoft Foundry/Azure OpenAI connectivity."""
        print(f"\n{Colors.BOLD}🤖 Validating Microsoft Foundry...{Colors.RESET}")

        try:
            # Use Azure CLI to check Foundry deployment
            result = subprocess.run(
                'az cognitiveservices account show --name fndry-01 --resource-group rg-01 -o json',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                status = APIStatus.HEALTHY.value
                message = "Foundry deployment available"
                status_text = "✓"
                status_code = 200

                api_result = APIValidationResult(
                    name="Microsoft Foundry",
                    api_type="LLM/OpenAI",
                    status=status_text,
                    status_code=status_code,
                    message=message,
                    details={
                        'kind': data.get('kind'),
                        'sku': data.get('sku', {}).get('name'),
                        'location': data.get('location'),
                        'provisioningState': data.get('properties', {}).get('provisioningState')
                    }
                )
                print(f"  ✓ Foundry - {message}")

            else:
                status = APIStatus.UNHEALTHY.value
                message = "Foundry not found or access denied"
                status_text = "✗"

                api_result = APIValidationResult(
                    name="Microsoft Foundry",
                    api_type="LLM/OpenAI",
                    status=status_text,
                    message=message
                )
                print(f"  ✗ Foundry - {message}")

        except Exception as e:
            api_result = APIValidationResult(
                name="Microsoft Foundry",
                api_type="LLM/OpenAI",
                status="✗",
                message=f"Error: {str(e)[:100]}"
            )
            print(f"  ✗ Error validating Foundry: {str(e)[:50]}")

        self.results.append(api_result)
        return api_result

    def validate_custom_api(self, name: str, url: str, method: str = 'GET',
                           headers: Optional[Dict] = None) -> APIValidationResult:
        """Validate a custom API endpoint."""
        print(f"\n{Colors.BOLD}🔗 Validating {name}...{Colors.RESET}")

        try:
            import time
            start_time = time.time()

            response = requests.request(
                method=method,
                url=url,
                headers=headers or {},
                timeout=10
            )

            latency_ms = (time.time() - start_time) * 1000

            if 200 <= response.status_code < 300:
                status_text = "✓"
                message = "Healthy"
            elif 400 <= response.status_code < 500:
                status_text = "✗"
                message = f"Client error {response.status_code}"
            elif response.status_code >= 500:
                status_text = "⚠"
                message = f"Server error {response.status_code}"
            else:
                status_text = "⚠"
                message = f"Status {response.status_code}"

            result = APIValidationResult(
                name=name,
                api_type="Custom",
                status=status_text,
                status_code=response.status_code,
                latency_ms=latency_ms,
                message=message,
                details={'endpoint': url}
            )

            print(f"  {status_text} {name} - {message} ({latency_ms:.0f}ms)")

        except Exception as e:
            result = APIValidationResult(
                name=name,
                api_type="Custom",
                status="✗",
                message=f"Error: {str(e)[:100]}"
            )
            print(f"  ✗ Error validating {name}")

        self.results.append(result)
        return result

    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate validation report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "validation_summary": {
                "total_apis": len(self.results),
                "healthy": sum(1 for r in self.results if r.status == "✓"),
                "degraded": sum(1 for r in self.results if r.status == "⚠"),
                "unhealthy": sum(1 for r in self.results if r.status == "✗"),
            },
            "apis": [asdict(r) for r in self.results]
        }

        print(f"\n{Colors.BOLD}{'='*60}")
        print(f"📊 API VALIDATION REPORT")
        print(f"{'='*60}{Colors.RESET}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"\n{Colors.BOLD}Summary:{Colors.RESET}")
        print(f"  Total APIs: {report['validation_summary']['total_apis']}")
        print(f"  {Colors.GREEN}Healthy: {report['validation_summary']['healthy']}{Colors.RESET}")
        print(f"  {Colors.YELLOW}Degraded: {report['validation_summary']['degraded']}{Colors.RESET}")
        print(f"  {Colors.RED}Unhealthy: {report['validation_summary']['unhealthy']}{Colors.RESET}")

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n✓ Report saved to: {output_file}")

        return report

    def run_all_validations(self):
        """Run all API validations."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}🚀 Starting API Validation{Colors.RESET}")
        print(f"{Colors.BLUE}Checking all integrated APIs...{Colors.RESET}\n")

        self.validate_cerebras()
        self.validate_tavily()
        self.validate_foundry()

        return self.generate_report()

def main():
    parser = argparse.ArgumentParser(
        description="API Validator for AgentArmy - Validates Cerebras, Tavily, Foundry, and custom APIs"
    )
    parser.add_argument(
        '--keyvault',
        help='Azure Key Vault name to fetch API keys'
    )
    parser.add_argument(
        '--output',
        help='Output report to JSON file'
    )
    parser.add_argument(
        '--api',
        action='append',
        nargs=2,
        metavar=('NAME', 'URL'),
        help='Custom API to validate (can be used multiple times)'
    )

    args = parser.parse_args()

    validator = APIValidator(keyvault_name=args.keyvault)
    report = validator.run_all_validations()

    # Validate custom APIs if provided
    if args.api:
        for api_name, api_url in args.api:
            validator.validate_custom_api(api_name, api_url)

    if args.output:
        validator.generate_report(output_file=args.output)

    # Exit with error if any APIs are unhealthy
    if report['validation_summary']['unhealthy'] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
