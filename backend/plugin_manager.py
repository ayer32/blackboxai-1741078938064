from typing import Dict, List, Any, Optional, Type
import importlib
import os
import yaml
import json
import logging
from abc import ABC, abstractmethod
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
import asyncio
import aiohttp
from datetime import datetime

class PluginMetadata(BaseModel):
    """Plugin metadata model"""
    name: str
    version: str
    description: str
    author: str
    dependencies: Optional[List[str]] = []
    permissions: Optional[List[str]] = []
    config_schema: Optional[Dict[str, Any]] = {}

class PluginBase(ABC):
    """Base class for all plugins"""
    
    def __init__(self, metadata: PluginMetadata, config: Dict[str, Any]):
        self.metadata = metadata
        self.config = config
        self.router = APIRouter(prefix=f"/plugins/{metadata.name}")
        self.logger = logging.getLogger(f"plugin.{metadata.name}")
        self.setup_routes()

    @abstractmethod
    def setup_routes(self):
        """Set up plugin routes"""
        pass

    @abstractmethod
    async def initialize(self):
        """Initialize plugin"""
        pass

    @abstractmethod
    async def cleanup(self):
        """Cleanup plugin resources"""
        pass

    async def validate_dependencies(self) -> bool:
        """Validate plugin dependencies"""
        for dep in self.metadata.dependencies:
            if not await self.check_dependency(dep):
                return False
        return True

    async def check_dependency(self, dependency: str) -> bool:
        """Check if a dependency is available"""
        try:
            importlib.import_module(dependency)
            return True
        except ImportError:
            self.logger.error(f"Missing dependency: {dependency}")
            return False

class PluginManager:
    """Manages plugin lifecycle and integration"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.router = APIRouter(prefix="/plugins")
        self.setup_admin_routes()
        self.load_plugins()

    def setup_admin_routes(self):
        """Set up plugin management routes"""
        
        @self.router.get("/")
        async def list_plugins():
            """List all installed plugins"""
            return {
                name: {
                    "metadata": plugin.metadata.dict(),
                    "status": "active"
                }
                for name, plugin in self.plugins.items()
            }

        @self.router.post("/{plugin_name}/enable")
        async def enable_plugin(plugin_name: str):
            """Enable a plugin"""
            if plugin_name not in self.plugins:
                raise HTTPException(status_code=404, detail="Plugin not found")
            await self.enable_plugin(plugin_name)
            return {"status": "success"}

        @self.router.post("/{plugin_name}/disable")
        async def disable_plugin(plugin_name: str):
            """Disable a plugin"""
            if plugin_name not in self.plugins:
                raise HTTPException(status_code=404, detail="Plugin not found")
            await self.disable_plugin(plugin_name)
            return {"status": "success"}

        @self.router.post("/{plugin_name}/config")
        async def update_plugin_config(plugin_name: str, config: Dict[str, Any]):
            """Update plugin configuration"""
            if plugin_name not in self.plugins:
                raise HTTPException(status_code=404, detail="Plugin not found")
            await self.update_plugin_config(plugin_name, config)
            return {"status": "success"}

    def load_plugins(self):
        """Load all available plugins"""
        plugin_dir = "plugins"
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)

        for plugin_name in os.listdir(plugin_dir):
            plugin_path = os.path.join(plugin_dir, plugin_name)
            if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, "plugin.yaml")):
                try:
                    self.load_plugin(plugin_name, plugin_path)
                except Exception as e:
                    logging.error(f"Failed to load plugin {plugin_name}: {str(e)}")

    def load_plugin(self, plugin_name: str, plugin_path: str):
        """Load a specific plugin"""
        # Load plugin metadata
        with open(os.path.join(plugin_path, "plugin.yaml"), "r") as f:
            metadata = PluginMetadata(**yaml.safe_load(f))

        # Load plugin configuration
        config_path = os.path.join(plugin_path, "config.json")
        config = {}
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)

        # Import plugin module
        spec = importlib.util.spec_from_file_location(
            plugin_name,
            os.path.join(plugin_path, "main.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Initialize plugin
        plugin_class = getattr(module, f"{plugin_name.capitalize()}Plugin")
        plugin = plugin_class(metadata, config)
        self.plugins[plugin_name] = plugin

    async def initialize_plugins(self):
        """Initialize all plugins"""
        for plugin in self.plugins.values():
            try:
                if await plugin.validate_dependencies():
                    await plugin.initialize()
            except Exception as e:
                logging.error(f"Failed to initialize plugin {plugin.metadata.name}: {str(e)}")

    async def cleanup_plugins(self):
        """Cleanup all plugins"""
        for plugin in self.plugins.values():
            try:
                await plugin.cleanup()
            except Exception as e:
                logging.error(f"Failed to cleanup plugin {plugin.metadata.name}: {str(e)}")

    async def enable_plugin(self, plugin_name: str):
        """Enable a plugin"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not found")
        
        if await plugin.validate_dependencies():
            await plugin.initialize()
        else:
            raise ValueError(f"Plugin {plugin_name} dependencies not satisfied")

    async def disable_plugin(self, plugin_name: str):
        """Disable a plugin"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not found")
        
        await plugin.cleanup()

    async def update_plugin_config(self, plugin_name: str, config: Dict[str, Any]):
        """Update plugin configuration"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin {plugin_name} not found")
        
        # Validate config against schema
        try:
            if plugin.metadata.config_schema:
                # You might want to use a schema validation library here
                pass
            
            plugin.config.update(config)
            
            # Save config to file
            config_path = os.path.join("plugins", plugin_name, "config.json")
            with open(config_path, "w") as f:
                json.dump(plugin.config, f, indent=2)
                
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {str(e)}")

    def get_plugin_router(self, plugin_name: str) -> Optional[APIRouter]:
        """Get plugin router by name"""
        plugin = self.plugins.get(plugin_name)
        return plugin.router if plugin else None

    async def execute_plugin_hook(self, hook_name: str, *args, **kwargs):
        """Execute a hook across all plugins"""
        results = []
        for plugin in self.plugins.values():
            if hasattr(plugin, hook_name):
                try:
                    hook = getattr(plugin, hook_name)
                    result = await hook(*args, **kwargs)
                    results.append((plugin.metadata.name, result))
                except Exception as e:
                    logging.error(f"Plugin {plugin.metadata.name} hook {hook_name} failed: {str(e)}")
        return results

    def register_plugin_type(self, plugin_type: Type[PluginBase]):
        """Register a new plugin type"""
        plugin_types[plugin_type.__name__] = plugin_type

# Example plugin types
class AIPlugin(PluginBase):
    """Base class for AI-related plugins"""
    
    @abstractmethod
    async def process_text(self, text: str) -> str:
        """Process text input"""
        pass

    @abstractmethod
    async def generate_response(self, context: Dict[str, Any]) -> str:
        """Generate AI response"""
        pass

class AutomationPlugin(PluginBase):
    """Base class for automation plugins"""
    
    @abstractmethod
    async def execute_action(self, action: str, params: Dict[str, Any]) -> Any:
        """Execute automation action"""
        pass

    @abstractmethod
    async def get_available_actions(self) -> List[Dict[str, Any]]:
        """Get available automation actions"""
        pass

class IntegrationPlugin(PluginBase):
    """Base class for third-party service integrations"""
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the service"""
        pass

    @abstractmethod
    async def execute_operation(self, operation: str, params: Dict[str, Any]) -> Any:
        """Execute service operation"""
        pass

# Register plugin types
plugin_types = {
    'AIPlugin': AIPlugin,
    'AutomationPlugin': AutomationPlugin,
    'IntegrationPlugin': IntegrationPlugin
}
