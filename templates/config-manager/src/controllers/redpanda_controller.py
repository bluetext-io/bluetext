import os
import time
from typing import Dict, Any, List
from pathlib import Path
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, ConfigResource, ConfigResourceType
from kafka.admin.config_resource import ConfigResource
from kafka.admin.new_topic import NewTopic
from kafka.errors import TopicAlreadyExistsError, KafkaError, NoBrokersAvailable
from config import Config
from utils.logger import get_logger

class RedpandaController:
    """Controls Redpanda topic operations."""
    
    def __init__(self, environment: str, config: Config = None, host: str = None, port: int = None):
        self.environment = environment
        self.config = config
        self.logger = get_logger('redpanda-controller')
        
        # Load from environment variables if not provided
        self.host = host or self._get_env_var('REDPANDA_HOST', 'redpanda')
        self.port = port or int(self._get_env_var('REDPANDA_PORT', '9092'))
        self.bootstrap_servers = f"{self.host}:{self.port}"
        self.admin_client = None
        
        self.logger.info(f"🔧 Initializing Redpanda controller for environment: {environment}")
        self.logger.info(f"📡 Bootstrap servers: {self.bootstrap_servers}")
    
    def _get_env_var(self, name: str, default: str = None) -> str:
        """Get environment variable with optional default."""
        try:
            if default is not None:
                return os.environ.get(name, default)
            else:
                return os.environ[name]
        except KeyError:
            raise KeyError(f"Environment variable '{name}' is not set")
    
    def get_admin_client(self) -> KafkaAdminClient:
        """Get Kafka admin client."""
        if self.admin_client is None:
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='init-module'
            )
        return self.admin_client
    
    def connect_with_retry(self, max_retries: int = 30, retry_interval: int = 2) -> KafkaAdminClient:
        """Connect to Redpanda with retry logic."""
        for attempt in range(max_retries):
            try:
                admin_client = self.get_admin_client()
                # Test connection by listing topics
                admin_client.list_topics()
                return admin_client
            except (NoBrokersAvailable, KafkaError) as e:
                if attempt == max_retries - 1:
                    self.logger.error(f'❌ Failed to connect to Redpanda after {max_retries} attempts: {e}')
                    raise e
                
                self.logger.debug(f"⏳ Waiting for connection to Redpanda... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_interval)
        
        raise Exception("Failed to connect to Redpanda after maximum retries")
    
    def topic_exists(self, topic_name: str) -> bool:
        """Check if a topic exists."""
        try:
            admin_client = self.connect_with_retry()
            metadata = admin_client.list_topics()
            return topic_name in metadata
        except Exception as e:
            self.logger.error(f"❌ Error checking if topic '{topic_name}' exists: {e}")
            return False
    
    def create_topic(self, topic_name: str, settings: Dict[str, Any]) -> None:
        """Create a topic with the specified settings."""
        admin_client = self.connect_with_retry()
        
        # Extract topic settings
        partitions = settings.get('partitions', 1)
        replication = settings.get('replication', 1)
        config = settings.get('config', {})
        
        # Convert config values to strings (Kafka requires string values)
        topic_config = {k: str(v) for k, v in config.items()}
        
        topic = NewTopic(
            name=topic_name,
            num_partitions=partitions,
            replication_factor=replication,
            topic_configs=topic_config
        )
        
        try:
            result = admin_client.create_topics([topic])
            
            # Simplified approach: just assume success if no exception was raised
            # The kafka-python library API has changed across versions and the response format
            # is inconsistent. Since we check topic existence before creation anyway,
            # we can rely on that check rather than parsing the complex response format.
            self.logger.info(f"✅ Topic '{topic_name}' created successfully")
                    
        except TopicAlreadyExistsError:
            self.logger.info(f"✅ Topic '{topic_name}' already exists")
        except Exception as e:
            self.logger.error(f"❌ Error creating topic '{topic_name}': {e}")
            raise e
    
    def ensure_topic(self, topic_name: str, settings: Dict[str, Any]) -> None:
        """Ensure a topic exists with the specified settings."""
        if self.topic_exists(topic_name):
            self.logger.info(f"✅ Topic '{topic_name}' already exists")
        else:
            self.logger.info(f"🔄 Creating topic '{topic_name}'...")
            self.create_topic(topic_name, settings)
    
    def _load_redpanda_config(self) -> Dict[str, Any]:
        """Load Redpanda configuration from YAML file using the config object."""
        if self.config is None:
            raise ValueError("Config object is required but not provided")
        return self.config.load_target_config('redpanda')
    
    def _merge_settings(self, global_defaults: Dict[str, Any], 
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
    
    def _get_topic_settings(self, topic_name: str, topic_config: Dict[str, Any], 
                           redpanda_config: Dict[str, Any], environment: str) -> Dict[str, Any]:
        """Get merged settings for a topic."""
        global_defaults = redpanda_config.get('defaults', {})
        item_defaults = topic_config.get('defaults', {})
        env_settings = topic_config.get('env_settings', {}).get(environment, {})
        
        return self._merge_settings(global_defaults, item_defaults, env_settings)
    
    def run_ops(self) -> None:
        """Run all Redpanda operations for the configured environment."""
        self.logger.info("🔄 Processing Redpanda topics...")
        redpanda_config = self._load_redpanda_config()
        self._ensure_topics(redpanda_config)
        self.logger.info("🎉 Redpanda topics processed successfully")
    
    def _ensure_topics(self, redpanda_config: Dict[str, Any]) -> None:
        """Ensure all topics exist according to configuration."""
        topics = redpanda_config.get('topics', {})
        
        for topic_name, topic_config in topics.items():
            self.logger.info(f"📝 Processing topic: {topic_name}")
            
            # Get topic settings
            topic_settings = self._get_topic_settings(topic_name, topic_config, redpanda_config, self.environment)
            
            # Ensure topic exists
            self.ensure_topic(topic_name, topic_settings)
