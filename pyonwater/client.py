"""EyeOnWater API integration."""

from __future__ import annotations

import datetime
import json
import logging
from typing import TYPE_CHECKING, Any

from aiohttp import ClientTimeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)
from yarl import URL

from .exceptions import (
    EyeOnWaterAPIError,
    EyeOnWaterAuthError,
    EyeOnWaterAuthExpired,
    EyeOnWaterRateLimitError,
)

if TYPE_CHECKING:  # pragma: no cover
    from aiohttp import ClientSession

    from .account import Account

TOKEN_EXPIRATION = datetime.timedelta(minutes=15)
AUTH_ENDPOINT = "account/signin"
MAX_LOG_PAYLOAD = 1000
DEFAULT_TIMEOUT = ClientTimeout(total=30, connect=10, sock_read=20)

_LOGGER = logging.getLogger(__name__)


class Client:
    """Class represents client object."""

    def __init__(
        self,
        websession: ClientSession,
        account: Account,
        *,
        timeout: ClientTimeout | None = None,
    ) -> None:
        """Initialize the client."""
        self.base_url = (
            "https://" + account.eow_hostname + "/" if account.eow_hostname else ""
        )
        self.username = account.username
        self.password = account.password
        self.websession = websession
        self.authenticated = False
        self.token_expiration = datetime.datetime.now()
        self.user_agent = None
        self.timeout = timeout or DEFAULT_TIMEOUT

    def _build_url(self, path: str) -> str:
        """Join base_url and path with exactly one separating slash.

        base_url carries a trailing slash while most endpoint constants carry a
        leading one, which produced URLs like ``https://host//api/...``.  The
        server tolerates that, but it should not be relied on.
        """
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _session_cookie_names(self, url: URL) -> list[str] | None:
        """Return the names of session cookies the jar holds for ``url``.

        Authentication state lives in the ``ClientSession`` cookie jar, not on
        this object: the session cookie is set on an intermediate redirect, so
        the final response carries no ``Set-Cookie`` at all and ``resp.cookies``
        is always empty (kdeyev/eyeonwater#180).

        Returns None when the session does not expose a jar, in which case no
        conclusion can be drawn either way.
        """
        jar = getattr(self.websession, "cookie_jar", None)
        if jar is None:
            # aiohttp's TestClient proxies requests and keeps the real session
            # (and therefore the jar) one level down.
            jar = getattr(getattr(self.websession, "session", None), "cookie_jar", None)
        if jar is None:
            return None
        return sorted(jar.filter_cookies(url).keys())

    def _truncate_payload(self, payload: str) -> str:
        if len(payload) <= MAX_LOG_PAYLOAD:
            return payload
        return f"{payload[:MAX_LOG_PAYLOAD]}..."

    def _update_token_expiration(self) -> None:
        self.token_expiration = datetime.datetime.now() + TOKEN_EXPIRATION

    @retry(  # type: ignore[misc]
        retry=retry_if_exception_type(
            (EyeOnWaterAuthExpired, EyeOnWaterRateLimitError),
        ),
        wait=wait_exponential_jitter(initial=1, max=20),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def request(
        self,
        path: str,
        method: str,
        **kwargs: Any,
    ) -> str:
        """Make API calls against the eow API."""
        await self.authenticate()
        _LOGGER.debug("%s %s", method.upper(), path)
        resp = await self.websession.request(
            method,
            self._build_url(path),
            timeout=self.timeout,
            **kwargs,
        )
        if resp.status == 403:
            _LOGGER.warning("Reached ratelimit")
            msg = "Reached ratelimit"
            raise EyeOnWaterRateLimitError(msg)
        elif resp.status == 401:
            _LOGGER.debug("Authentication token expired; requesting new token")
            self.authenticated = False
            await self.authenticate()
            raise EyeOnWaterAuthExpired

        self._update_token_expiration()

        data: str = await resp.text()

        # Log the real body size: resp.content_length is None for chunked
        # responses, which made large bodies look like "0 bytes" and hid the
        # fact that a login page was being returned (kdeyev/eyeonwater#180).
        _LOGGER.debug("Response: %s (%d bytes)", resp.status, len(data))

        if resp.status != 200:
            _LOGGER.error(
                "Request failed: %s %s",
                resp.status,
                self._truncate_payload(data),
            )
            msg = f"Request failed: {resp.status} {data}"
            raise EyeOnWaterAPIError(msg)

        return data

    async def authenticate(self) -> None:
        """Authenticate the client."""
        if not self.is_token_valid:
            _LOGGER.debug(
                "Token expired (authenticated=%s), re-authenticating",
                self.authenticated,
            )

            resp = await self.websession.request(
                "POST",
                self._build_url(AUTH_ENDPOINT),
                data={
                    "username": self.username,
                    "password": self.password,
                },
                timeout=self.timeout,
            )

            if resp.status == 400:
                msg = f"Username or password was not accepted by {self.base_url}"
                raise EyeOnWaterAuthError(msg)

            if resp.status == 403:
                msg = "Reached ratelimit"
                raise EyeOnWaterRateLimitError(msg)

            self._update_token_expiration()
            self.authenticated = True

            # Do not claim success outright: the sign-in endpoint answers 200
            # with the login page when credentials are not accepted, so the
            # final URL is the useful diagnostic (kdeyev/eyeonwater#180).
            session_cookies = self._session_cookie_names(resp.url)
            _LOGGER.debug(
                "Sign-in POST completed: status=%s, final_url=%s, session_cookies=%s",
                resp.status,
                resp.url,
                session_cookies if session_cookies is not None else "<unavailable>",
            )
            if session_cookies is not None and not session_cookies:
                # Not a signal about credentials - EOW issues a session cookie
                # even for anonymous visitors.  An empty jar means the caller
                # supplied a session that cannot store cookies, in which case
                # every subsequent request goes out unauthenticated.
                _LOGGER.warning(
                    "No session cookie was stored for %s. If the ClientSession "
                    "was created with a DummyCookieJar, requests will be "
                    "unauthenticated.",
                    self.base_url or "the configured host",
                )

    def extract_json(self, line: str, prefix: str) -> list[dict[str, Any]]:
        """Extract JSON response."""
        line = line[line.find(prefix) + len(prefix) :]
        line = line[: line.rfind(";")]
        return json.loads(line)  # type: ignore

    @property
    def is_token_valid(self) -> bool:
        """Validate the token."""
        if not self.authenticated:
            return False
        try:
            return datetime.datetime.now() < self.token_expiration
        except TypeError:
            # naive vs aware datetime comparison; treat as expired
            return False
