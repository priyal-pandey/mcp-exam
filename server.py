
import os
import hashlib
from contextvars import ContextVar

from fastmcp import FastMCP

# Holds the challenge for the current HTTP request.
# It is not shared between simultaneous requests.
current_challenge = ContextVar("current_challenge", default=None)

mcp = FastMCP("Exam Challenge Server")


@mcp.tool()
def solve_challenge() -> str:
    """Solve the exam challenge from the HTTP request header."""
    challenge = current_challenge.get()

    if not challenge:
        raise ValueError("Missing X-Exam-Challenge header")

    email = "23f2005558@ds.study.iitm.ac.in".strip().lower()
    message = f"{challenge}:{email}"

    return hashlib.sha256(message.encode("utf-8")).hexdigest()[:16]


class ChallengeHeaderMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        challenge = headers.get(b"x-exam-challenge")
        challenge = challenge.decode("ascii") if challenge else None

        token = current_challenge.set(challenge)
        try:
            await self.app(scope, receive, send)
        finally:
            current_challenge.reset(token)


# Build the MCP HTTP endpoint.
mcp_app = mcp.http_app(stateless_http=True)
app = ChallengeHeaderMiddleware(mcp_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
