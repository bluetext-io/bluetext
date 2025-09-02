import time
from couchbase.management.buckets import CreateBucketSettings, BucketType
from couchbase.exceptions import BucketDoesNotExistException

class ControllerBucket:
    def __init__(self, controller_cluster, cluster):
        self.controller_cluster = controller_cluster
        self.cluster = cluster

    def ensure_created(self, bucket_name, ram_quota_mb=100):
        bucket_manager = self.cluster.buckets()

        try:
            bucket_manager.get_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' already exists.")
        except BucketDoesNotExistException:
            if self.controller_cluster.type == "capella":
                raise Exception(f"No bucket '{bucket_name}' exists in Capella cluster. When using  bucket must be created manually using the Capella UI.")
            try:
                bucket_manager.create_bucket(
                    CreateBucketSettings(
                        name=bucket_name,
                        bucket_type=BucketType.COUCHBASE,
                        ram_quota_mb=ram_quota_mb
                    )
                )
                print(f"Bucket '{bucket_name}' created successfully.")
            except Exception as e:
                raise Exception(f"Failed to create bucket '{bucket_name}': {e}")
        return self.wait_for_bucket_ready(bucket_name)

    def wait_for_bucket_ready(self, bucket_name, max_retries=30, retry_interval=1):
        for attempt in range(max_retries):
            try:
                bucket = self.cluster.bucket(bucket_name)
                bucket.ping()
                print(f"Bucket '{bucket_name}' is ready.")
                return bucket
            except Exception as e:
                if attempt == max_retries - 1:
                    print("Timeout: waiting until bucket ready.")
                    raise e
                print(f"Waiting until bucket '{bucket_name}' is ready")
                time.sleep(retry_interval)
