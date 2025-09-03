import os
from typing import Any, Callable

from pydantic import (
    BaseModel,
    ValidationError,
    create_model,
    validate_call,
)

from . import log

logger = log.get_logger(__name__)

#### Types ####

class EnvVarSpec(BaseModel):
    id: str
    type: Any = (str, ...)
    default: str = None
    parse: Callable[[str], Any] = None
    is_optional: bool = False
    is_secret: bool = False

class UnsetException(Exception):
    pass

class ValidationException(Exception):
    def __init__(self, message, value):
        super().__init__(message)
        self.value = value

class ParseException(Exception):
    def __init__(self, message, value):
        super().__init__(message)
        self.value = value

#### State ####

_is_validated: bool = False

#### API ####

def check(label, value, t):
    M = create_model(label, x=t)
    result = M(**{'x': value})
    return result

@validate_call
def parse(var: EnvVarSpec):
    value = os.environ.get(var.id, var.default)
    if value is not None:
        if parse := var.parse:
            try:
                value = parse(value)
            except Exception as e:
                raise ParseException(f"Failed to parse {var.id}: {str(e)}",
                                     value=value)
        try:
            check(var.id, value, var.type)
        except ValidationError as e:
            raise ValidationException(f"Failed to validate {var.id}: {str(e)}",
                                      value=value)
        return value
    else:
        if var.is_optional:
            return None
        else:
            if var.default:
                return var.default
            else:
                raise UnsetException(f"{var.id} is unset")

def validate(env_vars: list[EnvVarSpec]) -> bool:
    global _is_validated
    ok = True
    for var in env_vars:
        try:
            value = parse(var)
            if not _is_validated:
                logger.info(
                    "Env var %s is set to %s",
                    log.blue(var.id),
                    log.cyan('<REDACTED>') if var.is_secret else log.cyan(value),
                )
        except UnsetException:
            if not _is_validated:
                logger.error(f"Env var {log.blue(var.id)} is {log.red('unset')}")
            ok = False
        except ParseException as e:
            if not _is_validated:
                logger.error(
                    "Env var %s (set to %s) failed to parse:\n%s",
                    log.blue(var.id),
                    log.cyan('<REDACTED>') if var.is_secret else log.cyan(e.value),
                    log.red(str(e))
                )
            ok = False
        except ValidationException as e:
            if not _is_validated:
                logger.error(
                    "Env var %s (set to %s) is invalid:\n%s",
                    log.blue(var.id),
                    log.cyan('<REDACTED>') if var.is_secret else log.cyan(e.value),
                    log.red(str(e))
                )
            ok = False
    _is_validated = True
    return ok
