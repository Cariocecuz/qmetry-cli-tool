"""
Agent-Compatible Configuration Management

Supports both file-based config (for CLI) and parameter-based config (for agents).
Handles secure credential management for agent contexts.
"""

import os
from typing import Optional, Dict
from dataclasses import dataclass, field
from qmetry_tool.config_handler import QMetryConfig as BaseConfig


@dataclass
class AgentQMetryConfig:
    """
    Enhanced QMetry configuration for agent skills.
    
    Supports multiple initialization methods:
    1. From parameters (agent provides credentials)
    2. From environment variables
    3. From file (fallback to CLI behavior)
    """
    api_key: str = ""
    project: str = ""
    default_folder: str = "/Uncategorized"
    ssl_verify: bool = True
    
    # Cached data (in-memory for agents)
    folder_cache: Dict[str, int] = field(default_factory=dict)
    field_id_cache: Dict[str, str] = field(default_factory=dict)
    field_options_cache: Dict[str, Dict[str, int]] = field(default_factory=dict)
    
    # Cache metadata
    cache_timestamp: Optional[float] = None
    cache_ttl_seconds: int = 3600  # 1 hour default
    
    @classmethod
    def from_parameters(
        cls,
        api_key: str,
        project: str,
        default_folder: str = "/Uncategorized",
        ssl_verify: bool = True
    ) -> 'AgentQMetryConfig':
        """
        Create config from explicit parameters (agent-provided credentials).
        
        Example:
            config = AgentQMetryConfig.from_parameters(
                api_key="abc123...",
                project="12345"
            )
        """
        return cls(
            api_key=api_key,
            project=project,
            default_folder=default_folder,
            ssl_verify=ssl_verify
        )
    
    @classmethod
    def from_environment(cls) -> 'AgentQMetryConfig':
        """
        Create config from environment variables.
        
        Expected variables:
        - QMETRY_API_KEY
        - QMETRY_PROJECT
        - QMETRY_DEFAULT_FOLDER (optional)
        - QMETRY_SSL_VERIFY (optional)
        
        Example:
            export QMETRY_API_KEY="abc123..."
            export QMETRY_PROJECT="12345"
            config = AgentQMetryConfig.from_environment()
        """
        api_key = os.getenv('QMETRY_API_KEY', '')
        project = os.getenv('QMETRY_PROJECT', '')
        default_folder = os.getenv('QMETRY_DEFAULT_FOLDER', '/Uncategorized')
        ssl_verify = os.getenv('QMETRY_SSL_VERIFY', 'true').lower() == 'true'
        
        if not api_key or not project:
            raise ValueError(
                "Missing required environment variables: QMETRY_API_KEY and/or QMETRY_PROJECT"
            )
        
        return cls(
            api_key=api_key,
            project=project,
            default_folder=default_folder,
            ssl_verify=ssl_verify
        )
    
    @classmethod
    def from_file(cls, config_path: Optional[str] = None) -> 'AgentQMetryConfig':
        """
        Create config from YAML file (fallback to CLI behavior).
        
        Example:
            config = AgentQMetryConfig.from_file(".qmetry_config.yaml")
        """
        from qmetry_tool.config_handler import load_config
        
        base_config = load_config(config_path)
        
        return cls(
            api_key=base_config.api_key,
            project=base_config.project,
            default_folder=base_config.default_folder,
            ssl_verify=base_config.ssl_verify,
            folder_cache=base_config.folder_cache,
            field_id_cache=base_config.field_id_cache,
            field_options_cache=base_config.field_options_cache
        )
    
    @classmethod
    def auto_detect(
        cls,
        api_key: Optional[str] = None,
        project: Optional[str] = None,
        **kwargs
    ) -> 'AgentQMetryConfig':
        """
        Auto-detect configuration source with priority:
        1. Explicit parameters (if provided)
        2. Environment variables
        3. Config file
        
        Example:
            # Agent provides credentials
            config = AgentQMetryConfig.auto_detect(
                api_key="abc123...",
                project="12345"
            )
            
            # Or fallback to environment/file
            config = AgentQMetryConfig.auto_detect()
        """
        if api_key and project:
            return cls.from_parameters(api_key, project, **kwargs)
        
        try:
            return cls.from_environment()
        except ValueError:
            pass
        
        try:
            return cls.from_file()
        except FileNotFoundError:
            raise ValueError(
                "No QMetry configuration found. Provide api_key and project, "
                "set environment variables, or create .qmetry_config.yaml"
            )
    
    def to_base_config(self) -> BaseConfig:
        """Convert to base QMetryConfig for compatibility with existing code."""
        return BaseConfig(
            api_key=self.api_key,
            project=self.project,
            default_folder=self.default_folder,
            ssl_verify=self.ssl_verify,
            folder_cache=self.folder_cache,
            field_id_cache=self.field_id_cache,
            field_options_cache=self.field_options_cache
        )
    
    def is_cache_expired(self) -> bool:
        """Check if cache has expired based on TTL."""
        if self.cache_timestamp is None:
            return True
        
        import time
        return (time.time() - self.cache_timestamp) > self.cache_ttl_seconds
    
    def refresh_cache_timestamp(self):
        """Update cache timestamp to current time."""
        import time
        self.cache_timestamp = time.time()

