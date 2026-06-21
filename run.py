"""Start the ScriptWeaver web application with ``python run.py``.

The API key, upstream base URL, and model are configured by
``scriptweaver.api.app`` through the canonical ``SCRIPTWEAVER_*`` variables.
This runner only controls the local listen port.
"""

import os

import uvicorn

from scriptweaver.api.app import app


PORT = int(os.getenv("SCRIPTWEAVER_PORT", "8000"))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
