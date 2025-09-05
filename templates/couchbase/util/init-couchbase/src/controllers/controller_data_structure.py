from couchbase.management.collections import CreateCollectionSettings
from couchbase.exceptions import ScopeAlreadyExistsException, CollectionAlreadyExistsException

class ControllerDataStructure:
    def __init__(self, bucket):
        self.bucket = bucket

    def create_scope(self, collection_manager, scope_name):
        try:
            collection_manager.create_scope(scope_name)
            print(f"Scope '{scope_name}' created successfully.")
        except ScopeAlreadyExistsException:
            print(f"Scope '{scope_name}' already exists.")

    def create_collections(self, collection_manager, scope_name, collection_names):
        for collection_name in collection_names:
            try:
                collection_manager.create_collection(
                    scope_name,
                    collection_name,
                    CreateCollectionSettings()
                )
                print(f"Collection '{collection_name}' created successfully in scope '{scope_name}'.")
            except CollectionAlreadyExistsException:
                print(f"Collection '{collection_name}' already exists in scope '{scope_name}'.")

    def create(self, spec):
        collection_manager = self.bucket.collections()
        for scope_name, collection_names in spec.items():
            if scope_name != '_default':
                self.create_scope(collection_manager, scope_name)
            self.create_collections(collection_manager, scope_name, collection_names)

