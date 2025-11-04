import sys
import yaml
import httpx
import logging
import importlib
from typing import Callable
# local imports
from utils.utils import is_url, get_logger

logger = get_logger(__name__, logging.INFO)


def load_config(config_path: str) -> dict:
    """
    Load YAML configuration
    If the path is a URL, fetch the content from the URL.
    Otherwise, read from the local file system.

    param config_path: Path to the YAML configuration file or URL
    return: Parsed configuration as a dictionary

    error: Raises an exception if the file cannot be read or parsed
    """
    if is_url(config_path):
        try:
            response = httpx.get(config_path)
            response.raise_for_status()
            return yaml.safe_load(response.text)
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch configuration from URL {config_path}: {e}")
        except yaml.YAMLError as e:
            raise Exception(f"Failed to parse YAML from URL {config_path}: {e}")

    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise Exception(f"Configuration file not found on disk: {config_path}")
    except yaml.YAMLError as e:
        raise Exception(f"Failed to parse YAML file on disk {config_path}: {e}")


def load_plugins(plugins: list) -> dict[str, str | Callable]:
    """
    Dynamically load plugins by their names according to the configuration.
    param plugin_names: List of plugin names to load
    return: None
    """
    results: dict = {}
    for plugin in plugins:
        logger.debug(f"Loading plugin: {plugin}")
        try:
            module = importlib.import_module(f"plugins.{plugin.get("plugin", None)}")
            func = getattr(module, plugin.get("plugin", None))
            results[plugin.get("name")] = {"plugin": plugin.get("plugin", None),
                                           "config": plugin.get("config", None),
                                           "func": func}
        except (ModuleNotFoundError, AttributeError) as e:
            logger.error(f"Error loading plugin '{plugin}': {e}")
            sys.exit(1)
    return results


def get_function_with_config_by_name(plugins_runnables: dict, name: str) -> tuple[dict, Callable, str, str] | None:
    """
    Retrieve the function and its configuration by plugin name.
    param plugins_runnables: Dictionary of loaded plugins
    param name: Name of the plugin to retrieve
    return: Tuple of (configuration dictionary, function, plugin display name, plugin name), or None if not found
    """
    plugin = plugins_runnables.get(name) if plugins_runnables.get(name, None) else None
    if plugin:
        plugin_display_name = name
        plugin_name = plugin.get("plugin", None)
        config = plugin.get("config", None)
        func = plugin.get("func", None)
        logger.debug(f"Retrieved plugin '{plugin_display_name}' with config: {config}")
        return config, func, plugin_display_name, plugin_name
    else:
        logger.error(f"Plugin with name '{name}' not found. {plugins_runnables}")
    return None


def main(config_path: str):
    config = load_config(config_path)
    plugins = config.get("pipeline", [])
    steps = load_plugins([p for p in plugins])
    # Example of running a specific plugin
    # config, func, display_name, plugin_name = get_function_with_config_by_name(steps, "display name of the step")
    for step in steps:
        logger.info(f"### Current step: {step} ###")
        config, func, display_name, plugin_name = get_function_with_config_by_name(steps, step)
        logger.debug(f"Running plugin {display_name}:{plugin_name} with config: {config}")
        if func:
            func(display_name, config)


if __name__ == "__main__":
    main("config.yml")
