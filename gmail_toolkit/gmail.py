import os
from dotenv import load_dotenv
from langchain_google_community import GmailToolkit

# Load .env variables
load_dotenv()

# Absolute path to credentials.json (in same directory as this script)
GMAIL_TOOLKIT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(GMAIL_TOOLKIT_DIR, "credentials.json")

# Ensure Google SDK can see the credentials (use absolute path)
if os.path.exists(CREDS_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(CREDS_PATH)
else:
    # Fallback: check if running from different directory
    fallback_path = os.path.join(os.path.dirname(GMAIL_TOOLKIT_DIR), "gmail_toolkit", "credentials.json")
    if os.path.exists(fallback_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(fallback_path)

# Initialize Gmail toolkit
gmail_tools = []
try:
    # Change to gmail_toolkit directory to ensure credentials.json is found
    original_cwd = os.getcwd()
    os.chdir(GMAIL_TOOLKIT_DIR)

    toolkit = GmailToolkit()
    gmail_tools = toolkit.get_tools()

    os.chdir(original_cwd)
except Exception as e:
    print(f"Error initializing Gmail toolkit: {e}")
    try:
        os.chdir(original_cwd)
    except:
        pass

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
    print("=" * 60)
    print("Gmail Toolkit - Available Tools")
    print("=" * 60)
    for tool in gmail_tools:
        print(f"\nTool: {tool.name}")
        print(f"   Description: {tool.description}")
