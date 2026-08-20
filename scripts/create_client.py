"""Script to create a client and print the API key."""
import argparse
import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()


async def main(name: str) -> None:
    from app.core.config import get_settings
    from app.core.database import get_session_factory
    from app.core.security import generate_api_key, hash_api_key
    from app.models.client import Client

    settings = get_settings()
    factory = get_session_factory(settings.DATABASE_URL)

    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key, settings.API_KEY_SALT)

    async with factory() as session:
        client = Client(name=name, api_key_hash=key_hash, is_active=True)
        session.add(client)
        await session.commit()
        await session.refresh(client)

    print("Client created successfully.")
    print(f"ID:      {client.id}")
    print(f"Name:    {client.name}")
    print(f"API Key: {raw_key}")
    print("Save this key now. It will not be shown again.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new API client")
    parser.add_argument("--name", required=True, help="Client name")
    args = parser.parse_args()
    asyncio.run(main(args.name))
