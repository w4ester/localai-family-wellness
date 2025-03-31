# ./backend/app/tools/registry.py
"""
Tool registry for AI tools, loaded from a local JSON configuration file.

This module handles loading, validating, and providing access to the definitions
of external tools that the AI agents can use.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Global variable to store the loaded tools (internal use)
# Populated by load_tools_registry() during application startup.
_TOOLS_REGISTRY: Dict[str, Dict] = {}

# Define the path to the config file relative to this file's location
_TOOL_CONFIG_FILENAME = "tools_config.json"
_TOOL_CONFIG_PATH = Path(__file__).parent / _TOOL_CONFIG_FILENAME

logger = logging.getLogger(__name__)


def load_tools_registry() -> None:
    """
    Load and validate the tools registry from tools_config.json located
    in the same directory as this module. Populates the internal _TOOLS_REGISTRY.

    This should be called once during application startup (e.g., in main.py lifespan).
    """
    global _TOOLS_REGISTRY

    if not _TOOL_CONFIG_PATH.is_file():
        logger.warning(f"Tools config file not found at '{_TOOL_CONFIG_PATH}'. No tools will be loaded.")
        _TOOLS_REGISTRY = {}
        return

    logger.info(f"Loading tools registry from: '{_TOOL_CONFIG_PATH}'")
    try:
        with open(_TOOL_CONFIG_PATH, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        validated_tools = {}
        
        # Make sure loaded_data has a "tools" key and it's a list
        if not isinstance(loaded_data, dict) or "tools" not in loaded_data or not isinstance(loaded_data["tools"], list):
            logger.error(f"Tools config file content in '{_TOOL_CONFIG_PATH}' doesn't have the expected 'tools' array.")
            _TOOLS_REGISTRY = {}
            return
            
        # Iterate through tools in the JSON array
        for tool_config in loaded_data["tools"]:
            # Get the tool name
            tool_name = tool_config.get("name")
            if not tool_name:
                logger.warning(f"Tool config missing 'name' field. Skipping.")
                continue
                
            if validate_tool_config(tool_config):
                # Process actions into a more accessible format for client.py
                tool_data = {
                    "display_name": tool_config.get("display_name", tool_name),
                    "description": tool_config.get("description", ""),
                    "server_url": tool_config.get("server_url", ""),
                    "actions": {}
                }
                
                # Convert actions array into a dict for easier lookup
                for action in tool_config.get("actions", []):
                    action_name = action.get("name")
                    if action_name:
                        tool_data["actions"][action_name] = {
                            "description": action.get("description", ""),
                            "required_params": action.get("required_params", []),
                            "optional_params": action.get("optional_params", [])
                        }
                
                validated_tools[tool_name] = tool_data
                logger.debug(f"Validated tool: {tool_name} with {len(tool_data['actions'])} actions")
            else:
                logger.warning(f"Invalid tool configuration for '{tool_name}' in '{_TOOL_CONFIG_PATH}'. Skipping.")

        _TOOLS_REGISTRY = validated_tools
        logger.info(f"Successfully loaded and validated {len(_TOOLS_REGISTRY)} tools.")

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from tools config file '{_TOOL_CONFIG_PATH}': {e}")
        _TOOLS_REGISTRY = {}
    except Exception as e:
        logger.error(f"An unexpected error occurred loading tools registry from '{_TOOL_CONFIG_PATH}': {e}", exc_info=True)
        _TOOLS_REGISTRY = {}


def validate_tool_config(tool_config: Any) -> bool:
    """
    Validate a single tool's configuration dictionary for required fields.
    Returns True if valid, False otherwise.
    """
    if not isinstance(tool_config, dict):
        logger.warning(f"Tool configuration is not a dictionary.")
        return False

    # Define the fields required for the tool client to function
    # These match the format in your tools_config.json
    required_fields = ["name", "display_name", "description", "server_url", "actions"]
    has_error = False
    
    for field in required_fields:
        if field not in tool_config:
            logger.warning(f"Tool missing required configuration field '{field}'.")
            has_error = True
        # Basic type checks
        elif field == "description" and not isinstance(tool_config[field], str):
            logger.warning(f"Tool field 'description' must be a string.")
            has_error = True
        elif field == "display_name" and not isinstance(tool_config[field], str):
            logger.warning(f"Tool field 'display_name' must be a string.")
            has_error = True
        elif field == "server_url" and not isinstance(tool_config[field], str):
            logger.warning(f"Tool field 'server_url' must be a string.")
            has_error = True
        elif field == "actions" and not isinstance(tool_config[field], list):
            logger.warning(f"Tool field 'actions' must be an array.")
            has_error = True
    
    # Validate each action in the actions array
    if "actions" in tool_config and isinstance(tool_config["actions"], list):
        for i, action in enumerate(tool_config["actions"]):
            if not isinstance(action, dict):
                logger.warning(f"Action at index {i} is not a dictionary.")
                has_error = True
                continue
                
            if "name" not in action:
                logger.warning(f"Action at index {i} missing required 'name' field.")
                has_error = True
            
            if "description" in action and not isinstance(action["description"], str):
                logger.warning(f"Action '{action.get('name', f'at index {i}')}': Field 'description' must be a string.")
                has_error = True
                
            if "required_params" in action and not isinstance(action["required_params"], list):
                logger.warning(f"Action '{action.get('name', f'at index {i}')}': Field 'required_params' must be an array.")
                has_error = True
                
            if "optional_params" in action and not isinstance(action["optional_params"], list):
                logger.warning(f"Action '{action.get('name', f'at index {i}')}': Field 'optional_params' must be an array.")
                has_error = True

    return not has_error


def get_tool_definitions_for_llm() -> List[Dict]:
    """
    Get tool definitions formatted for use with LLM agent frameworks
    (like LangChain Function Calling or Instructor).
    
    Returns a list of tools with their actions formatted for the LLM.
    """
    tool_definitions = []
    
    for tool_name, tool_config in _TOOLS_REGISTRY.items():
        # Get all actions for this tool
        actions = tool_config.get("actions", {})
        
        for action_name, action_details in actions.items():
            # Format as function definition
            properties = {}
            required = []
            
            # Add required parameters
            for param in action_details.get("required_params", []):
                properties[param] = {"type": "string", "description": f"Required parameter: {param}"}
                required.append(param)
                
            # Add optional parameters
            for param in action_details.get("optional_params", []):
                properties[param] = {"type": "string", "description": f"Optional parameter: {param}"}
            
            # Create the function definition
            function_def = {
                "type": "function",
                "function": {
                    "name": action_name,
                    "description": action_details.get("description", "No description provided."),
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            }
            
            tool_definitions.append(function_def)
    
    return tool_definitions


def get_tool_details(tool_name: str, action_name: str = None) -> Optional[Dict]:
    """
    Get the configuration details for a specific tool by name.
    
    Args:
        tool_name: The name of the tool (e.g., "chore_tool")
        action_name: Optional name of the specific action (e.g., "get_chore_status")
        
    Returns:
        If action_name is provided:
            Details for the specific action including server_url
        Otherwise:
            Complete tool configuration
    """
    tool_config = _TOOLS_REGISTRY.get(tool_name)
    
    if not tool_config:
        logger.warning(f"Attempted to get details for non-existent tool: {tool_name}")
        return None
        
    if action_name:
        # Looking for a specific action
        action_details = tool_config.get("actions", {}).get(action_name)
        
        if not action_details:
            logger.warning(f"Action '{action_name}' not found for tool '{tool_name}'")
            return None
            
        # Return action details with the server_url from the parent tool
        return {
            "tool": tool_name,
            "action": action_name,
            "description": action_details.get("description", ""),
            "server_url": tool_config.get("server_url", ""),
            "required_params": action_details.get("required_params", []),
            "optional_params": action_details.get("optional_params", [])
        }
    
    # Return the full tool config
    logger.debug(f"Retrieved details for tool: {tool_name}")
    return tool_config