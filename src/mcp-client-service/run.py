#!/usr/bin/env python3

# Copyright 2024 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask
import os
import logging
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client.routes import bp


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure Flask application"""
    flask_app = Flask(__name__)
    
    # Register blueprints
    flask_app.register_blueprint(bp)
    
    return flask_app


def get_env_var(env_string, default=None):
    """Get environment variable with optional default"""
    value = os.environ.get(env_string, default)
    if value and value.isdigit():
        return int(value)
    return value


if __name__ == '__main__':
    app = create_app()
    
    port = get_env_var('SERVER_PORT', 8090)
    host = get_env_var('SERVER_HOST', '0.0.0.0')
    debug = get_env_var('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting MCP Client Service on {host}:{port}")
    logger.info(f"MCP Server URL: {os.environ.get('MCP_SERVER_URL', 'Not configured')}")
    logger.info(f"Environment ID: {os.environ.get('MCP_ENVIRONMENT_ID', 'Not configured')}")
    
    app.run(host=host, port=port, debug=debug)