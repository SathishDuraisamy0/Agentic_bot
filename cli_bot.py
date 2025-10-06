import asyncio
import sys
import time
from src.logger import get_logger
from src.chatbot import get_answer

logger = get_logger(__name__)

AUTO_CLOSE_TIMEOUT = 240  
QUIT_WORDS = {"exit", "quit", "bye", "close", "end"}

def main():
    logger.info("🤖CLI Chatbot started.")
    print("Log Summarization & Insights Bot CLI started.")
    last_activity = time.time()

    try:
        while True:
            # Auto-close if idle > 4 minutes
            if time.time() - last_activity > AUTO_CLOSE_TIMEOUT:
                print("\n⏰ Session closed automatically after 4 minutes of inactivity.")
                logger.info("Auto-closed after inactivity (4 min).")
                break

            query = input("User: ").strip()
            if not query:
                continue
            last_activity = time.time()

            # Exit confirmation
            if query.lower() in QUIT_WORDS:
                confirm = input("Do you really want to close the chat? (yes/no): ").strip().lower()
                if confirm in {"y", "yes"}:
                    logger.info("Session ended by user confirmation.")
                    print("\n🙏 Thank you for using Log Summarization & Insights Bot!")
                    break
                else:
                    print("Alright, continuing the session...\n")
                    continue

            try:
                print("🤖 Thinking...")
                response = get_answer(query)
                print(f"Bot: {response}\n")
                logger.info(f"Processed query: {query[:60]}")
                
            except Exception as e:
                print("❌ Error while processing query.")
                logger.error(f"Error: {e}")

    except KeyboardInterrupt:
        print("\nInterrupted. Closing session gracefully...")
        logger.warning("Keyboard interrupt detected. Session closed.")

    finally:
        print("\n Session closed. Goodbye!")
        logger.info("CLI chatbot terminated cleanly.")
        sys.exit(0)

if __name__ == "__main__":
    main()
