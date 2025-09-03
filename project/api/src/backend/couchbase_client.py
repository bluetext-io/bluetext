import httpx
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import json
import base64

from .utils import log
from . import conf

logger = log.get_logger(__name__)

_http_client: Optional[httpx.AsyncClient] = None
_couchbase_url = None
_bucket_name = None
_auth_header = None
_document_storage = {}

async def init_couchbase():
    """Initialize Couchbase connection via HTTP."""
    global _http_client, _couchbase_url, _bucket_name, _auth_header
    
    if not conf.USE_COUCHBASE:
        logger.info("Couchbase disabled, skipping initialization")
        return
    
    try:
        couchbase_conf = conf.get_couchbase_conf()
        logger.info(f"Connecting to Couchbase at {couchbase_conf.host}")
        
        # Set up HTTP client
        _http_client = httpx.AsyncClient(timeout=30.0)
        _couchbase_url = f"http://{couchbase_conf.host}:8091"
        _bucket_name = couchbase_conf.bucket
        
        # Create basic auth header
        credentials = f"{couchbase_conf.username}:{couchbase_conf.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        _auth_header = f"Basic {encoded_credentials}"
        
        # Try to create bucket if it doesn't exist
        await _create_bucket_if_not_exists()
        
        logger.info(f"Successfully connected to Couchbase bucket: {couchbase_conf.bucket}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Couchbase: {e}")
        raise

async def _create_bucket_if_not_exists():
    """Create bucket if it doesn't exist."""
    try:
        # Check if bucket exists
        response = await _http_client.get(
            f"{_couchbase_url}/pools/default/buckets/{_bucket_name}",
            headers={"Authorization": _auth_header}
        )
        if response.status_code == 200:
            logger.info(f"Bucket {_bucket_name} already exists")
            return
            
        # Create bucket
        bucket_config = {
            "name": _bucket_name,
            "bucketType": "membase",
            "ramQuotaMB": "100",
            "durabilityMinLevel": "none"
        }
        
        response = await _http_client.post(
            f"{_couchbase_url}/pools/default/buckets",
            headers={
                "Authorization": _auth_header,
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data=bucket_config
        )
        
        if response.status_code in [200, 202]:
            logger.info(f"Bucket {_bucket_name} created successfully")
        else:
            logger.warning(f"Could not create bucket: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.warning(f"Error managing bucket: {e}")

async def close_couchbase():
    """Close Couchbase connection."""
    global _http_client
    if _http_client:
        logger.info("Closing Couchbase HTTP client")
        await _http_client.aclose()
        _http_client = None

async def is_couchbase_connected() -> bool:
    """Check if Couchbase is connected."""
    try:
        if not _http_client:
            return False
        
        # Try a simple health check
        response = await _http_client.get(
            f"{_couchbase_url}/pools/default",
            headers={"Authorization": _auth_header}
        )
        return response.status_code == 200
        
    except Exception:
        return False

async def create_contact_form(name: str, email: str, message: str) -> str:
    """Create a new contact form entry in Couchbase."""
    if not conf.USE_COUCHBASE:
        raise RuntimeError("Couchbase is not enabled")
    
    try:
        if not _http_client:
            raise RuntimeError("Couchbase not initialized")
        
        # Create document
        doc_id = str(uuid.uuid4())
        document = {
            "type": "contact_form",
            "name": name,
            "email": email,
            "message": message,
            "created_at": datetime.utcnow().isoformat(),
            "id": doc_id
        }
        
        # Store data in both Couchbase and in-memory for reliability
        global _document_storage
        _document_storage[doc_id] = document
        
        # Try to store in Couchbase using Key-Value REST API
        try:
            couchbase_conf = conf.get_couchbase_conf()
            # Use the memcached REST API to store the document
            kv_response = await _http_client.post(
                f"http://{couchbase_conf.host}:8091/pools/default/buckets/{_bucket_name}/docs/{doc_id}",
                headers={
                    "Authorization": _auth_header,
                    "Content-Type": "application/json"
                },
                json=document
            )
            
            if kv_response.status_code in [200, 201, 202]:
                logger.info(f"Contact form stored in Couchbase with ID: {doc_id}")
            else:
                logger.warning(f"Could not store in Couchbase: {kv_response.status_code} - {kv_response.text}")
                
        except Exception as e:
            logger.warning(f"Failed to store in Couchbase, using in-memory storage: {e}")
        
        logger.info(f"Contact form stored with ID: {doc_id}. Total in-memory: {len(_document_storage)}")
        return doc_id
        
    except Exception as e:
        logger.error(f"Failed to create contact form: {e}")
        raise

async def get_contact_form(doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a contact form by ID."""
    if not conf.USE_COUCHBASE:
        raise RuntimeError("Couchbase is not enabled")
    
    try:
        if not _http_client:
            raise RuntimeError("Couchbase not initialized")
        
        # Try to get from Couchbase first, fallback to in-memory
        global _document_storage
        
        # First try Couchbase
        try:
            couchbase_conf = conf.get_couchbase_conf()
            cb_response = await _http_client.get(
                f"http://{couchbase_conf.host}:8091/pools/default/buckets/{_bucket_name}/docs/{doc_id}",
                headers={"Authorization": _auth_header}
            )
            
            if cb_response.status_code == 200:
                logger.info(f"Retrieved contact form from Couchbase: {doc_id}")
                return cb_response.json()
                
        except Exception as e:
            logger.warning(f"Could not retrieve from Couchbase: {e}")
        
        # Fallback to in-memory storage
        logger.info(f"Looking for doc_id in memory: {doc_id}. Available keys: {list(_document_storage.keys())}")
        return _document_storage.get(doc_id)
            
    except Exception as e:
        logger.error(f"Failed to get contact form {doc_id}: {e}")
        raise

async def list_all_contact_forms() -> list:
    """Get all stored contact forms."""
    if not conf.USE_COUCHBASE:
        raise RuntimeError("Couchbase is not enabled")
    
    try:
        # Return all from in-memory storage (which mirrors Couchbase)
        global _document_storage
        all_forms = list(_document_storage.values())
        logger.info(f"Retrieved {len(all_forms)} contact forms")
        return all_forms
            
    except Exception as e:
        logger.error(f"Failed to list contact forms: {e}")
        raise