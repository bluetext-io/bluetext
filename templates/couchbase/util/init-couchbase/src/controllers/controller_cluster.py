import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import timedelta
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, WaitUntilReadyOptions
from couchbase.exceptions import RequestCanceledException, AuthenticationException
from couchbase.diagnostics import ServiceType

class ControllerCluster:
    def __init__(self, host, username, password, tls, type):
        self.host = host
        self.username = username
        self.password = password
        self.tls = tls
        self.type = type

    def get_connection_string(self):
        protocol = "couchbases" if self.tls else "couchbase"
        return f"{protocol}://{self.host}"

    def params_cluster_init(self):
        protocol = "https" if self.tls else "http"
        port = "18091" if self.tls else "8091"
        return {
            'url': f"{protocol}://{self.host}:{port}/clusterInit",
            'data': {
                'username': self.username,
                'password': self.password,
                'services': 'kv,n1ql,index,fts,eventing',
                'hostname': '127.0.0.1',
                'memoryQuota': '256',
                'sendStats': 'false',
                'clusterName': 'cillers',
                'setDefaultMemQuotas': 'true',
                'indexerStorageMode': 'plasma',
                'port': 'SAME'
            }
        }

    def ensure_initialized(self):
        encoded_data = urllib.parse.urlencode(self.params_cluster_init()['data']).encode()
        request = urllib.request.Request(
            self.params_cluster_init()['url'],
            data=encoded_data,
            method='POST')
        max_retries = 100
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(request, timeout=10*60) as response:
                    response.read().decode()
                    print("Cluster initialization successful.")
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    print('Timeout: Waiting until cluster is started')
                    raise e
                error_message = str(e)
                if 'already initialized' in error_message or 'Unauthorized' in error_message:
                    print("Cluster already initialized.")
                    return
                print("Waiting until cluster is started ... ")
                time.sleep(1)
        assert False

    def connect(self):
        auth = PasswordAuthenticator(self.username, self.password)
        cluster_options = ClusterOptions(auth)
        if self.tls:
            cluster_options.verify_credentials = True
        cluster = Cluster(self.get_connection_string(), cluster_options)
        wait_options = WaitUntilReadyOptions(
                service_types=[ServiceType.KeyValue,
                               ServiceType.Query,
                               ServiceType.Management])
        cluster.wait_until_ready(timedelta(seconds=300), wait_options)
        return cluster

    def connect_with_retry(self, max_retries=30, retry_interval=1):
        for attempt in range(max_retries):
            try:
                return self.connect()
            except (RequestCanceledException, AuthenticationException) as e:
                if attempt == max_retries - 1:
                    if isinstance(e, RequestCanceledException):
                        print('Timeout: Connecting to cluster.')
                    elif isinstance(e, AuthenticationException):
                        print('Authentication failed: Cluster might not be fully initialized.')
                    raise e

                if isinstance(e, RequestCanceledException):
                    print("Waiting for connection to cluster ...")
                elif isinstance(e, AuthenticationException):
                    print("Waiting for cluster to initialize ...")

                time.sleep(retry_interval)
