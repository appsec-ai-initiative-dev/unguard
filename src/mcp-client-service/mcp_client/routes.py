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

import logging
from flask import Flask, Blueprint, jsonify, request
from .mcp_client import MCPClient
import os


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask blueprint
bp = Blueprint('mcp_routes', __name__)

# Global MCP client instance
mcp_client = None


def get_mcp_client():
    """Get or create MCP client instance"""
    global mcp_client
    if mcp_client is None:
        server_url = os.environ.get('MCP_SERVER_URL', 'https://localhost/mcp')
        api_token = os.environ.get('MCP_API_TOKEN', 'demo-token')
        environment_id = os.environ.get('MCP_ENVIRONMENT_ID', 'demo-env')
        timeout = int(os.environ.get('MCP_CONNECTION_TIMEOUT', '30'))
        
        mcp_client = MCPClient(server_url, api_token, environment_id, timeout)
    
    return mcp_client


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with MCP connection status"""
    client = get_mcp_client()
    status = client.get_status()
    
    return jsonify({
        "status": "healthy",
        "service": "mcp-client-service",
        "mcp_connection": status
    })


@bp.route('/mcp/connect', methods=['POST'])
def connect_mcp():
    """Connect to MCP server"""
    try:
        client = get_mcp_client()
        
        success = client.connect()
        
        if success:
            return jsonify({
                "status": "connected",
                "message": "Successfully connected to Dynatrace MCP server"
            })
        else:
            return jsonify({
                "status": "failed",
                "message": "Failed to connect to MCP server"
            }), 500
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@bp.route('/mcp/disconnect', methods=['POST'])
def disconnect_mcp():
    """Disconnect from MCP server"""
    try:
        client = get_mcp_client()
        client.disconnect()
        
        return jsonify({
            "status": "disconnected",
            "message": "Disconnected from MCP server"
        })
        
    except Exception as e:
        logger.error(f"Disconnection error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@bp.route('/mcp/send-context', methods=['POST'])
def send_context():
    """Send application context to MCP server"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No context data provided"}), 400
        
        client = get_mcp_client()
        result = client.send_context(data)
        
        if result:
            return jsonify({
                "status": "sent",
                "result": result
            })
        else:
            return jsonify({
                "status": "failed",
                "message": "Failed to send context to MCP server"
            }), 500
            
    except Exception as e:
        logger.error(f"Send context error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@bp.route('/mcp/insights', methods=['GET'])
def get_insights():
    """Get AI insights from MCP server"""
    try:
        query = request.args.get('query', 'application performance')
        
        client = get_mcp_client()
        result = client.get_insights(query)
        
        if result:
            return jsonify({
                "status": "success",
                "insights": result
            })
        else:
            return jsonify({
                "status": "failed",
                "message": "Failed to get insights from MCP server"
            }), 500
            
    except Exception as e:
        logger.error(f"Get insights error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@bp.route('/mcp/status', methods=['GET'])
def get_status():
    """Get MCP connection status and metrics"""
    try:
        client = get_mcp_client()
        status = client.get_status()
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@bp.route('/mcp/ping', methods=['POST'])
def ping_mcp():
    """Ping MCP server to maintain connection"""
    try:
        client = get_mcp_client()
        success = client.ping()
        
        if success:
            return jsonify({
                "status": "pong",
                "message": "MCP server responded to ping"
            })
        else:
            return jsonify({
                "status": "failed",
                "message": "MCP server did not respond to ping"
            }), 500
            
    except Exception as e:
        logger.error(f"Ping error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500