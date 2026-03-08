import os
import asyncio
import threading
from auth0_server_python.auth_server.server_client import ServerClient
from dotenv import load_dotenv
from flask import session
load_dotenv(override=True)

load_dotenv(override=True)

# Persistent background event loop for Auth0 coroutines
_shared_loop = asyncio.new_event_loop()
def _start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

_loop_thread = threading.Thread(target=_start_loop, args=(_shared_loop,), daemon=True)
_loop_thread.start()

def run_async(coro):
    """Helper to dispatch auth0 sdk calls to the persistent event loop"""
    return asyncio.run_coroutine_threadsafe(coro, _shared_loop).result()

class AttributeDict(dict):
    """A dictionary that allows attribute access to its keys. 
    This allows the Auth0 SDK to use both attribute access (obj.key) 
    and dictionary methods (obj.get('key')) interchangeably."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
    def __setattr__(self, name, value):
        self[name] = value

class FlaskSessionStore:
    """Store Auth0 transaction/state data in Flask's session cookie.
    This ensures data persists across Gunicorn workers since the session
    is serialized into a browser cookie, not held in process memory.
    Objects are converted to dicts for JSON serialization."""
    def __init__(self, prefix):
        self._prefix = prefix

    def _serialize(self, value):
        """Convert complex SDK objects to JSON-safe dicts."""
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {k: self._serialize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._serialize(v) for v in value]
        # For Pydantic models / dataclass-like objects
        if hasattr(value, '__dict__'):
            return {k: self._serialize(v) for k, v in vars(value).items()
                    if not k.startswith('_')}
        return str(value)

    def _deserialize(self, value):
        """Convert stored dicts back to AttributeDict for both attribute and dict-like access."""
        if value is None:
            return None
        if isinstance(value, dict):
            return AttributeDict({k: self._deserialize(v) for k, v in value.items()})
        if isinstance(value, (list, tuple)):
            return [self._deserialize(v) for v in value]
        return value

    async def get(self, key, options=None):
        data = session.get(f"{self._prefix}:{key}")
        return self._deserialize(data)

    async def set(self, key, value, options=None):
        session[f"{self._prefix}:{key}"] = self._serialize(value)

    async def delete(self, key, options=None):
        session.pop(f"{self._prefix}:{key}", None)

    async def delete_by_logout_token(self, claims, options=None):
        pass

state_store = FlaskSessionStore("auth0_state")
transaction_store = FlaskSessionStore("auth0_txn")

auth0 = ServerClient(
    domain=os.getenv('AUTH0_DOMAIN'),
    client_id=os.getenv('AUTH0_CLIENT_ID'),
    client_secret=os.getenv('AUTH0_CLIENT_SECRET'),
    secret=os.getenv('AUTH0_SECRET'),
    redirect_uri=os.getenv('AUTH0_REDIRECT_URI'),
    state_store=state_store,
    transaction_store=transaction_store,
    authorization_params={
        'scope': 'openid profile email',
        'audience': os.getenv('AUTH0_AUDIENCE', '')
    }
)