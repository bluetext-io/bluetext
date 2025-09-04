# Utility Helper Functions
# Common helper functions for your application

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from uuid import uuid4


def generate_uuid() -> str:
    """Generate a unique UUID string"""
    return str(uuid4())


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with salt.
    Note: In production, use bcrypt or similar for password hashing.
    """
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, pwd_hash = hashed.split('$')
        return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
    except ValueError:
        return False


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object to string"""
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse string to datetime object"""
    return datetime.strptime(date_str, format_str)


def get_current_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.utcnow()


def add_days(dt: datetime, days: int) -> datetime:
    """Add days to a datetime"""
    return dt + timedelta(days=days)


def clean_dict(data: Dict[str, Any], remove_none: bool = True, remove_empty: bool = False) -> Dict[str, Any]:
    """
    Clean dictionary by removing None values and/or empty values.
    
    Args:
        data: Dictionary to clean
        remove_none: Remove None values
        remove_empty: Remove empty strings, lists, dicts
        
    Returns:
        Cleaned dictionary
    """
    cleaned = {}
    for key, value in data.items():
        if remove_none and value is None:
            continue
        if remove_empty and value in ("", [], {}):
            continue
        cleaned[key] = value
    return cleaned


def paginate_list(items: list, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List to paginate
        page: Page number (1-based)
        page_size: Items per page
        
    Returns:
        Dictionary with pagination info and items
    """
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": end < total,
        "has_prev": page > 1
    }


def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string by stripping whitespace and limiting length.
    
    Args:
        text: String to sanitize
        max_length: Maximum length (truncates if longer)
        
    Returns:
        Sanitized string
    """
    sanitized = text.strip()
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def convert_keys_to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dictionary keys from snake_case to camelCase"""
    def to_camel_case(snake_str: str) -> str:
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    if isinstance(data, dict):
        return {to_camel_case(k): convert_keys_to_camel_case(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_camel_case(item) for item in data]
    else:
        return data


def convert_keys_to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dictionary keys from camelCase to snake_case"""
    def to_snake_case(camel_str: str) -> str:
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    if isinstance(data, dict):
        return {to_snake_case(k): convert_keys_to_snake_case(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_snake_case(item) for item in data]
    else:
        return data


def chunk_list(items: list, chunk_size: int) -> list:
    """Split list into chunks of specified size"""
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def build_where_clause(conditions: Dict[str, Any], table_prefix: str = "") -> tuple:
    """
    Build SQL WHERE clause from conditions dictionary.
    
    Args:
        conditions: Dictionary of column: value conditions
        table_prefix: Optional table prefix for columns
        
    Returns:
        Tuple of (where_clause, parameters)
    """
    if not conditions:
        return "", {}
    
    prefix = f"{table_prefix}." if table_prefix else ""
    clauses = []
    params = {}
    
    for i, (column, value) in enumerate(conditions.items()):
        param_key = f"param_{i}"
        clauses.append(f"{prefix}{column} = %({param_key})s")
        params[param_key] = value
    
    return " AND ".join(clauses), params


def build_update_clause(data: Dict[str, Any], table_prefix: str = "") -> tuple:
    """
    Build SQL UPDATE SET clause from data dictionary.
    
    Args:
        data: Dictionary of column: value updates
        table_prefix: Optional table prefix for columns
        
    Returns:
        Tuple of (set_clause, parameters)
    """
    if not data:
        return "", {}
    
    prefix = f"{table_prefix}." if table_prefix else ""
    clauses = []
    params = {}
    
    for i, (column, value) in enumerate(data.items()):
        param_key = f"update_param_{i}"
        clauses.append(f"{prefix}{column} = %({param_key})s")
        params[param_key] = value
    
    return ", ".join(clauses), params


# =============================================================================
# COUCHBASE HELPERS  
# =============================================================================

def build_n1ql_where_clause(conditions: Dict[str, Any], keyspace: str = "") -> tuple:
    """
    Build N1QL WHERE clause from conditions dictionary.
    
    Args:
        conditions: Dictionary of field: value conditions
        keyspace: Optional keyspace prefix
        
    Returns:
        Tuple of (where_clause, parameters)
    """
    if not conditions:
        return "", {}
    
    prefix = f"{keyspace}." if keyspace else ""
    clauses = []
    params = {}
    
    for field, value in conditions.items():
        param_key = f"${field}"
        clauses.append(f"{prefix}{field} = {param_key}")
        params[field] = value
    
    return " AND ".join(clauses), params


def format_couchbase_keyspace(bucket: str, scope: str = "_default", collection: str = "_default") -> str:
    """Format Couchbase keyspace string"""
    return f"`{bucket}`.`{scope}`.`{collection}`"


# =============================================================================
# USAGE EXAMPLES
# =============================================================================
"""
PASSWORD HASHING:
    hashed = hash_password("mypassword123")
    is_valid = verify_password("mypassword123", hashed)

PAGINATION:
    result = paginate_list(my_items, page=2, page_size=10)
    
DATETIME UTILITIES:
    now = get_current_timestamp()
    formatted = format_datetime(now)
    future = add_days(now, 30)

DICTIONARY CLEANING:
    cleaned = clean_dict({"a": 1, "b": None, "c": ""}, remove_none=True)
    
SQL BUILDING:
    where_clause, params = build_where_clause({"name": "John", "age": 25})
    # Result: "name = %(param_0)s AND age = %(param_1)s", {"param_0": "John", "param_1": 25}
"""