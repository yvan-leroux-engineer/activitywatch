"""
Unit tests for client code structure (no external dependencies required)
These tests verify the code structure and configuration without importing the full client.
"""

import pytest
import os
import ast
import re


def test_client_config_has_new_fields():
    """Test that config.py includes the new fields."""
    config_path = os.path.join(
        os.path.dirname(__file__),
        '../../activitywatch/aw-client/aw_client/config.py'
    )
    
    if not os.path.exists(config_path):
        pytest.skip("config.py not found")
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Check for new configuration fields
    assert 'protocol' in content, "config should include 'protocol' field"
    assert 'api_key' in content, "config should include 'api_key' field"
    assert 'verify_ssl' in content, "config should include 'verify_ssl' field"
    
    # Check default values
    assert 'protocol = "http"' in content or 'protocol="http"' in content
    assert 'verify_ssl = true' in content or 'verify_ssl=true' in content


def test_client_code_has_session():
    """Test that client.py uses requests.Session."""
    client_path = os.path.join(
        os.path.dirname(__file__),
        '../../activitywatch/aw-client/aw_client/client.py'
    )
    
    if not os.path.exists(client_path):
        pytest.skip("client.py not found")
    
    with open(client_path, 'r') as f:
        content = f.read()
    
    # Check for session usage
    assert 'self.session' in content, "client should use self.session"
    assert 'req.Session()' in content or 'requests.Session()' in content, "client should create Session"
    assert 'session.get' in content or 'session.post' in content, "client should use session for requests"


def test_client_code_has_api_key_support():
    """Test that client.py supports API keys."""
    client_path = os.path.join(
        os.path.dirname(__file__),
        '../../activitywatch/aw-client/aw_client/client.py'
    )
    
    if not os.path.exists(client_path):
        pytest.skip("client.py not found")
    
    with open(client_path, 'r') as f:
        content = f.read()
    
    # Check for API key support
    assert 'api_key' in content, "client should support api_key parameter"
    assert 'X-API-Key' in content, "client should add X-API-Key header"


def test_client_code_has_https_support():
    """Test that client.py supports HTTPS."""
    client_path = os.path.join(
        os.path.dirname(__file__),
        '../../activitywatch/aw-client/aw_client/client.py'
    )
    
    if not os.path.exists(client_path):
        pytest.skip("client.py not found")
    
    with open(client_path, 'r') as f:
        content = f.read()
    
    # Check for HTTPS support
    assert 'protocol' in content, "client should support protocol parameter"
    assert 'verify_ssl' in content or 'verify' in content, "client should support SSL verification"
    assert 'https://' in content or 'protocol' in content, "client should handle HTTPS URLs"


def test_client_init_signature():
    """Test that ActivityWatchClient.__init__ has the new parameters."""
    client_path = os.path.join(
        os.path.dirname(__file__),
        '../../activitywatch/aw-client/aw_client/client.py'
    )
    
    if not os.path.exists(client_path):
        pytest.skip("client.py not found")
    
    with open(client_path, 'r') as f:
        content = f.read()
    
    # Check __init__ method signature
    # Look for the method definition
    init_match = re.search(r'def __init__\([^)]+\)', content)
    assert init_match is not None, "ActivityWatchClient should have __init__ method"
    
    init_signature = init_match.group(0)
    # Check for new parameters (they might be optional)
    assert 'protocol' in init_signature or 'protocol=None' in content, "Should have protocol parameter"
    assert 'api_key' in init_signature or 'api_key=None' in content, "Should have api_key parameter"
    assert 'verify_ssl' in init_signature or 'verify_ssl' in content, "Should have verify_ssl parameter"


