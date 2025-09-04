import yaml
from pathlib import Path
from typing import Dict, Any
from utils.logger import get_logger

class Config:
    """Manages configuration loading and environment validation."""
    
    def __init__(self, config_file_path: Path, environment: str):
        self.config_file_path = config_file_path
        self.environment = environment
        self._main_config = None
        self._targets = None
        self.logger = get_logger('config')
    
    def load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load a YAML configuration file from the given path."""
        self.logger.debug(f"📄 Loading YAML file: {file_path}")
        
        # Check if the exact path exists first
        if file_path.exists():
            self.logger.info(f"✅ Found config file: {file_path}")
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f)
                self.logger.debug(f"📊 Loaded {len(config)} top-level keys from {file_path}")
                return config
        
        # If not found and path doesn't have an extension, try both .yaml and .yml
        if not file_path.suffix:
            yaml_path = file_path.with_suffix('.yaml')
            yml_path = file_path.with_suffix('.yml')
            
            if yaml_path.exists():
                self.logger.info(f"✅ Found config file: {yaml_path} (tried .yaml extension)")
                with open(yaml_path, 'r') as f:
                    return yaml.safe_load(f)
            elif yml_path.exists():
                self.logger.info(f"✅ Found config file: {yml_path} (tried .yml extension)")
                with open(yml_path, 'r') as f:
                    return yaml.safe_load(f)
        
        # If path has .yaml extension, also try .yml
        elif file_path.suffix == '.yaml':
            yml_path = file_path.with_suffix('.yml')
            if yml_path.exists():
                self.logger.info(f"✅ Found config file: {yml_path} (fallback from .yaml to .yml)")
                with open(yml_path, 'r') as f:
                    return yaml.safe_load(f)
        
        # If path has .yml extension, also try .yaml
        elif file_path.suffix == '.yml':
            yaml_path = file_path.with_suffix('.yaml')
            if yaml_path.exists():
                self.logger.info(f"✅ Found config file: {yaml_path} (fallback from .yml to .yaml)")
                with open(yaml_path, 'r') as f:
                    return yaml.safe_load(f)
        
        self.logger.error(f"❌ Configuration file not found: {file_path} (tried .yaml and .yml extensions)")
        raise FileNotFoundError(f"Configuration file not found: {file_path} (tried .yaml and .yml extensions)")
    
    def get_main_config(self) -> Dict[str, Any]:
        """Get main configuration from config.yaml."""
        if self._main_config is None:
            self._main_config = self.load_yaml(self.config_file_path)
        return self._main_config
    
    def get_targets(self) -> Dict[str, Path]:
        """Get available target config file paths by detecting existing files in conf/ directory."""
        if self._targets is None:
            # Always look in the conf/ directory in project root
            conf_dir = Path('conf')
            self._targets = {}
            
            # Check for couchbase config files
            couchbase_paths = [
                conf_dir / 'couchbase.yaml',
                conf_dir / 'couchbase.yml'
            ]
            for path in couchbase_paths:
                if path.exists():
                    self._targets['couchbase'] = path
                    break
            
            # Check for redpanda config files
            redpanda_paths = [
                conf_dir / 'redpanda.yaml',
                conf_dir / 'redpanda.yml'
            ]
            for path in redpanda_paths:
                if path.exists():
                    self._targets['redpanda'] = path
                    break
        
        return self._targets
    
    def load_target_config(self, target_id: str) -> Dict[str, Any]:
        """Load configuration for a specific service using configured paths."""
        self.logger.info(f"🎯 Loading target configuration: {target_id}")
        targets = self.get_targets()
        
        if target_id not in targets:
            self.logger.error(f"❌ No configured path found for target '{target_id}'")
            raise ValueError(f"No configured path found for target '{target_id}'")
        
        config_file_path = targets[target_id]
        self.logger.debug(f"📁 Target '{target_id}' config path: {config_file_path}")
        return self.load_yaml(config_file_path)
    
    def is_valid_environment(self, environment: str) -> bool:
        """Check if the environment is valid."""
        main_config = self.get_main_config()
        return environment in main_config.get('environments', [])
    
    def merge_settings(self, global_defaults: Dict[str, Any], 
                      item_defaults: Dict[str, Any], 
                      env_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Merge settings with precedence: env_settings > item_defaults > global_defaults."""
        result = {}
        
        # Start with global defaults
        if global_defaults:
            result.update(global_defaults)
        
        # Apply item defaults
        if item_defaults:
            result.update(item_defaults)
        
        # Apply environment-specific settings
        if env_settings:
            result.update(env_settings)
        
        return result
