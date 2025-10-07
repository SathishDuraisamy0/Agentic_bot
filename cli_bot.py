
"""
Log Summarization & Insights Bot CLI
------------------------------------
A lightweight command-line client that connects to your Cloud Run FastAPI service.
URL: https://bot-650010057363.asia-south1.run.app
"""

import requests
import time
import sys
import os

# -------------------------------
# CONFIGURATION
# -------------------------------
BASE_URL = "https://bot-650010057363.asia-south1.run.app"
AUTO_CLOSE_TIMEOUT = 240     # auto-close after 4 minutes
QUIT_WORDS = {"exit", "quit", "bye", "close", "end"}


# HEADERS = {"x-api-key": API_KEY}
HEADERS = {}

# -------------------------------
# MAIN CHAT LOOP
# -------------------------------
def main():
    print("=" * 70)
    print("🤖  Log Summarization & Insights Bot (Cloud Run Edition)")
    print("Connected to:", BASE_URL)
    print("Type your query below, or type 'exit' to quit.")
    print("=" * 70)

    last_activity = time.time()

    try:
        while True:
            # Auto-close after timeout
            if time.time() - last_activity > AUTO_CLOSE_TIMEOUT:
                print("\n⏰ Session closed automatically after 4 minutes of inactivity.")
                break

            query = input("User: ").strip()
            if not query:
                continue
            last_activity = time.time()

            if query.lower() in QUIT_WORDS:
                confirm = input("Do you really want to close the chat? (yes/no): ").strip().lower()
                if confirm in {"y", "yes"}:
                    print("\n🙏 Thank you for using Log Summarization & Insights Bot!")
                    break
                else:
                    print("Okay, continuing...\n")
                    continue

            # Send query to Cloud Run API
            try:
                print("🤖 Thinking...\n")
                res = requests.get(f"{BASE_URL}/chat", params={"query": query}, headers=HEADERS, timeout=120)

                if res.status_code == 200:
                    data = res.json()
                    response = data.get("response", "No response received.")
                    print(f"Bot: {response}\n")

                else:
                    print(f"❌ Server returned {res.status_code}: {res.text}\n")

            except requests.exceptions.RequestException as e:
                print(f"❌ Network error: {e}\n")

    except KeyboardInterrupt:
        print("\n🧩 Interrupted. Closing session gracefully...")

    finally:
        print("\nSession closed. Goodbye!")
        sys.exit(0)

# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    main()
