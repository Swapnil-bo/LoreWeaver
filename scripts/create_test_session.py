"""
Create a test session via the running backend API.
Usage: python scripts/create_test_session.py

Prints the session_id to paste into the browser console:
  localStorage.setItem('lw_session_id', '<id>'); location.reload()
"""
import urllib.request
import json

url = "http://127.0.0.1:8000/api/create_session"
req = urllib.request.Request(url, method="POST", data=b"",
                             headers={"Content-Type": "application/json"})

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

session_id = data["session_id"]
region     = data["region"]

print(f"Session created: {session_id}")
print(f"Starting region: {region}")
print()
print("Paste this in your browser console (F12 > Console):")
print(f"  localStorage.setItem('lw_session_id', '{session_id}'); location.reload()")
