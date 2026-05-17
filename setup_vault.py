#!/usr/bin/env python3
"""Run ONCE to create Gmail vault credentials."""

import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# 1. Create vault
vault = client.beta.vaults.create(name="gmail-vault")
print(f"Vault created: {vault.id}")

# 2. Add Gmail OAuth credential
client.beta.vaults.credentials.create(
    vault_id=vault.id,
    display_name="Gmail OAuth",
    auth={
        "type": "mcp_oauth",
        "mcp_server_url": "https://gmail.mcp.claude.com/mcp",
        "access_token": os.environ["GMAIL_ACCESS_TOKEN"],
        "expires_at": "2026-12-01T00:00:00Z",
        "refresh": {
            "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"],
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "token_endpoint": "https://oauth2.googleapis.com/token",
            "token_endpoint_auth": {
                "type": "client_secret_post",
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            },
        },
    },
)
print(f"\n Done! Add this to your .env:\nVAULT_ID={vault.id}")