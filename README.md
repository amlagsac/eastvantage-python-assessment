# Address Book API by Andre Lagsac

An address book API built using FastAPI backed by SQLite database. It supports contact and address management, soft deletion, unique email addresses checking, paginated listing, and nearby searches using longitude and latitude coordinates.

## Requirements

- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/)

## Install uv (Skip this step if already installed in local machine)

### macOS

In Terminal:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close and reopen Terminal if needed, then verify:

```sh
uv --version
```

### Windows

In PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen PowerShell if needed, then verify:

```powershell
uv --version
```

## Set up project

From the repository root, install the required Python version and sync the dependencies:

```sh
uv python install 3.13
uv sync
```

### Environment Variables configuration

To configure it, copy `.env.example` to `.env`.

macOS:

```sh
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Environment Variable settings:

| Variable | Default Value | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./address_book.db` | SQLAlchemy database connection URL to SQLite database |
| `DEBUG` | `false` | Debug-mode setting |
| `LOG_LEVEL` | `INFO` | Application log level |

## Run the application

From the repository root:

```sh
uv run fastapi dev
```

Alternatively:

```sh
uv run uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. API docs is available at `http://127.0.0.1:8000/docs`.

## API endpoints

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/addresses` | Create an address |
| `GET` | `/api/v1/addresses` | List active addresses |
| `GET` | `/api/v1/addresses/nearby` | Find active addresses within a distance |
| `GET` | `/api/v1/addresses/{address_id}` | Get one active address |
| `PATCH` | `/api/v1/addresses/{address_id}` | Update an active address |
| `DELETE` | `/api/v1/addresses/{address_id}` | Soft-delete an address |

### Pagination

The list and nearby endpoints accept:

- `limit`: page size, default `20`, minimum `1`, maximum `100`
- `offset`: number of matching records to skip, default `0`, minimum `0`

Both return `items` and nested pagination metadata:

```json
{
  "items": [],
  "pagination": {
    "total": 0,
    "limit": 20,
    "offset": 0,
    "has_more": false
  }
}
```

## Run tests

Run the complete test suite:

```sh
uv run pytest
```
