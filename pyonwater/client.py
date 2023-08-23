"""EyeOnWater API integration."""
from __future__ import annotations

import datetime
import json
import logging
from typing import TYPE_CHECKING, Any
import urllib.parse

from dateutil import parser
import pytz
from tenacity import retry, retry_if_exception_type

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from .account import Account

from .exceptions import (
    EyeOnWaterAPIError,
    EyeOnWaterAuthError,
    EyeOnWaterAuthExpired,
    EyeOnWaterException,
    EyeOnWaterRateLimitError,
    EyeOnWaterResponseIsEmpty,
)

TOKEN_EXPIRATION = datetime.timedelta(minutes=15)
AUTH_ENDPOINT = "account/signin"

_LOGGER = logging.getLogger(__name__)


class Client:
    """Class represents client object."""

    def __init__(self, websession: ClientSession, account: Account) -> None:
        """Initialize the client."""
        self.base_url = "https://" + account.eow_hostname + "/"
        self.username = account.username
        self.password = account.password
        self.websession = websession
        self.cookies = None
        self.authenticated = False
        self.token_expiration = datetime.datetime.now()
        self.user_agent = None

    def _update_token_expiration(self):
        self.token_expiration = datetime.datetime.now() + TOKEN_EXPIRATION

    @retry(retry=retry_if_exception_type(EyeOnWaterAuthExpired))
    async def request(
        self,
        path: str,
        method: str,
        **kwargs,
    ):
        """Make API calls against the eow API."""
        await self.authenticate()
        resp = await self.websession.request(
            method,
            f"{self.base_url}{path}",
            cookies=self.cookies,
            **kwargs,
        )
        if resp.status == 403:
            _LOGGER.error("Reached ratelimit")
            msg = "Reached ratelimit"
            raise EyeOnWaterRateLimitError(msg)
        elif resp.status == 401:
            _LOGGER.debug("Authentication token expired; requesting new token")
            self.authenticated = False
            await self.authenticate()
            raise EyeOnWaterAuthExpired

        # Since API call did not return a 400 code, update the token_expiration.
        self._update_token_expiration()

        data = await resp.text()

        if resp.status != 200:
            _LOGGER.error(f"Request failed: {resp.status} {data}")
            msg = f"Request failed: {resp.status} {data}"
            raise EyeOnWaterException(msg)

        return data

    async def authenticate(self):
        """Authenticate the client."""
        if not self.token_valid:
            _LOGGER.debug("Requesting login token")

            resp = await self.websession.request(
                "POST",
                f"{self.base_url}{AUTH_ENDPOINT}",
                data={
                    "username": self.username,
                    "password": self.password,
                },
            )

            if "dashboard" not in str(resp.url):
                _LOGGER.warning("METER NOT FOUND!")
                msg = "No meter found"
                raise EyeOnWaterAuthError(msg)

            if resp.status == 400:
                msg = f"Username or password was not accepted by {self.base_url}"
                raise EyeOnWaterAuthError(msg)

            if resp.status == 403:
                msg = "Reached ratelimit"
                raise EyeOnWaterRateLimitError(msg)

            self.cookies = resp.cookies
            self._update_token_expiration()
            self.authenticated = True
            _LOGGER.debug("Successfully retrieved login token")

    def extract_json(self, line, prefix):
        """Extract JSON response."""
        line = line[line.find(prefix) + len(prefix) :]
        line = line[: line.find(";")]
        return json.loads(line)

    @property
    def token_valid(self):
        """Validate the token."""
        if self.authenticated or (datetime.datetime.now() < self.token_expiration):
            return True

        return False
