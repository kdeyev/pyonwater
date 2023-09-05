"""Exceptions of EOW Client."""


class EyeOnWaterException(Exception):
    """Base exception for more specific exceptions to inherit from."""


class EyeOnWaterAuthError(EyeOnWaterException):
    """Exception for authentication failures.

    Either wrong username or wrong password.
    """


class EyeOnWaterRateLimitError(EyeOnWaterException):
    """Exception for reaching the ratelimit.

    Either too many login attempts or too many requests.
    """


class EyeOnWaterAuthExpired(EyeOnWaterException):
    """Exception for when a token is no longer valid."""


class EyeOnWaterAPIError(EyeOnWaterException):
    """General exception for unknown API responses."""


class EyeOnWaterResponseIsEmpty(EyeOnWaterException):
    """API answered correct but there is not content to parse."""


class EyeOnWaterUnitError(EyeOnWaterException):
    """Exception for units related errors."""
