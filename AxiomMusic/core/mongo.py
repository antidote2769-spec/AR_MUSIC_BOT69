# -----------------------------------------------
# 🔸 AxiomMusic Project
# 🔹 Developed & Maintained by: Axiom Bots (https://t.me/axiombots)
# 📅 Copyright © 2026 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by AxiomBots
# -----------------------------------------------


from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConfigurationError, ConnectionFailure, ServerSelectionTimeoutError

from config import MONGO_DB_URI
from ..logging import LOGGER

MONGO_TIMEOUT_MS = 10000


def _validate_mongo_uri(uri: str) -> None:
    if not uri:
        raise RuntimeError(
            "MONGO_DB_URI is missing. On Railway, add MONGO_DB_URI or link the MongoDB "
            "plugin variable MONGO_URL to MONGO_DB_URI."
        )
    if not uri.startswith(("mongodb://", "mongodb+srv://")):
        raise RuntimeError(
            "MongoDB URI must start with mongodb:// or mongodb+srv://. Check Railway variables."
        )


LOGGER(__name__).info("Connecting to your Mongo Database...")
try:
    _validate_mongo_uri(MONGO_DB_URI)
    mongo_client = AsyncIOMotorClient(
        MONGO_DB_URI,
        connectTimeoutMS=MONGO_TIMEOUT_MS,
        serverSelectionTimeoutMS=MONGO_TIMEOUT_MS,
    )
    mongodb = mongo_client.Maanav
except (ConfigurationError, RuntimeError) as exc:
    LOGGER(__name__).error("Failed to configure Mongo Database: %s", exc)
    raise SystemExit(1) from exc


async def verify_mongo_connection() -> None:
    try:
        await mongo_client.admin.command("ping")
        LOGGER(__name__).info("Connected to your Mongo Database.")
    except (ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError) as exc:
        LOGGER(__name__).error(
            "Failed to connect to your Mongo Database: %s. "
            "If you use MongoDB Atlas, allow Railway's outbound IPs or allow 0.0.0.0/0 in Network Access.",
            exc.__class__.__name__,
        )
        raise SystemExit(1) from exc
