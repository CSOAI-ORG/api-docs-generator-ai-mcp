#!/usr/bin/env python3
"""api-docs-generator-ai-mcp - Generate OpenAPI specs from descriptions."""

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json
import time
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "api-docs-generator-ai-mcp",
    instructions="Generate OpenAPI/Swagger specifications from natural language API descriptions. Supports REST endpoint generation, schema creation, and full spec assembly.",
)

# Rate limiting
_calls: list[float] = []
DAILY_LIMIT = 50


def _check_rate() -> bool:
    now = time.time()
    _calls[:] = [t for t in _calls if now - t < 86400]
    if len(_calls) >= DAILY_LIMIT:
        return False
    _calls.append(now)
    return True


@mcp.tool()
def generate_endpoint(
    path: str, method: str, summary: str, request_body: Optional[str] = None, response_description: str = "Successful response"
, api_key: str = "") -> dict:
    """Generate an OpenAPI endpoint definition from a description."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if not _check_rate():
        return {"error": "Rate limit exceeded (50/day)"}
    method = method.lower()
    if method not in ("get", "post", "put", "patch", "delete", "head", "options"):
        return {"error": f"Invalid HTTP method: {method}"}
    endpoint: dict = {
        "summary": summary,
        "operationId": path.strip("/").replace("/", "_").replace("{", "").replace("}", "") + f"_{method}",
        "responses": {
            "200": {
                "description": response_description,
                "content": {"application/json": {"schema": {"type": "object"}}},
            },
            "400": {"description": "Bad request"},
            "500": {"description": "Internal server error"},
        },
    }
    if request_body and method in ("post", "put", "patch"):
        fields = [f.strip() for f in request_body.split(",")]
        properties = {}
        for field in fields:
            parts = field.split(":")
            fname = parts[0].strip()
            ftype = parts[1].strip() if len(parts) > 1 else "string"
            properties[fname] = {"type": ftype}
        endpoint["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {"type": "object", "properties": properties, "required": list(properties.keys())},
                }
            },
        }
    params = []
    import re
    for match in re.finditer(r"\{(\w+)\}", path):
        params.append({"name": match.group(1), "in": "path", "required": True, "schema": {"type": "string"}})
    if params:
        endpoint["parameters"] = params
    return {"path": path, "method": method, "definition": endpoint}


@mcp.tool()
def generate_schema(name: str, fields: str, api_key: str = "") -> dict:
    """Generate an OpenAPI schema component. Fields format: 'name:type,name2:type2' (types: string,integer,number,boolean,array)."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if not _check_rate():
        return {"error": "Rate limit exceeded (50/day)"}
    properties = {}
    required = []
    for field in fields.split(","):
        parts = field.strip().split(":")
        fname = parts[0].strip()
        ftype = parts[1].strip() if len(parts) > 1 else "string"
        if not fname:
            continue
        if ftype == "array":
            properties[fname] = {"type": "array", "items": {"type": "string"}}
        else:
            properties[fname] = {"type": ftype}
        required.append(fname)
    schema = {"type": "object", "properties": properties, "required": required}
    return {"schema_name": name, "schema": schema}


@mcp.tool()
def generate_full_spec(
    title: str, description: str, version: str = "1.0.0", endpoints_json: str = "[]"
, api_key: str = "") -> dict:
    """Generate a complete OpenAPI 3.0 spec. Pass endpoints_json as a JSON array of {path, method, summary} objects."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if not _check_rate():
        return {"error": "Rate limit exceeded (50/day)"}
    try:
        endpoints = json.loads(endpoints_json)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON for endpoints_json"}
    paths: dict = {}
    for ep in endpoints:
        p = ep.get("path", "/")
        m = ep.get("method", "get").lower()
        s = ep.get("summary", "")
        if p not in paths:
            paths[p] = {}
        paths[p][m] = {
            "summary": s,
            "operationId": p.strip("/").replace("/", "_") + f"_{m}",
            "responses": {"200": {"description": "Success", "content": {"application/json": {"schema": {"type": "object"}}}}},
        }
    spec = {
        "openapi": "3.0.3",
        "info": {"title": title, "description": description, "version": version},
        "paths": paths,
        "components": {"schemas": {}},
    }
    return {"spec": spec}


@mcp.tool()
def add_auth_to_spec(spec_json: str, auth_type: str = "bearer", api_key: str = "") -> dict:
    """Add authentication scheme to an OpenAPI spec. auth_type: bearer, api_key, basic, oauth2."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if not _check_rate():
        return {"error": "Rate limit exceeded (50/day)"}
    try:
        spec = json.loads(spec_json)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON for spec"}
    schemes = {
        "bearer": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        "api_key": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
        "basic": {"type": "http", "scheme": "basic"},
        "oauth2": {
            "type": "oauth2",
            "flows": {"authorizationCode": {"authorizationUrl": "https://example.com/oauth/authorize", "tokenUrl": "https://example.com/oauth/token", "scopes": {"read": "Read access", "write": "Write access"}}},
        },
    }
    if auth_type not in schemes:
        return {"error": f"Unknown auth type: {auth_type}. Use: bearer, api_key, basic, oauth2"}
    if "components" not in spec:
        spec["components"] = {}
    spec["components"]["securitySchemes"] = {auth_type: schemes[auth_type]}
    spec["security"] = [{auth_type: []}]
    return {"spec": spec}


@mcp.tool()
def validate_spec(spec_json: str, api_key: str = "") -> dict:
    """Validate an OpenAPI spec for common issues."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    if not _check_rate():
        return {"error": "Rate limit exceeded (50/day)"}
    try:
        spec = json.loads(spec_json)
    except json.JSONDecodeError:
        return {"valid": False, "errors": ["Invalid JSON"]}
    errors = []
    warnings = []
    if "openapi" not in spec:
        errors.append("Missing 'openapi' version field")
    if "info" not in spec:
        errors.append("Missing 'info' object")
    else:
        if "title" not in spec["info"]:
            errors.append("Missing 'info.title'")
        if "version" not in spec["info"]:
            errors.append("Missing 'info.version'")
    if "paths" not in spec:
        errors.append("Missing 'paths' object")
    else:
        for path, methods in spec["paths"].items():
            if not path.startswith("/"):
                errors.append(f"Path '{path}' must start with /")
            for method, definition in methods.items():
                if method not in ("get", "post", "put", "patch", "delete", "head", "options", "trace"):
                    errors.append(f"Invalid method '{method}' on {path}")
                if "responses" not in definition:
                    warnings.append(f"{method.upper()} {path} has no responses defined")
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
