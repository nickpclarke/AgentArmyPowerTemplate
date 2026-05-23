#!/usr/bin/env python3
"""
Sync remote GCP MCP configurations to the Antigravity CLI configuration file
located at ~/.gemini/antigravity-cli/mcp_config.json.
"""

import os
import json
from pathlib import Path

def main():
    home = Path.home()
    config_dir = home / '.gemini' / 'antigravity-cli'
    config_file = config_dir / 'mcp_config.json'

    # Read existing configuration if it exists
    config_data = {"mcpServers": {}}
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read existing configuration: {e}. Starting fresh.")

    if "mcpServers" not in config_data:
        config_data["mcpServers"] = {}

    # Read GCP remote URLs from the environment
    servers = {
        "gcp-bigquery": os.environ.get("GCP_BIGQUERY_MCP_URL"),
        "gcp-storage": os.environ.get("GCP_STORAGE_MCP_URL"),
        "gcp-observability": os.environ.get("GCP_OBSERVABILITY_MCP_URL"),
    }

    region = os.environ.get("GCP_REGION", "us-central1")
    project_id = os.environ.get("GCP_PROJECT_ID")
    if project_id:
        servers["gcp-vertex-agents"] = f"https://{region}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{region}/agents/gcp-mcp-server:callMcp"

    # Merge remote server configurations
    updated = False
    for name, url in servers.items():
        if url:
            # Antigravity CLI uses 'serverUrl' field for remote endpoints
            config_data["mcpServers"][name] = {
                "serverUrl": url
            }
            updated = True

    if updated:
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            print(f"Successfully updated Antigravity MCP config at: {config_file}")
        except Exception as e:
            print(f"Error writing configuration to {config_file}: {e}")
    else:
        print("No remote GCP environment variables (GCP_BIGQUERY_MCP_URL, etc.) were found in the environment.")
        print("No updates were made to the Antigravity configuration.")

if __name__ == '__main__':
    main()
