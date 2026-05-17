#!/usr/bin/env python3
"""
NYC Running Events Finder – Managed Agent Trigger
Starts a session for a pre-built agent (defined in Anthropic Console),
sends the initial user message, and streams events until completion.

Configuration is loaded from a .env file (or environment variables).

Required:
    ANTHROPIC_API_KEY   Your Anthropic API key
    MANAGED_AGENT_ID    The agent ID from Anthropic Console
    ENVIRONMENT_ID      The environment ID from Anthropic Console
"""

import logging
import os
import sys
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Reading from environment only.")
    print("Install with: pip install python-dotenv")

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed")
    print("Install with: pip install anthropic")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _get_required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(
            f"Missing required environment variable: {name}\n"
            f"  Set it in your .env file or via: export {name}='...'"
        )
    return value


def _get_optional(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip() or default


def load_env_config() -> dict:
    return {
        "api_key":        _get_required("ANTHROPIC_API_KEY"),
        "agent_id":       _get_required("MANAGED_AGENT_ID"),
        "environment_id": _get_required("ENVIRONMENT_ID"),
        "vault_id":       _get_optional("VAULT_ID"),
        "email":          _get_optional("AGENT_EMAIL",            "sawan.dasari@gmail.com"),
        "search_weeks":   int(_get_optional("AGENT_SEARCH_WEEKS", "4")),
    }


def log_config(cfg: dict) -> None:
    logger.info("Configuration:")
    logger.info("  Agent ID      : %s", cfg["agent_id"])
    logger.info("  Environment   : %s", cfg["environment_id"])
    logger.info("  Vault ID      : %s", cfg["vault_id"] or "(none)")
    logger.info("  Recipient     : %s", cfg["email"])
    logger.info("  Search weeks  : %d", cfg["search_weeks"])


def create_session(cfg: dict, client: anthropic.Anthropic) -> str | None:
    """Create a managed agent session via the SDK and return the session ID."""
    logger.info("Creating managed agent session...")

    kwargs = {
        "agent":          cfg["agent_id"],
        "environment_id": cfg["environment_id"],
    }
    if cfg["vault_id"]:
        kwargs["vault_ids"] = [cfg["vault_id"]]

    try:
        session = client.beta.sessions.create(**kwargs)
        logger.info("Session created: %s", session.id)
        return session.id
    except anthropic.APIError as e:
        logger.error("Failed to create session: %s", e)
        return None


def build_user_message(cfg: dict) -> str:
    today       = datetime.now()
    date_str    = today.strftime("%B %d, %Y")
    day_of_week = today.strftime("%A")
    weeks       = cfg["search_weeks"]

    return (
        f"Today is {day_of_week}, {date_str}.\n\n"
        f"Please search for upcoming running events in the NYC metro area "
        f"(including NYC, Jersey City, Hoboken, Exchange Place, and surrounding "
        f"New Jersey/NYC areas) for the next {weeks}\u2013{weeks + 2} weeks.\n\n"
        f"Collect the essential information for each event (event name, date, "
        f"location, distance, cost, registration close date, and registration link).\n\n"
        f"Format the results as a clean HTML table and send an email to {cfg['email']} "
        f"with the subject line "
        f'"\U0001f3c3 Upcoming Running Events Near NYC \u2013 {date_str}".\n\n'
        f"Use the Gmail tool to actually SEND the email \u2014 do not just draft it. "
        f"If no events are found, send a brief email stating that."
    )


def run_session(cfg: dict, client: anthropic.Anthropic, session_id: str) -> bool:
    user_message = build_user_message(cfg)

    logger.info("Sending initial message to session %s...", session_id)

    try:
        client.beta.sessions.events.send(
            session_id=session_id,
            events=[{
                "type":    "user.message",
                "content": [{"type": "text", "text": user_message}],
            }],
        )
    except anthropic.APIError as e:
        logger.error("Failed to send initial message: %s", e)
        return False

    logger.info("Message sent. Streaming session events...\n")

    event_count = 0
    try:
        for event in client.beta.sessions.events.stream(session_id=session_id):
            event_count += 1
            event_type = event.type
            event_id   = getattr(event, "id", "")

            if event_type in (
                    "session.status_active",
                    "session.status_idle",
                    "message.created",
                    "message.completed",
            ):
                logger.info("[%d] %s  %s", event_count, event_type, event_id)

            if event_type == "session.status_idle":
                logger.info(
                    "\nSession completed (idle). Email should be in %s's inbox.",
                    cfg["email"],
                )
                return True

            if event_type == "error":
                logger.error("Agent error: %s", getattr(event, "message", "unknown"))
                return False

            if event_count > 10_000:
                logger.warning("Event limit reached; stopping stream.")
                break

    except anthropic.APIError as e:
        logger.error("Stream error: %s", e)
        return False

    logger.info("Total events processed: %d", event_count)
    return True


def main() -> int:
    logger.info("\nNYC Running Events Finder \u2013 Managed Agent\n")

    try:
        cfg = load_env_config()
    except ValueError as e:
        logger.error(str(e))
        return 1

    log_config(cfg)

    client = anthropic.Anthropic(api_key=cfg["api_key"])

    session_id = create_session(cfg, client)
    if not session_id:
        logger.error("Could not create session. Aborting.")
        return 1

    success = run_session(cfg, client, session_id)
    if success:
        logger.info("\nAgent execution completed successfully.")
        return 0
    else:
        logger.error("\nAgent execution failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())