async def init(app: FastAPI) -> None:
    """Initialize all components during app startup."""
    # <integration-name>.init(app)
    pass


async def deinit(app: FastAPI) -> None:
    """Deinitialize all components during app shutdown."""
    # <integration-name>.deinit(app)
    pass

INTEGRATIONS_ENV_VARS = []
# INTEGRATIONS_ENV_VARS.extend(<integration-name>.ENV_VARS)

