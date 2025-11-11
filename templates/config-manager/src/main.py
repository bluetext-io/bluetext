#!/usr/bin/env python3

import os
import sys
import yaml
import time
from pathlib import Path
from config import Config
from controllers.couchbase_controller import CouchbaseController
from controllers.redpanda_controller import RedpandaController
from couchbase_seeder import CouchbaseSeeder
from utils.logger import get_logger

def get_env_var(name, default=None):
    """Get environment variable with optional default."""
    try:
        if default is not None:
            return os.environ.get(name, default)
        else:
            return os.environ[name]
    except KeyError:
        raise KeyError(f"Environment variable '{name}' is not set")

def process_seed_files(environment, config, logger):
    """Process seed files from conf/seeds directory."""
    seeds_dir = Path('conf/seeds')

    if not seeds_dir.exists():
        logger.debug("📦 No seeds directory found, skipping seed processing")
        return 0

    # Find all yaml/yml files in seeds directory
    seed_files = list(seeds_dir.glob('*.yaml')) + list(seeds_dir.glob('*.yml'))

    if not seed_files:
        logger.debug("📦 No seed files found in conf/seeds")
        return 0

    logger.info(f"🌱 Found {len(seed_files)} seed file(s) in conf/seeds")

    processed_count = 0
    for seed_file in seed_files:
        logger.info(f"🌱 Processing seed file: {seed_file.name}")

        try:
            # Load the seed file
            with open(seed_file, 'r') as f:
                seed_config = yaml.safe_load(f)

            # Determine the type of seed file (couchbase or redpanda)
            # based on the content or filename
            if 'buckets' in seed_config:
                logger.info(f"  └─ Detected Couchbase seed configuration")
                couchbase_controller = CouchbaseController(environment, config)
                # Process the seed config directly
                couchbase_controller._ensure_resources(seed_config)
                processed_count += 1
                logger.info(f"  └─ ✅ Couchbase seed processed")
            elif 'topics' in seed_config:
                logger.info(f"  └─ Detected Redpanda seed configuration")
                redpanda_controller = RedpandaController(environment, config)
                redpanda_controller._ensure_resources(seed_config)
                processed_count += 1
                logger.info(f"  └─ ✅ Redpanda seed processed")
            else:
                logger.warning(f"  └─ ⚠️  Unknown seed format in {seed_file.name}")

        except Exception as e:
            logger.error(f"  └─ ❌ Error processing seed file {seed_file.name}: {e}")
            logger.exception("Stack trace:")

    logger.info(f"🌱 Processed {processed_count}/{len(seed_files)} seed files")
    return processed_count

def main():
    """Main entry point for the init module."""
    logger = get_logger('config-manager')

    logger.info("🚀 Starting config-manager...")

    try:
        # Get environment variables
        environment = get_env_var('ENVIRONMENT')
        logger.info(f"📊 Environment: {environment}")

        # Initialize config manager with hardcoded config path
        config_file_path = Path('conf/config.yaml')
        logger.info(f"📁 Config file path: {config_file_path}")

        config = Config(config_file_path, environment)

        # Validate environment
        if not config.is_valid_environment(environment):
            logger.error(f"❌ Invalid environment '{environment}' - not found in config file")
            sys.exit(1)

        logger.info(f"✅ Environment '{environment}' validated successfully")

        # Get available targets by detecting config files
        targets = config.get_targets()
        target_ids = list(targets.keys())

        if not target_ids:
            logger.warning("⚠️  No target config files found (couchbase.yaml/yml, redpanda.yaml/yml)")

        if target_ids:
            logger.info(f"🎯 Found {len(target_ids)} available target(s): {', '.join(target_ids)}")

        # Process each available target
        processed_count = 0

        if 'couchbase' in target_ids:
            logger.info("🔄 Processing Couchbase configuration...")
            couchbase_controller = CouchbaseController(environment, config)
            couchbase_controller.run_ops()
            processed_count += 1
            logger.info("✅ Couchbase processing completed")

        if 'redpanda' in target_ids:
            logger.info("🔄 Processing Redpanda configuration...")
            redpanda_controller = RedpandaController(environment, config)
            redpanda_controller.run_ops()
            processed_count += 1
            logger.info("✅ Redpanda processing completed")

        if target_ids:
            logger.info(f"🎉 Main configuration processed! Completed {processed_count}/{len(target_ids)} targets")

        # Process seed files (YAML configuration files)
        seed_count = process_seed_files(environment, config, logger)

        # Process JSON data seed files for Couchbase
        if 'couchbase' in target_ids or processed_count > 0:
            # Only run seeder if we have couchbase configured
            couchbase_controller = CouchbaseController(environment, config) if 'couchbase' in target_ids else None
            seeder = CouchbaseSeeder(environment, couchbase_controller)
            seeder_stats = seeder.process_seeds_directory(upsert=True)
            data_seed_count = seeder_stats['succeeded']
        else:
            logger.debug("📦 Skipping Couchbase data seeding (no Couchbase target configured)")
            data_seed_count = 0

        if seed_count == 0 and processed_count == 0 and data_seed_count == 0:
            logger.info("ℹ️  No configurations to process. Waiting for seed files in conf/seeds...")
        else:
            logger.info(f"🎉 All operations completed successfully!")

    except Exception as e:
        logger.error(f"💥 Fatal error in config-manager: {e}")
        logger.exception("Stack trace:")
        sys.exit(1)

if __name__ == "__main__":
    main()
