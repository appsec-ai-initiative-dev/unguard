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

"""
MCP Client Service Package

This package provides connectivity to Dynatrace MCP (Model Context Protocol) servers
for enhanced observability and AI-driven insights.
"""

from .mcp_client import MCPClient, MCPMessage
from .routes import bp

__version__ = "0.1.0"
__all__ = ["MCPClient", "MCPMessage", "bp"]