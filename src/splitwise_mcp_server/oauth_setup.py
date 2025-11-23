#!/usr/bin/env python3
"""
OAuth 2.0 Setup Helper for Splitwise MCP Server

This script guides users through the OAuth 2.0 authentication flow
to obtain an access token for the Splitwise API.
"""

import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlencode, parse_qs, urlparse

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install it with: pip install httpx")
    sys.exit(1)


def print_header():
    """Print welcome header."""
    print("=" * 70)
    print("Splitwise MCP Server - OAuth 2.0 Setup")
    print("=" * 70)
    print()


def print_step(step_num: int, title: str):
    """Print step header."""
    print(f"\n{'─' * 70}")
    print(f"Step {step_num}: {title}")
    print(f"{'─' * 70}\n")


def get_consumer_credentials() -> tuple[str, str]:
    """
    Prompt user for OAuth consumer key and secret.
    
    Returns:
        Tuple of (consumer_key, consumer_secret)
    """
    print_step(1, "Enter Your Application Credentials")
    
    print("If you haven't registered an application yet:")
    print("1. Go to: https://secure.splitwise.com/apps")
    print("2. Click 'Register your application'")
    print("3. Fill in the required details")
    print("4. Use 'http://localhost:8000/callback' as the callback URL")
    print()
    
    consumer_key = input("Enter your Consumer Key: ").strip()
    if not consumer_key:
        print("Error: Consumer Key is required")
        sys.exit(1)
    
    consumer_secret = input("Enter your Consumer Secret: ").strip()
    if not consumer_secret:
        print("Error: Consumer Secret is required")
        sys.exit(1)
    
    return consumer_key, consumer_secret


def generate_authorization_url(consumer_key: str, redirect_uri: str) -> str:
    """
    Generate the OAuth authorization URL.
    
    Args:
        consumer_key: OAuth consumer key
        redirect_uri: Callback URL
        
    Returns:
        Authorization URL
    """
    params = {
        "client_id": consumer_key,
        "response_type": "code",
        "redirect_uri": redirect_uri,
    }
    
    base_url = "https://secure.splitwise.com/oauth/authorize"
    return f"{base_url}?{urlencode(params)}"


def get_authorization_code(auth_url: str) -> str:
    """
    Get authorization code from user.
    
    Args:
        auth_url: Authorization URL to open
        
    Returns:
        Authorization code
    """
    print_step(2, "Authorize the Application")
    
    print("Opening your browser to authorize the application...")
    print(f"URL: {auth_url}")
    print()
    
    try:
        webbrowser.open(auth_url)
        print("✓ Browser opened")
    except Exception as e:
        print(f"⚠ Could not open browser automatically: {e}")
        print(f"Please manually open this URL in your browser:")
        print(f"{auth_url}")
    
    print()
    print("After authorizing, you'll be redirected to a URL like:")
    print("http://localhost:8000/callback?code=AUTHORIZATION_CODE&state=")
    print()
    print("Copy the ENTIRE redirect URL or just the 'code' parameter value.")
    print()
    
    user_input = input("Paste the redirect URL or authorization code: ").strip()
    
    # Try to parse as URL first
    if user_input.startswith("http"):
        try:
            parsed = urlparse(user_input)
            query_params = parse_qs(parsed.query)
            if "code" in query_params:
                code = query_params["code"][0]
                print(f"✓ Extracted authorization code from URL")
                return code
        except Exception:
            pass
    
    # Assume it's the code directly
    if user_input:
        return user_input
    
    print("Error: No authorization code provided")
    sys.exit(1)


def exchange_code_for_token(
    consumer_key: str,
    consumer_secret: str,
    code: str,
    redirect_uri: str
) -> str:
    """
    Exchange authorization code for access token.
    
    Args:
        consumer_key: OAuth consumer key
        consumer_secret: OAuth consumer secret
        code: Authorization code
        redirect_uri: Callback URL
        
    Returns:
        Access token
    """
    print_step(3, "Exchange Code for Access Token")
    
    print("Requesting access token from Splitwise...")
    
    token_url = "https://secure.splitwise.com/oauth/token"
    data = {
        "client_id": consumer_key,
        "client_secret": consumer_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    
    try:
        response = httpx.post(token_url, data=data, timeout=30.0)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            print("Error: No access token in response")
            print(f"Response: {token_data}")
            sys.exit(1)
        
        print("✓ Access token obtained successfully")
        return access_token
        
    except httpx.HTTPStatusError as e:
        print(f"Error: HTTP {e.response.status_code}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def save_to_env_file(
    consumer_key: str,
    consumer_secret: str,
    access_token: str,
    env_path: Path
):
    """
    Save credentials to .env file.
    
    Args:
        consumer_key: OAuth consumer key
        consumer_secret: OAuth consumer secret
        access_token: OAuth access token
        env_path: Path to .env file
    """
    print_step(4, "Save Credentials")
    
    # Read existing .env if it exists
    existing_lines = []
    if env_path.exists():
        with open(env_path, "r") as f:
            existing_lines = f.readlines()
    
    # Remove old Splitwise credentials
    filtered_lines = [
        line for line in existing_lines
        if not line.startswith("SPLITWISE_")
    ]
    
    # Add new credentials
    new_lines = filtered_lines + [
        "\n",
        "# Splitwise OAuth Credentials\n",
        f"SPLITWISE_OAUTH_CONSUMER_KEY={consumer_key}\n",
        f"SPLITWISE_OAUTH_CONSUMER_SECRET={consumer_secret}\n",
        f"SPLITWISE_OAUTH_ACCESS_TOKEN={access_token}\n",
    ]
    
    # Write to file
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    
    print(f"✓ Credentials saved to: {env_path}")


def verify_token(access_token: str) -> bool:
    """
    Verify the access token by making a test API call.
    
    Args:
        access_token: OAuth access token
        
    Returns:
        True if token is valid
    """
    print_step(5, "Verify Token")
    
    print("Testing access token with Splitwise API...")
    
    try:
        response = httpx.get(
            "https://secure.splitwise.com/api/v3.0/get_current_user",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0
        )
        response.raise_for_status()
        
        user_data = response.json()
        user = user_data.get("user", {})
        
        print("✓ Token is valid!")
        print(f"  Authenticated as: {user.get('first_name')} {user.get('last_name')}")
        print(f"  Email: {user.get('email')}")
        print(f"  User ID: {user.get('id')}")
        
        return True
        
    except httpx.HTTPStatusError as e:
        print(f"✗ Token verification failed: HTTP {e.response.status_code}")
        print(f"  Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"✗ Token verification failed: {e}")
        return False


def main():
    """Main setup flow."""
    print_header()
    
    # Default redirect URI
    redirect_uri = "http://localhost:8000/callback"
    
    # Step 1: Get consumer credentials
    consumer_key, consumer_secret = get_consumer_credentials()
    
    # Step 2: Generate authorization URL and get code
    auth_url = generate_authorization_url(consumer_key, redirect_uri)
    auth_code = get_authorization_code(auth_url)
    
    # Step 3: Exchange code for token
    access_token = exchange_code_for_token(
        consumer_key,
        consumer_secret,
        auth_code,
        redirect_uri
    )
    
    # Step 4: Save to .env file
    env_path = Path.cwd() / ".env"
    save_to_env_file(consumer_key, consumer_secret, access_token, env_path)
    
    # Step 5: Verify token
    verify_token(access_token)
    
    # Success message
    print()
    print("=" * 70)
    print("✓ OAuth Setup Complete!")
    print("=" * 70)
    print()
    print("Your Splitwise MCP Server is now configured and ready to use.")
    print()
    print("Next steps:")
    print("1. Add the server to your MCP client configuration")
    print("2. Restart your MCP client")
    print("3. Start using Splitwise tools!")
    print()
    print("See README.md for MCP configuration examples.")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)
