import os
import asyncio
import threading
from auth0_server_python.auth_server.server_client import ServerClient
from dotenv import load_dotenv
from flask import session

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

class MemoryStore:
    def __init__(self): self._data = {}
    async def get(self, key, options=None): return self._data.get(key)
    async def set(self, key, value, options=None): self._data[key] = value
    async def delete(self, key, options=None): self._data.pop(key, None)
    async def delete_by_logout_token(self, claims, options=None): pass

state_store = MemoryStore()
transaction_store = MemoryStore()

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