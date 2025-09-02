from typing import List, Optional, Dict, Any
import time
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, QueryOptions
from couchbase.auth import PasswordAuthenticator
from couchbase.exceptions import DocumentNotFoundException

from ..utils import log

logger = log.get_logger(__name__)

class SchedulingClient:
    def __init__(
        self,
        url: str = None,
        username: str = None,
        password: str = None,
        bucket_name: str = None,
        scope: str = "_default",
        employees_coll: str = "employees",
        schedules_coll: str = "schedules",
        rules_coll: str = "rules"
    ):
        self.url = url
        self.username = username
        self.password = password
        self.bucket_name = bucket_name
        self.scope_name = scope
        self.employees_coll = employees_coll
        self.schedules_coll = schedules_coll
        self.rules_coll = rules_coll
        self.cluster = None
        self.bucket = None
        self.scope = None
        self.employees = None
        self.schedules = None
        self.rules = None
        self._is_query_service_ready = False

    def connect(self, max_retries: int = 30, initial_delay: float = 1.0, max_delay: float = 10.0) -> None:
        """
        Establish connection to Couchbase database.

        Args:
            max_retries: Maximum number of retry attempts.
            initial_delay: Initial delay between retries in seconds.
            max_delay: Maximum delay between retries in seconds.
        """
        auth = PasswordAuthenticator(self.username, self.password)
        options = ClusterOptions(auth)

        self.cluster = Cluster(self.url, options)
        delay = initial_delay
        connected = False

        for attempt in range(1, max_retries + 1):
            try:
                self.bucket = self.cluster.bucket(self.bucket_name)
                self.scope = self.bucket.scope(self.scope_name)
                connected = True
                logger.info(f"Connected to Couchbase database with bucket and scope on attempt {attempt}")
                break
            except Exception as bucket_err:
                logger.warning(f"Bucket or scope not ready yet (attempt {attempt}/{max_retries}): {str(bucket_err)}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    # Exponential backoff with a cap
                    delay = min(max_delay, delay * 1.5)
                else:
                    logger.error(f"Failed to connect after {max_retries} attempts")

        if connected:
            try:
                self.init()
            except Exception as col_err:
                logger.warning(f"Collections not ready yet: {str(col_err)}")

    def init(self, max_retries: int = 30, initial_delay: float = 1.0, max_delay: float = 10.0) -> None:
        """
        Create the collections if they don't exist.

        Args:
            max_retries: Maximum number of retry attempts.
            initial_delay: Initial delay between retries in seconds.
            max_delay: Maximum delay between retries in seconds.
        """
        # Add retry mechanism around cluster connection
        connection_delay = initial_delay
        connection_attempts = 0

        while not self.cluster and connection_attempts < max_retries:
            try:
                self.connect()
                logger.info("Successfully connected to cluster")
            except Exception as e:
                connection_attempts += 1
                logger.warning(f"Failed to connect to cluster (attempt {connection_attempts}/{max_retries}): {str(e)}")
                if connection_attempts < max_retries:
                    logger.info(f"Retrying connection in {connection_delay:.1f} seconds...")
                    time.sleep(connection_delay)
                    # Exponential backoff with a cap
                    connection_delay = min(max_delay, connection_delay * 1.5)
                else:
                    logger.error(f"Failed to connect to cluster after {max_retries} attempts")
                    raise

        delay = initial_delay

        for attempt in range(1, max_retries + 1):
            try:
                # Ensure we have bucket and scope
                if not self.bucket:
                    self.bucket = self.cluster.bucket(self.bucket_name)
                if not self.scope:
                    self.scope = self.bucket.scope(self.scope_name)

                collection_manager = self.bucket.collections()

                # Create collections if they don't exist
                for coll in [self.employees_coll, self.schedules_coll, self.rules_coll]:
                    try:
                        collection_manager.create_collection(self.scope_name, coll)
                        logger.info(f"Created collection: {coll}")
                    except Exception as e:
                        if "already exists" in str(e):
                            pass
                        else:
                            logger.warning(f"Error creating collection {coll}: {str(e)}")

                # Get collection references
                self.employees = self.scope.collection(self.employees_coll)
                self.schedules = self.scope.collection(self.schedules_coll)
                self.rules = self.scope.collection(self.rules_coll)

                # Initialize default rules if not exists
                self._init_default_rules()

                logger.info(f"Collections initialized successfully on attempt {attempt}")
                break

            except Exception as e:
                logger.warning(f"Error initializing collections (attempt {attempt}/{max_retries}): {str(e)}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                    # Exponential backoff with a cap
                    delay = min(max_delay, delay * 1.5)
                else:
                    logger.error(f"Failed to initialize collections after {max_retries} attempts")
                    raise

    def _init_default_rules(self) -> None:
        """Initialize default rules if they don't exist."""
        try:
            rules_key = "system_rules"
            existing_rules = self.rules.get(rules_key)
            if not existing_rules.value:
                default_rules = {
                    "max_days_per_week": 3,
                    "preferred_balance": 0.2
                }
                self.rules.upsert(rules_key, default_rules)
                logger.info("Initialized default scheduling rules")
        except Exception:
            # Rules don't exist, create them
            default_rules = {
                "max_days_per_week": 3,
                "preferred_balance": 0.2
            }
            self.rules.upsert("system_rules", default_rules)
            logger.info("Initialized default scheduling rules")

    def await_up(self, max_retries: int = 30, initial_delay: float = 1.0, max_delay: float = 10.0) -> None:
        """
        Wait until the Couchbase query service is available by running a simple query in a loop.

        Args:
            max_retries: Maximum number of retry attempts.
            initial_delay: Initial delay between retries in seconds.
            max_delay: Maximum delay between retries in seconds.
        """
        # If we already know the service is ready, skip the check
        if self._is_query_service_ready:
            return

        if not self.cluster:
            self.connect()

        delay = initial_delay
        for attempt in range(1, max_retries + 1):
            try:
                # Try a simple query that doesn't depend on any collections
                query = "SELECT 1"
                result = self.cluster.query(query)
                # Consume the result to ensure it completes
                list(result)

                # If we got here, the query service is ready
                self._is_query_service_ready = True
                logger.info("Couchbase query service is ready")
                return
            except Exception:
                logger.warning(
                    f"Attempt {attempt}/{max_retries}: Couchbase query service not available yet. "
                    f"Retrying in {delay:.1f} seconds..."
                )
                time.sleep(delay)
                # Exponential backoff with a cap
                delay = min(max_delay, delay * 1.5)

        # If we've exhausted all retries
        raise Exception(f"Couchbase query service not available after {max_retries} attempts")

    # Employee methods
    def create_employee(self, name: str, employee_number: str, known_absences: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new employee.

        Args:
            name: The name of the employee
            employee_number: The employee number (unique identifier)
            known_absences: Optional list of known absence dates in ISO format
            metadata: Optional metadata for the employee

        Returns:
            The employee number
        """
        if not self.employees:
            self.init()

        known_absences = known_absences or []
        doc = {
            "name": name,
            "employee_number": employee_number,
            "first_line_support_count": 0,
            "known_absences": known_absences,
            "metadata": metadata or {}
        }

        try:
            self.employees.upsert(employee_number, doc)
            logger.info(f"Created employee with number: {employee_number}")
            return employee_number
        except Exception:
            logger.exception("Failed to create employee")
            raise

    def get_employee(self, employee_number: str) -> Optional[Dict[str, Any]]:
        """
        Get an employee by employee number.

        Args:
            employee_number: The employee number

        Returns:
            The employee details or None if not found
        """
        if not self.employees:
            self.init()

        try:
            result = self.employees.get(employee_number)

            if not result or not hasattr(result, 'value') or not result.value:
                return None

            return result.value
        except DocumentNotFoundException:
            return None
        except Exception as e:
            logger.warning(f"Failed to get employee: {str(e)}")
            return None

    def get_employees(self) -> List[Dict[str, Any]]:
        """
        Get all employees.

        Returns:
            List of employees
        """
        if not self.employees:
            self.init()

        # Make sure the query service is available
        self.await_up()

        try:
            query = f"""
            SELECT e.*
            FROM {self.bucket_name}.{self.scope_name}.{self.employees_coll} e
            """

            result = self.cluster.query(query)
            return [row for row in result]
        except Exception:
            logger.exception("Failed to get employees.")
            raise

    def update_employee(self, employee_number: str, updates: Dict[str, Any]) -> bool:
        """
        Update an employee.

        Args:
            employee_number: The employee number
            updates: The fields to update

        Returns:
            True if the update was successful, False otherwise
        """
        if not self.employees:
            self.init()

        try:
            employee = self.get_employee(employee_number)
            if not employee:
                return False

            # Update employee fields
            for key, value in updates.items():
                employee[key] = value

            self.employees.upsert(employee_number, employee)
            logger.info(f"Updated employee {employee_number}")
            return True
        except Exception:
            logger.exception("Failed to update employee")
            return False

    def delete_employee(self, employee_number: str) -> bool:
        """
        Delete an employee.

        Args:
            employee_number: The employee number

        Returns:
            True if the employee was deleted, False otherwise
        """
        if not self.employees:
            self.init()

        try:
            employee = self.get_employee(employee_number)
            if not employee:
                return False

            self.employees.remove(employee_number)
            logger.info(f"Deleted employee {employee_number}")
            return True
        except Exception:
            logger.exception("Failed to delete employee")
            return False

    # Schedule methods
    def create_schedule(self, date_str: str, employee_number: str) -> str:
        """
        Create a schedule entry.

        Args:
            date_str: The date in ISO format (YYYY-MM-DD)
            employee_number: The employee number for first-line support

        Returns:
            The schedule ID (date string)
        """
        if not self.schedules:
            self.init()

        doc = {
            "date": date_str,
            "first_line_support": employee_number
        }

        try:
            self.schedules.upsert(date_str, doc)
            logger.info(f"Created schedule for date: {date_str}")

            # Update employee's first-line support count
            self._update_employee_counts()

            return date_str
        except Exception:
            logger.exception("Failed to create schedule")
            raise

    def get_schedule(self, date_str: str) -> Optional[Dict[str, Any]]:
        """
        Get a schedule by date.

        Args:
            date_str: The date in ISO format (YYYY-MM-DD)

        Returns:
            The schedule details or None if not found
        """
        if not self.schedules:
            self.init()

        try:
            result = self.schedules.get(date_str)

            if not result or not hasattr(result, 'value') or not result.value:
                return None

            return result.value
        except DocumentNotFoundException:
            return None
        except Exception as e:
            logger.warning(f"Failed to get schedule: {str(e)}")
            return None

    def get_schedules(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Get schedules within a date range.

        Args:
            start_date: Optional start date in ISO format (inclusive)
            end_date: Optional end date in ISO format (inclusive)

        Returns:
            List of schedules
        """
        if not self.schedules:
            self.init()

        # Make sure the query service is available
        self.await_up()

        try:
            where_clause = ""
            named_params = {}

            if start_date and end_date:
                where_clause = "WHERE s.date >= $start_date AND s.date <= $end_date"
                named_params = {"start_date": start_date, "end_date": end_date}
            elif start_date:
                where_clause = "WHERE s.date >= $start_date"
                named_params = {"start_date": start_date}
            elif end_date:
                where_clause = "WHERE s.date <= $end_date"
                named_params = {"end_date": end_date}

            query = f"""
            SELECT s.*
            FROM {self.bucket_name}.{self.scope_name}.{self.schedules_coll} s
            {where_clause}
            ORDER BY s.date ASC
            """

            options = QueryOptions(named_parameters=named_params) if named_params else None
            result = self.cluster.query(query, options)
            return [row for row in result]
        except Exception:
            logger.exception("Failed to get schedules.")
            raise

    def update_schedule(self, date_str: str, employee_number: str) -> bool:
        """
        Update a schedule entry.

        Args:
            date_str: The date in ISO format (YYYY-MM-DD)
            employee_number: The new employee number for first-line support

        Returns:
            True if the update was successful, False otherwise
        """
        if not self.schedules:
            self.init()

        try:
            schedule = self.get_schedule(date_str)
            if not schedule:
                return False

            schedule["first_line_support"] = employee_number
            self.schedules.upsert(date_str, schedule)
            logger.info(f"Updated schedule for date {date_str}")

            # Update employee counts
            self._update_employee_counts()

            return True
        except Exception:
            logger.exception("Failed to update schedule")
            return False

    def delete_schedule(self, date_str: str) -> bool:
        """
        Delete a schedule entry.

        Args:
            date_str: The date in ISO format (YYYY-MM-DD)

        Returns:
            True if the schedule was deleted, False otherwise
        """
        if not self.schedules:
            self.init()

        try:
            schedule = self.get_schedule(date_str)
            if not schedule:
                return False

            self.schedules.remove(date_str)
            logger.info(f"Deleted schedule for date {date_str}")

            # Update employee counts
            self._update_employee_counts()

            return True
        except Exception:
            logger.exception("Failed to delete schedule")
            return False

    def _update_employee_counts(self) -> None:
        """Update first-line support counts for all employees."""
        if not self.employees or not self.schedules:
            self.init()

        try:
            # Reset all counts
            employees = self.get_employees()
            for emp in employees:
                emp["first_line_support_count"] = 0
                self.employees.upsert(emp["employee_number"], emp)

            # Count schedules for each employee
            schedules = self.get_schedules()
            emp_counts = {}

            for schedule in schedules:
                emp_id = schedule["first_line_support"]
                emp_counts[emp_id] = emp_counts.get(emp_id, 0) + 1

            # Update employees with counts
            for emp_id, count in emp_counts.items():
                emp = self.get_employee(emp_id)
                if emp:
                    emp["first_line_support_count"] = count
                    self.employees.upsert(emp_id, emp)

            logger.info("Updated employee first-line support counts")
        except Exception:
            logger.exception("Failed to update employee counts")

    # Rules methods
    def get_rules(self) -> Dict[str, Any]:
        """
        Get the scheduling system rules.

        Returns:
            The rules
        """
        if not self.rules:
            self.init()

        try:
            result = self.rules.get("system_rules")
            if not result or not hasattr(result, 'value') or not result.value:
                # Initialize default rules if not found
                self._init_default_rules()
                result = self.rules.get("system_rules")

            return result.value
        except DocumentNotFoundException:
            # Initialize default rules without logging warning when document not found
            self._init_default_rules()
            try:
                result = self.rules.get("system_rules")
                return result.value
            except Exception:
                # Fallback to default rules
                return {
                    "max_days_per_week": 3,
                    "preferred_balance": 0.2
                }
        except Exception as e:
            logger.warning(f"Failed to get rules: {str(e)}")
            # Return default rules
            return {
                "max_days_per_week": 3,
                "preferred_balance": 0.2
            }

    def update_rules(self, updates: Dict[str, Any]) -> bool:
        """
        Update the scheduling system rules.

        Args:
            updates: The rule fields to update

        Returns:
            True if the update was successful, False otherwise
        """
        if not self.rules:
            self.init()

        try:
            current_rules = self.get_rules()

            # Update rule fields
            for key, value in updates.items():
                if value is not None:  # Only update provided fields
                    current_rules[key] = value

            self.rules.upsert("system_rules", current_rules)
            logger.info("Updated scheduling rules")
            return True
        except Exception:
            logger.exception("Failed to update rules")
            return False

    def close(self) -> None:
        """Close the database connection."""
        if self.cluster:
            self.cluster = None
            logger.info("Database connection closed")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
