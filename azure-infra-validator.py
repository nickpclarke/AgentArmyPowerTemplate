#!/usr/bin/env python3
"""
Azure Infrastructure Validator & Inventory Tool
Validates and inventories all Azure resources for AgentArmy
"""

import json
import sys
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import argparse

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

@dataclass
class ResourceStatus:
    name: str
    resource_type: str
    status: str  # "✓", "✗", "⚠"
    message: str
    location: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class AzureValidator:
    def __init__(self, subscription: str = "AASub1"):
        self.subscription = subscription
        self.results: List[ResourceStatus] = []
        self.inventory = {}

    def run_az_command(self, command: str) -> tuple[bool, Any]:
        """Execute Azure CLI command and return result."""
        try:
            result = subprocess.run(
                f"az {command} --subscription {self.subscription} -o json",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                try:
                    return True, json.loads(result.stdout)
                except json.JSONDecodeError:
                    return True, result.stdout
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timeout"
        except Exception as e:
            return False, str(e)

    def validate_key_vault(self):
        """Validate Azure Key Vault access."""
        print(f"\n{Colors.BOLD}🔐 Validating Key Vault...{Colors.RESET}")

        success, result = self.run_az_command("keyvault list")
        if not success:
            self.results.append(ResourceStatus(
                name="Key Vault",
                resource_type="Microsoft.KeyVault/vaults",
                status="✗",
                message=f"Failed to list: {result[:100]}"
            ))
            return

        vaults = result if isinstance(result, list) else []
        self.inventory["keyvaults"] = vaults

        for vault in vaults:
            vault_name = vault.get("name", "unknown")
            location = vault.get("location", "unknown")

            # Test secret access
            secret_success, secrets = self.run_az_command(
                f"keyvault secret list --vault-name {vault_name}"
            )

            if secret_success:
                secret_count = len(secrets) if isinstance(secrets, list) else 0
                status = "✓"
                message = f"{secret_count} secrets accessible"
            else:
                status = "⚠"
                message = "RBAC restricted"
                secret_count = 0

            self.results.append(ResourceStatus(
                name=vault_name,
                resource_type="Microsoft.KeyVault/vaults",
                status=status,
                location=location,
                message=message,
                details={"secrets": secret_count}
            ))
            print(f"  {status} {vault_name} ({location}) - {message}")

    def validate_cosmos_db(self):
        """Validate Cosmos DB access."""
        print(f"\n{Colors.BOLD}🗄️  Validating Cosmos DB...{Colors.RESET}")

        success, result = self.run_az_command("cosmosdb list")
        if not success:
            self.results.append(ResourceStatus(
                name="Cosmos DB",
                resource_type="Microsoft.DocumentDB/databaseAccounts",
                status="✗",
                message=f"Failed to list: {result[:100]}"
            ))
            return

        accounts = result if isinstance(result, list) else []
        self.inventory["cosmos_accounts"] = accounts

        for account in accounts:
            account_name = account.get("name", "unknown")
            location = account.get("location", "unknown")
            kind = account.get("kind", "unknown")

            status = "✓"
            message = f"Kind: {kind}"

            self.results.append(ResourceStatus(
                name=account_name,
                resource_type="Microsoft.DocumentDB/databaseAccounts",
                status=status,
                location=location,
                message=message,
                details={
                    "kind": kind,
                    "provisioningState": account.get("properties", {}).get("provisioningState", "unknown")
                }
            ))
            print(f"  {status} {account_name} ({location}) - {message}")

    def validate_foundry(self):
        """Validate Microsoft Foundry/Azure OpenAI."""
        print(f"\n{Colors.BOLD}🤖 Validating Microsoft Foundry...{Colors.RESET}")

        success, result = self.run_az_command("cognitiveservices account list")
        if not success:
            self.results.append(ResourceStatus(
                name="Microsoft Foundry",
                resource_type="Microsoft.CognitiveServices/accounts",
                status="✗",
                message=f"Failed to list: {result[:100]}"
            ))
            return

        accounts = result if isinstance(result, list) else []
        self.inventory["foundry_accounts"] = accounts

        foundry_accounts = [a for a in accounts if "fndry" in a.get("name", "").lower()]

        for account in foundry_accounts:
            account_name = account.get("name", "unknown")
            location = account.get("location", "unknown")
            kind = account.get("kind", "OpenAI")

            status = "✓"
            message = f"Kind: {kind}, SKU: {account.get('sku', {}).get('name', 'unknown')}"

            self.results.append(ResourceStatus(
                name=account_name,
                resource_type="Microsoft.CognitiveServices/accounts",
                status=status,
                location=location,
                message=message,
                details={
                    "kind": kind,
                    "sku": account.get("sku", {}).get("name", "unknown")
                }
            ))
            print(f"  {status} {account_name} ({location}) - {message}")

    def validate_container_registry(self):
        """Validate Container Registry."""
        print(f"\n{Colors.BOLD}📦 Validating Container Registry...{Colors.RESET}")

        success, result = self.run_az_command("acr list")
        if not success:
            self.results.append(ResourceStatus(
                name="Container Registry",
                resource_type="Microsoft.ContainerRegistry/registries",
                status="⚠",
                message="No registries found - needs creation for CI/CD"
            ))
            print(f"  ⚠ No Container Registry - Required for pipeline")
            return

        registries = result if isinstance(result, list) else []
        self.inventory["registries"] = registries

        if not registries:
            self.results.append(ResourceStatus(
                name="Container Registry",
                resource_type="Microsoft.ContainerRegistry/registries",
                status="⚠",
                message="No registries found - needs creation"
            ))
            print(f"  ⚠ No Container Registry deployed")
            return

        for registry in registries:
            reg_name = registry.get("name", "unknown")
            location = registry.get("location", "unknown")

            self.results.append(ResourceStatus(
                name=reg_name,
                resource_type="Microsoft.ContainerRegistry/registries",
                status="✓",
                location=location,
                message=f"SKU: {registry.get('sku', {}).get('name', 'unknown')}"
            ))
            print(f"  ✓ {reg_name} ({location})")

    def validate_container_apps(self):
        """Validate Container Apps."""
        print(f"\n{Colors.BOLD}🐳 Validating Container Apps...{Colors.RESET}")

        success, result = self.run_az_command("containerapp list")
        if not success:
            self.results.append(ResourceStatus(
                name="Container Apps",
                resource_type="Microsoft.App/containerApps",
                status="⚠",
                message="Not available or none deployed"
            ))
            print(f"  ⚠ No Container Apps deployed yet")
            return

        apps = result if isinstance(result, list) else []
        self.inventory["container_apps"] = apps

        if not apps:
            self.results.append(ResourceStatus(
                name="Container Apps",
                resource_type="Microsoft.App/containerApps",
                status="⚠",
                message="Ready for deployment - none deployed yet"
            ))
            print(f"  ⚠ No Container Apps deployed (ready for CI/CD)")
            return

        for app in apps:
            app_name = app.get("name", "unknown")
            location = app.get("location", "unknown")

            self.results.append(ResourceStatus(
                name=app_name,
                resource_type="Microsoft.App/containerApps",
                status="✓",
                location=location,
                message="Deployed and running"
            ))
            print(f"  ✓ {app_name} ({location})")

    def validate_function_apps(self):
        """Validate Function Apps."""
        print(f"\n{Colors.BOLD}⚡ Validating Function Apps...{Colors.RESET}")

        success, result = self.run_az_command("functionapp list")
        apps = result if success and isinstance(result, list) else []
        self.inventory["function_apps"] = apps

        if not apps:
            self.results.append(ResourceStatus(
                name="Function Apps",
                resource_type="Microsoft.Web/sites",
                status="⚠",
                message="No Function Apps deployed"
            ))
            print(f"  ⚠ No Function Apps deployed")
            return

        for app in apps:
            app_name = app.get("name", "unknown")
            location = app.get("location", "unknown")

            self.results.append(ResourceStatus(
                name=app_name,
                resource_type="Microsoft.Web/sites",
                status="✓",
                location=location,
                message="Deployed"
            ))
            print(f"  ✓ {app_name} ({location})")

    def validate_sql(self):
        """Validate SQL Database."""
        print(f"\n{Colors.BOLD}🗃️  Validating SQL Database...{Colors.RESET}")

        success, result = self.run_az_command("sql server list")
        servers = result if success and isinstance(result, list) else []
        self.inventory["sql_servers"] = servers

        if not servers:
            self.results.append(ResourceStatus(
                name="SQL Servers",
                resource_type="Microsoft.Sql/servers",
                status="⚠",
                message="No SQL servers deployed"
            ))
            print(f"  ⚠ No SQL servers deployed")
            return

        for server in servers:
            server_name = server.get("name", "unknown")
            location = server.get("location", "unknown")

            self.results.append(ResourceStatus(
                name=server_name,
                resource_type="Microsoft.Sql/servers",
                status="✓",
                location=location,
                message="Deployed"
            ))
            print(f"  ✓ {server_name} ({location})")

    def generate_report(self, output_file: Optional[str] = None):
        """Generate final report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "subscription": self.subscription,
            "validation_summary": {
                "total_resources": len(self.results),
                "healthy": sum(1 for r in self.results if r.status == "✓"),
                "warnings": sum(1 for r in self.results if r.status == "⚠"),
                "failures": sum(1 for r in self.results if r.status == "✗"),
            },
            "resources": [asdict(r) for r in self.results],
            "inventory": self.inventory
        }

        print(f"\n{Colors.BOLD}{'='*60}")
        print(f"📋 VALIDATION REPORT")
        print(f"{'='*60}{Colors.RESET}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"Subscription: {report['subscription']}")
        print(f"\n{Colors.BOLD}Summary:{Colors.RESET}")
        print(f"  Total Resources: {report['validation_summary']['total_resources']}")
        print(f"  {Colors.GREEN}Healthy: {report['validation_summary']['healthy']}{Colors.RESET}")
        print(f"  {Colors.YELLOW}Warnings: {report['validation_summary']['warnings']}{Colors.RESET}")
        print(f"  {Colors.RED}Failures: {report['validation_summary']['failures']}{Colors.RESET}")

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n✓ Report saved to: {output_file}")

        return report

    def run_all_validations(self):
        """Run all validation checks."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}🚀 Starting Azure Infrastructure Validation{Colors.RESET}")
        print(f"{Colors.BLUE}Subscription: {self.subscription}{Colors.RESET}\n")

        self.validate_key_vault()
        self.validate_cosmos_db()
        self.validate_foundry()
        self.validate_container_registry()
        self.validate_container_apps()
        self.validate_function_apps()
        self.validate_sql()

        return self.generate_report()

def main():
    parser = argparse.ArgumentParser(
        description="Azure Infrastructure Validator & Inventory Tool"
    )
    parser.add_argument(
        "--subscription",
        default="AASub1",
        help="Azure subscription name or ID (default: AASub1)"
    )
    parser.add_argument(
        "--output",
        help="Output report to JSON file"
    )

    args = parser.parse_args()

    validator = AzureValidator(subscription=args.subscription)
    report = validator.run_all_validations()

    if args.output:
        validator.generate_report(output_file=args.output)

    # Exit with error if any failures
    if report['validation_summary']['failures'] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
