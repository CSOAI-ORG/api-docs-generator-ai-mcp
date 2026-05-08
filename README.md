<div align="center">

# Api Docs Generator Ai MCP

**MCP server for api docs generator ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-api-docs-generator-ai-mcp)](https://pypi.org/project/meok-api-docs-generator-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Api Docs Generator Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `generate_endpoint` | Generate an OpenAPI endpoint definition from a description. |
| `generate_schema` | Generate an OpenAPI schema component. Fields format: 'name:type,name2:type2' (ty |
| `generate_full_spec` | Generate a complete OpenAPI 3.0 spec. Pass endpoints_json as a JSON array of {pa |
| `add_auth_to_spec` | Add authentication scheme to an OpenAPI spec. auth_type: bearer, api_key, basic, |
| `validate_spec` | Validate an OpenAPI spec for common issues. |

## Installation

```bash
pip install meok-api-docs-generator-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "api-docs-generator-ai-mcp": {
      "command": "python",
      "args": ["-m", "meok_api_docs_generator_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 5 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
