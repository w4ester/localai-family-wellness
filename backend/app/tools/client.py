# ./backend/app/tools/client.py
"""
Asynchronous client logic for communicating with external tool microservices.

This module provides the `execute_tool` function which handles:
- Looking up tool details (URL, schemas) from the registry.
- Validating input arguments against required/optional parameters.
- Making HTTP POST requests to the appropriate tool server using httpx.
- Handling potential HTTP errors, timeouts, and connection issues.
- Applying a circuit breaker pattern for resilience.
- Returning the validated response from the tool server.
"""
import json
import logging
from typing import Any, Dict, Optional, List

import httpx
from circuitbreaker import circuit
from fastapi import HTTPException, status

# Import function to get tool details from the registry module
from .registry import get_tool_details

logger = logging.getLogger(__name__)

# --- Circuit Breaker Configuration ---
FAILURE_THRESHOLD: int = 5  # Number of consecutive failures before opening the circuit
RECOVERY_TIMEOUT: int = 30  # Seconds to wait before attempting requests again (half-open state)


# --- Tool Execution Function ---
@circuit(failure_threshold=FAILURE_THRESHOLD, recovery_timeout=RECOVERY_TIMEOUT, name="tool_execution_breaker")
async def execute_tool(tool_name: str, action: str, arguments: Dict[str, Any], timeout: int = 10) -> Dict[str, Any]:
    """
    Execute a specific tool action by making an asynchronous HTTP POST request
    to its dedicated tool server, wrapped in a circuit breaker.

    Args:
        tool_name: The unique name of the tool (e.g., "chore_tool")
        action: The specific action to execute (e.g., "get_chore_status")
        arguments: A dictionary containing the arguments for the action
        timeout: Request timeout in seconds (default: 10)

    Returns:
        A dictionary containing the JSON response from the tool server.

    Raises:
        HTTPException:
            - 404 Not Found: If the tool_name or action is not found in the registry.
            - 400 Bad Request: If required input arguments are missing.
            - 500 Internal Server Error: For unexpected errors during execution.
            - 502 Bad Gateway: If there's an error connecting to or communicating with the tool server.
            - 504 Gateway Timeout: If the request to the tool server times out.
            - Other status codes (>=400) as propagated from the tool server itself.
        circuitbreaker.CircuitBreakerError: If the circuit is open (raised by the decorator).
    """
    logger.debug(f"Attempting to execute tool: '{tool_name}' action: '{action}' with args: {arguments}")

    # 1. Get tool and action details from the registry
    action_details = get_tool_details(tool_name, action)
    if not action_details:
        logger.error(f"Tool '{tool_name}' action '{action}' not found in registry.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Tool '{tool_name}' action '{action}' not found"
        )

    server_url = action_details.get("server_url")
    if not server_url:
        logger.error(f"Missing 'server_url' in configuration for tool '{tool_name}'.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Configuration error for tool '{tool_name}'"
        )

    # 2. Validate arguments against required parameters
    required_params = action_details.get("required_params", [])
    missing_params = [param for param in required_params if param not in arguments]
    if missing_params:
        error_msg = f"Missing required arguments for '{tool_name}.{action}': {', '.join(missing_params)}"
        logger.error(error_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # 3. Filter out any arguments that aren't in required or optional params
    optional_params = action_details.get("optional_params", [])
    valid_params = required_params + optional_params
    filtered_arguments = {k: v for k, v in arguments.items() if k in valid_params}

    # 4. Construct the full URL
    # If server_url already ends with /execute, just append the action
    # Otherwise, construct the URL with /execute/action
    if server_url.endswith("/execute"):
        full_url = f"{server_url}/{action}"
    else:
        full_url = f"{server_url}/execute/{action}"

    # 5. Make HTTP request to the tool server using httpx.AsyncClient
    try:
        # Use AsyncClient context manager for proper connection handling
        async with httpx.AsyncClient() as client:
            logger.info(f"Executing tool '{tool_name}' action '{action}' -> POST {full_url}")
            
            # Wrap arguments in a consistent format expected by tool servers
            request_payload = {"params": filtered_arguments}
            
            response = await client.post(
                url=full_url,
                json=request_payload,  # Send arguments in the expected format
                timeout=timeout  # Apply request timeout
            )

            # Check if the tool server returned an error status code
            if response.status_code >= 400:
                error_detail = f"Tool server for '{tool_name}.{action}' returned error: {response.text}"
                logger.error(f"HTTP {response.status_code} from tool '{tool_name}.{action}': {response.text}")
                # Propagate the error status and detail from the tool server
                raise HTTPException(status_code=response.status_code, detail=error_detail)

            # Attempt to parse the JSON response
            result = response.json()
            logger.info(f"Tool '{tool_name}.{action}' executed successfully. Status: {response.status_code}")

            return result

    # Handle specific httpx exceptions
    except httpx.TimeoutException:
        logger.error(f"Timeout occurred while executing tool '{tool_name}.{action}' at {full_url}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, 
            detail=f"Tool '{tool_name}.{action}' execution timed out"
        )
    except httpx.RequestError as req_err:
        # Covers connection errors, DNS errors, etc.
        logger.error(f"Network request error executing tool '{tool_name}.{action}' at {full_url}: {req_err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, 
            detail=f"Could not communicate with tool '{tool_name}.{action}'"
        )
    # Handle potential JSON decoding errors
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON response from tool '{tool_name}.{action}' at {full_url}. Response text: {response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, 
            detail=f"Invalid response format from tool '{tool_name}.{action}'"
        )
    # Catch unexpected errors during execution
    except Exception as e:
        logger.error(f"Unexpected error during execution of tool '{tool_name}.{action}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unexpected error executing tool '{tool_name}.{action}'"
        )