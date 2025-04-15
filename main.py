from mcp.server.fastmcp import FastMCP
import os
import asyncio
import httpx
from pydantic import BaseModel, Field
from typing import Any, Dict

# Create an MCP server
mcp = FastMCP("AI Sticky Notes")

NOTES_FILE = os.path.join(os.path.dirname(__file__), "notes.txt")

def ensure_file():
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w") as f:
            f.write("")

@mcp.tool()
def add_note(message: str) -> str:
    """
    Append a new note to the sticky note file.
    """
    ensure_file()
    with open(NOTES_FILE, "a") as f:
        f.write(message + "\n")
    return "Note saved!"

@mcp.tool()
def read_notes() -> str:
    """
    Read and return all notes from the sticky note file.
    """
    ensure_file()
    with open(NOTES_FILE, "r") as f:
        content = f.read().strip()
    return content or "No notes yet."

@mcp.resource("notes://latest")
def get_latest_note() -> str:
    """
    Get the most recently added note from the sticky note file.
    """
    ensure_file()
    with open(NOTES_FILE, "r") as f:
        lines = f.readlines()
    return lines[-1].strip() if lines else "No notes yet."

@mcp.prompt()
def note_summary_prompt() -> str:
    """
    Generate a prompt asking the AI to summarize all current notes.
    """
    ensure_file()
    with open(NOTES_FILE, "r") as f:
        content = f.read().strip()
    if not content:
        return "There are no notes yet."
    return f"Summarize the current notes: {content}"


# -------------------------------
# New: Profile API Integration
# -------------------------------

# 🔐 Bearer Token for API Authorization
BEARER_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyNTEyIiwianRpIjoiODg4MzAyNjkt"
    "Y2MxNy00YmFiLTgyNmItOWZjMWI0Y2VmZTQxIiwiaXNzIjoibWlkZ2FyZCIsImV4cCI6MjE0NzQ4Mj"
    "c5OSwia2V5IjoidHJ1ZSIsImFnZW5jeUlkIjoiMSIsImJ1c2luZXNzSWQiOiIiLCJuYmYiOjE1NTk3M"
    "zk5NTYsImF1ZCI6Im1pbGVzdG9uZS5hc2dhcmQifQ.pEMDHsrD0WIh-Mk2PjoazdR-A2uOHMVfQcJWqppVtNE"
)

class Selector(BaseModel):
    profileId: int = Field(..., description="Unique ID of the profile to fetch")

class ProfileRequest(BaseModel):
    selectors: list[Selector]
    showInactiveProfiles: bool = True

async def fetch_profile(profile_id: int) -> Dict[str, Any]:
    """
    Fetch profile data from the Midgard API for the given profile ID.
    """
    url = "https://t-midgard.milestoneinternet.com/api/v1.0/profile/findprofiles"
    payload = ProfileRequest(selectors=[Selector(profileId=profile_id)])
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload.dict(), headers=headers)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_profile(profile_id: int) -> dict:
    """
    Get profile information by ID from the Midgard API.

    Args:
        profile_id (int): ID of the profile to fetch.

    Returns:
        dict: Profile data retrieved from the API.
    """
    try:
        return await fetch_profile(profile_id)
    except Exception as e:
        return {"error": str(e)}
