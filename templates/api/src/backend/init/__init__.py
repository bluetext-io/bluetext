"""Centralized initialization and deinitialization for the API."""

from fastapi import FastAPI


async def init(app: FastAPI) -> None:
    """Initialize all components during app startup."""
    pass


async def deinit(app: FastAPI) -> None:
    """Deinitialize all components during app shutdown."""
    pass
