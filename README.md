# AxiomMuzic

## Railway MongoDB deployment fix

This bot needs a valid MongoDB connection string at startup. Railway's MongoDB plugin commonly exposes the connection string as `MONGO_URL`, while this project reads `MONGO_DB_URI`.

Set one of these variables in Railway:

- `MONGO_DB_URI` — recommended project variable name.
- `MONGO_URL` — also supported for Railway's MongoDB plugin.
- `MONGODB_URI` — also supported as a common alias.

If you use MongoDB Atlas instead of Railway's MongoDB plugin, also make sure Atlas Network Access allows Railway to connect. For quick testing you can allow `0.0.0.0/0`; for production, prefer Railway's documented outbound/IP allowlist setup when available.

Example Railway variable:

```env
MONGO_DB_URI=mongodb+srv://username:password@cluster0.example.mongodb.net/?retryWrites=true&w=majority
```

Do not commit real Telegram bot tokens, MongoDB passwords, API keys, or session strings to this repository. Rotate any secrets that were previously committed.
