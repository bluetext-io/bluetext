#!/usr/bin/env python3

import json
import time
from pathlib import Path
from typing import Dict, Any, List
from couchbase.cluster import Cluster
from couchbase.exceptions import (
    DocumentExistsException,
    CouchbaseException
)
from controllers.couchbase_controller import CouchbaseController
from utils.logger import get_logger


class CouchbaseSeeder:
    """Handles seeding Couchbase collections with JSON data files."""

    def __init__(self, environment: str, couchbase_controller: CouchbaseController = None):
        self.environment = environment
        self.controller = couchbase_controller
        self.logger = get_logger('couchbase-seeder')

        if self.controller is None:
            self.logger.warning("No CouchbaseController provided, will create one")

    def _get_controller(self) -> CouchbaseController:
        """Get or create CouchbaseController instance."""
        if self.controller is None:
            self.controller = CouchbaseController(self.environment)
        return self.controller

    def _parse_filename(self, filename: str) -> Dict[str, str]:
        """
        Parse filename to extract bucket, scope, and collection.

        Expected format: bucket.scope.collection.json
        Example: main.api.users.json -> bucket=main, scope=api, collection=users

        Returns dict with 'bucket', 'scope', 'collection' keys, or None if invalid format.
        """
        # Remove .json extension
        if not filename.endswith('.json'):
            return None

        name_parts = filename[:-5].split('.')

        if len(name_parts) != 3:
            self.logger.warning(f"⚠️  Invalid filename format: {filename}")
            self.logger.warning(f"    Expected format: bucket.scope.collection.json")
            return None

        return {
            'bucket': name_parts[0],
            'scope': name_parts[1],
            'collection': name_parts[2]
        }

    def _load_seed_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Load seed data from JSON file.

        Expected format:
        [
            {"id": "doc1", "data": {...}},
            {"id": "doc2", "data": {...}}
        ]

        Or for a single document:
        {"id": "doc1", "data": {...}}
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Convert single document to list
        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            raise ValueError(f"Seed data must be a JSON array or object, got {type(data)}")

        return data

    def _validate_document(self, doc: Dict[str, Any], index: int) -> bool:
        """Validate that document has required 'id' field."""
        if 'id' not in doc:
            self.logger.error(f"  └─ ❌ Document at index {index} missing required 'id' field")
            return False
        return True

    def seed_collection(self, bucket_name: str, scope_name: str,
                       collection_name: str, documents: List[Dict[str, Any]],
                       upsert: bool = True) -> Dict[str, int]:
        """
        Seed a collection with documents.

        Args:
            bucket_name: Name of the bucket
            scope_name: Name of the scope
            collection_name: Name of the collection
            documents: List of documents to insert
            upsert: If True, update existing documents. If False, skip existing.

        Returns:
            Dict with 'inserted', 'updated', 'skipped', 'failed' counts
        """
        controller = self._get_controller()
        cluster = controller.connect_with_retry()

        # Get the collection
        bucket = cluster.bucket(bucket_name)
        scope = bucket.scope(scope_name)
        collection = scope.collection(collection_name)

        stats = {
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0
        }

        for idx, doc in enumerate(documents):
            if not self._validate_document(doc, idx):
                stats['failed'] += 1
                continue

            doc_id = doc['id']
            # Remove 'id' from the document data if present
            doc_data = {k: v for k, v in doc.items() if k != 'id'}

            try:
                if upsert:
                    # Upsert: insert or update
                    collection.upsert(doc_id, doc_data)
                    # We can't easily tell if this was insert or update without checking first
                    # So we'll count it as "updated" for simplicity
                    stats['updated'] += 1
                    self.logger.debug(f"  └─ ✅ Upserted document: {doc_id}")
                else:
                    # Insert only: skip if exists
                    collection.insert(doc_id, doc_data)
                    stats['inserted'] += 1
                    self.logger.debug(f"  └─ ✅ Inserted document: {doc_id}")

            except DocumentExistsException:
                stats['skipped'] += 1
                self.logger.debug(f"  └─ ⏭️  Skipped existing document: {doc_id}")

            except CouchbaseException as e:
                stats['failed'] += 1
                self.logger.error(f"  └─ ❌ Failed to seed document {doc_id}: {e}")

            except Exception as e:
                stats['failed'] += 1
                self.logger.error(f"  └─ ❌ Unexpected error seeding document {doc_id}: {e}")

        return stats

    def process_seed_file(self, seed_file: Path, upsert: bool = True) -> bool:
        """
        Process a single seed file.

        Args:
            seed_file: Path to the seed file
            upsert: If True, update existing documents. If False, skip existing.

        Returns:
            True if processing was successful, False otherwise
        """
        self.logger.info(f"🌱 Processing seed file: {seed_file.name}")

        # Parse filename
        target = self._parse_filename(seed_file.name)
        if target is None:
            return False

        bucket_name = target['bucket']
        scope_name = target['scope']
        collection_name = target['collection']

        self.logger.info(f"  └─ Target: {bucket_name}.{scope_name}.{collection_name}")

        try:
            # Load seed data
            documents = self._load_seed_data(seed_file)
            self.logger.info(f"  └─ Loaded {len(documents)} document(s)")

            # Seed the collection
            stats = self.seed_collection(
                bucket_name,
                scope_name,
                collection_name,
                documents,
                upsert=upsert
            )

            # Log stats
            total = sum(stats.values())
            self.logger.info(f"  └─ ✅ Seeding complete:")
            if stats['inserted'] > 0:
                self.logger.info(f"      ├─ Inserted: {stats['inserted']}")
            if stats['updated'] > 0:
                self.logger.info(f"      ├─ Updated: {stats['updated']}")
            if stats['skipped'] > 0:
                self.logger.info(f"      ├─ Skipped: {stats['skipped']}")
            if stats['failed'] > 0:
                self.logger.info(f"      └─ Failed: {stats['failed']}")

            return stats['failed'] == 0

        except Exception as e:
            self.logger.error(f"  └─ ❌ Error processing seed file: {e}")
            self.logger.exception("Stack trace:")
            return False

    def _is_example_file(self, filename: str) -> bool:
        """
        Check if a file is an example/template file that should be ignored.

        Patterns to ignore:
        - Files starting with "EXAMPLE"
        - Files starting with "_"
        - Files ending with ".example.json"
        """
        name = filename.upper()
        return (
            name.startswith('EXAMPLE') or
            name.startswith('_') or
            name.endswith('.EXAMPLE.JSON')
        )

    def process_seeds_directory(self, seeds_dir: Path = None, upsert: bool = True) -> Dict[str, int]:
        """
        Process all JSON seed files in the seeds directory.

        Args:
            seeds_dir: Path to seeds directory (defaults to conf/seeds)
            upsert: If True, update existing documents. If False, skip existing.

        Returns:
            Dict with 'processed', 'succeeded', 'failed' counts
        """
        if seeds_dir is None:
            seeds_dir = Path('conf/seeds')

        if not seeds_dir.exists():
            self.logger.debug("📦 No seeds directory found")
            return {'processed': 0, 'succeeded': 0, 'failed': 0}

        # Find all JSON files
        all_json_files = list(seeds_dir.glob('*.json'))

        if not all_json_files:
            self.logger.debug("📦 No JSON seed files found")
            return {'processed': 0, 'succeeded': 0, 'failed': 0}

        # Filter out example files
        json_files = [f for f in all_json_files if not self._is_example_file(f.name)]
        example_count = len(all_json_files) - len(json_files)

        self.logger.info(f"🌱 Found {len(json_files)} JSON seed file(s)")
        if example_count > 0:
            self.logger.info(f"📝 Ignored {example_count} example file(s)")

        if not json_files:
            return {'processed': 0, 'succeeded': 0, 'failed': 0}

        stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0
        }

        for json_file in json_files:
            stats['processed'] += 1
            success = self.process_seed_file(json_file, upsert=upsert)
            if success:
                stats['succeeded'] += 1
            else:
                stats['failed'] += 1

        self.logger.info(f"🌱 Seed processing summary: {stats['succeeded']}/{stats['processed']} succeeded")

        return stats
