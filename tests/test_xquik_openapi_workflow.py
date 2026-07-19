import json

from server import add_auth_to_spec, generate_endpoint, generate_full_spec, validate_spec


API_KEY = "CSOAI-test"
SEARCH_SUMMARY = "Search tweets by query, Tweet ID, X status URL, or account date window"
USER_SUMMARY = "Get user profile with follower counts and verification"


def test_xquik_endpoint_generation_includes_path_parameters() -> None:
    result = generate_endpoint(
        "/api/v1/x/users/{id}",
        "GET",
        USER_SUMMARY,
        api_key=API_KEY,
    )

    assert result["method"] == "get"
    assert result["definition"]["summary"] == USER_SUMMARY
    assert result["definition"]["operationId"] == "api_v1_x_users_id_get"
    assert result["definition"]["parameters"] == [
        {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
    ]


def test_xquik_full_spec_workflow_preserves_auth_and_path_parameters() -> None:
    endpoints_json = json.dumps(
        [
            {
                "path": "/api/v1/x/tweets/search",
                "method": "get",
                "summary": SEARCH_SUMMARY,
            },
            {
                "path": "/api/v1/x/users/{id}",
                "method": "get",
                "summary": USER_SUMMARY,
            },
        ]
    )
    spec_result = generate_full_spec(
        "Xquik API",
        "Public REST API for X automation workflows.",
        "1.0",
        endpoints_json,
        api_key=API_KEY,
    )
    spec = spec_result["spec"]
    spec["servers"] = [{"url": "https://xquik.com"}]

    authenticated = add_auth_to_spec(json.dumps(spec), "api_key", api_key=API_KEY)["spec"]
    validation = validate_spec(json.dumps(authenticated), api_key=API_KEY)

    assert validation == {"valid": True, "errors": [], "warnings": []}
    assert authenticated["security"] == [{"api_key": []}]
    assert authenticated["components"]["securitySchemes"]["api_key"]["type"] == "apiKey"
    user_operation = authenticated["paths"]["/api/v1/x/users/{id}"]["get"]
    assert user_operation["parameters"] == [
        {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
    ]
