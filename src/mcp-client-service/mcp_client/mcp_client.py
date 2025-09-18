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

import json
import time
import logging
from typing import Dict, Optional, Any
import requests
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class MCPMessage(BaseModel):
    """MCP protocol message structure"""
    id: str
    method: str
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class MCPClient:
    """Client for connecting to Dynatrace MCP servers"""
    
    def __init__(self, server_url: str, api_token: str, environment_id: str, timeout: int = 30):
        self.server_url = server_url
        self.api_token = api_token
        self.environment_id = environment_id
        self.timeout = timeout
        self.session = requests.Session()
        self.connected = False
        self.last_ping = None
        
        # Set up session headers
        self.session.headers.update({
            "Authorization": f"Api-Token {self.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "unguard-mcp-client/0.1.0"
        })
        
    def connect(self) -> bool:
        """Establish connection to MCP server"""
        try:
            # Check if the MCP endpoint is available via HTTP
            health_url = f"{self.server_url}/health"
            response = self.session.get(health_url, timeout=self.timeout)
            
            if response.status_code == 200:
                # Send initialization message
                init_data = {
                    "id": "init_1",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "1.0",
                        "clientInfo": {
                            "name": "unguard-mcp-client",
                            "version": "0.1.0"
                        },
                        "capabilities": {
                            "roots": {"listChanged": True},
                            "sampling": {}
                        }
                    }
                }
                
                init_url = f"{self.server_url}/initialize"
                init_response = self.session.post(init_url, json=init_data, timeout=self.timeout)
                
                if init_response.status_code in [200, 201]:
                    self.connected = True
                    self.last_ping = time.time()
                    logger.info("Successfully connected to Dynatrace MCP server")
                    return True
                else:
                    logger.warning(f"MCP initialization failed: {init_response.status_code}")
                    # Still consider connected if health check passed
                    self.connected = True
                    self.last_ping = time.time()
                    return True
            else:
                logger.error(f"MCP server health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MCP server: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from MCP server"""
        self.session.close()
        self.connected = False
        logger.info("Disconnected from MCP server")
    
    def send_context(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send application context to MCP server"""
        if not self.connected:
            logger.warning("Not connected to MCP server")
            return None
            
        try:
            message_data = {
                "id": f"context_{int(time.time())}",
                "method": "sendContext",
                "params": {
                    "environmentId": self.environment_id,
                    "timestamp": int(time.time() * 1000),
                    "context": context
                }
            }
            
            url = f"{self.server_url}/context"
            response = self.session.post(url, json=message_data, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json().get("result")
            else:
                logger.error(f"Failed to send context: {response.status_code}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send context: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending context: {e}")
            return None
    
    def get_insights(self, query: str) -> Optional[Dict[str, Any]]:
        """Get AI insights from MCP server"""
        if not self.connected:
            logger.warning("Not connected to MCP server")
            return None
            
        try:
            message_data = {
                "id": f"insights_{int(time.time())}",
                "method": "getInsights",
                "params": {
                    "environmentId": self.environment_id,
                    "query": query,
                    "timestamp": int(time.time() * 1000)
                }
            }
            
            url = f"{self.server_url}/insights"
            response = self.session.post(url, json=message_data, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json().get("result")
            else:
                logger.error(f"Failed to get insights: {response.status_code}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get insights: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting insights: {e}")
            return None
    
    def ping(self) -> bool:
        """Send ping to maintain connection"""
        if not self.connected:
            return False
            
        try:
            message_data = {
                "id": f"ping_{int(time.time())}",
                "method": "ping",
                "params": {"timestamp": int(time.time() * 1000)}
            }
            
            url = f"{self.server_url}/ping"
            response = self.session.post(url, json=message_data, timeout=self.timeout)
            
            if response.status_code == 200:
                self.last_ping = time.time()
                return True
            else:
                logger.error(f"Ping failed: {response.status_code}")
                self.connected = False
                return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ping failed: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error during ping: {e}")
            self.connected = False
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get connection status and metrics"""
        return {
            "connected": self.connected,
            "server_url": self.server_url,
            "environment_id": self.environment_id,
            "last_ping": self.last_ping,
            "uptime": time.time() - self.last_ping if self.last_ping else 0
        }