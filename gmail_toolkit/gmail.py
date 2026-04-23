import os
import logging
import threading
from contextlib import contextmanager
from dotenv import load_dotenv
from langchain_google_community import GmailToolkit

logger = logging.getLogger(__name__)

# Load .env variables
load_dotenv()

# Absolute path to credentials.json (in same directory as this script)
GMAIL_TOOLKIT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(GMAIL_TOOLKIT_DIR, "credentials.json")

# Thread-safe context manager for chdir
_cwd_lock = threading.Lock()

@contextmanager
def _chdir(path):
    """Thread-safe context manager for temporarily changing working directory"""
    with _cwd_lock:
        prev = os.getcwd()
        try:
            os.chdir(path)
            yield
        finally:
            os.chdir(prev)

# Ensure Google SDK can see the credentials (use absolute path)
if os.path.exists(CREDS_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(CREDS_PATH)
else:
    logger.warning(f"Gmail credentials not found at {CREDS_PATH}")

# Initialize Gmail toolkit
gmail_tools = []
try:
    with _chdir(GMAIL_TOOLKIT_DIR):
        toolkit = GmailToolkit()
        gmail_tools = toolkit.get_tools()
except Exception as e:
    logger.error(f"Error initializing Gmail toolkit: {e}")

# Export tools individually for easy use
if gmail_tools:
    # Create a dictionary of tools for easy access
    tools_dict = {tool.name: tool for tool in gmail_tools}

    # Export commonly used tools
    send_email = next((t for t in gmail_tools if 'send' in t.name.lower()), None)
    get_message = next((t for t in gmail_tools if 'get_message' in t.name.lower()), None)
    create_draft = next((t for t in gmail_tools if 'create_draft' in t.name.lower()), None)
    search_messages = next((t for t in gmail_tools if 'search' in t.name.lower()), None)
else:
    send_email = None
    get_message = None
    create_draft = None
    search_messages = None


if __name__ == "__main__":
    # List available tools
    logging.basicConfig(level=logging.INFO)
    logger.info("=" * 60)
    logger.info("Gmail Toolkit - Available Tools")
    logger.info("=" * 60)
    for tool in gmail_tools:
        logger.info(f"\nTool: {tool.name}")
        logger.info(f"   Description: {tool.description}")
