# FastAPI Blog

A small blog built while learning FastAPI. It serves regular HTML pages with Jinja2 and also exposes a JSON API, so you can use it in a browser or try it out from `/docs`.

What's in it:

- Registration and login with JWT access tokens
- Create, edit, and delete posts (only the author can change their own)
- Profile picture uploads with server-side resizing
- Pagination on the home page and user post pages
- Forgot/reset password flow with a token sent by email
- Async SQLAlchemy models, PostgreSQL, and Alembic migrations
- A demo data seeder if you want a populated site right away

## Requirements

- Python 3.12+ (uv can install it for you)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL 14+ running locally, or Docker, or SQLite if you just want to try things
- Optional: Mailpit or another SMTP server if you want to test password reset emails

The commands below are for macOS/Linux. Run them from the project root.

## Setup

### 1. Install dependencies

```bash
uv sync
```

This creates `.venv` and installs everything from `uv.lock`.

### 2. Create the media directory

```bash
mkdir -p media/profile_pics
```

The app mounts `media/` at startup, and it will fail with `RuntimeError: Directory 'media' does not exist` if the folder isn't there. Uploaded profile pictures go in `media/profile_pics/`, which is gitignored.

### 3. Start PostgreSQL with Docker

If you don't already have PostgreSQL running, this is the quickest way to get one:

```bash
docker run --name fastapi-blog-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=fastapi_blog \
  -p 5432:5432 \
  -v fastapi_blog_pgdata:/var/lib/postgresql/data \
  -d postgres:17
```

Check that it's accepting connections:

```bash
docker exec fastapi-blog-db pg_isready -U postgres -d fastapi_blog
```

You want to see `accepting connections` at the end of the output. On the first run it can take a few seconds, so retry if it isn't ready yet. If it still isn't ready, `docker logs fastapi-blog-db` usually shows why.

A few useful commands for later:

```bash
docker stop fastapi-blog-db     # stop it
docker start fastapi-blog-db    # start it again
docker rm -f fastapi-blog-db    # remove the container (data stays in the volume)
```

If you want to wipe the database and start over, remove the container and the volume:

```bash
docker rm -f fastapi-blog-db
docker volume rm fastapi_blog_pgdata
```

If port `5432` is already taken by another Postgres, publish a different host port, for example `-p 5433:5432`, and use `5433` in `DATABASE_URL`.

If you already have Postgres installed locally, you can skip Docker and create the database directly:

```bash
createdb fastapi_blog
```

Then use your local Postgres user and password in `DATABASE_URL` rather than the Docker credentials.

### 4. Create your `.env`

```bash
cp .env.example .env
```

Generate a secret key:

```bash
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

Open `.env` and paste that value into `SECRET_KEY`. The two required values are `DATABASE_URL` and `SECRET_KEY`. The `DATABASE_URL` already points at the Docker database described above, so you only need to edit it if you changed the credentials or port. A minimal `.env` looks like this:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/fastapi_blog
SECRET_KEY=paste-the-generated-value-here
```

If your database password contains special characters, URL-encode them.

Prefer SQLite? No server or Docker needed. Replace the `DATABASE_URL` line with this:

```env
DATABASE_URL=sqlite+aiosqlite:///./blog.db
```

The file is created when you run the migrations.

### 5. Run the migrations

```bash
uv run alembic upgrade head
```

This creates the `users`, `posts`, and `password_reset_token` tables. Alembic reads `DATABASE_URL` from `.env`, so make sure that file exists first.

### 6. Seed some demo data (optional)

```bash
uv run python populate_db.py
```

This creates six users and 44 posts, and uploads the profile pictures in `populate_images/`. It is destructive: it deletes existing users, posts, and profile pictures first. Only run it on a development database.

After seeding you can log in as:

```text
Email:    UjjavalParmar@gmail.com
Password: DemoPass1!
```

The other demo accounts and their passwords are listed at the top of `populate_db.py`.

### 7. Start the app

```bash
uv run fastapi dev main.py
```

Open:

- App: <http://127.0.0.1:8000>
- API docs (Swagger UI): <http://127.0.0.1:8000/docs>
- Alternative docs (ReDoc): <http://127.0.0.1:8000/redoc>

The login endpoint expects your **email** in the OAuth2 form's `username` field. In Swagger, that means putting the email in the `username` box, not your username.

## Environment variables

All of these live in `.env`. Only `DATABASE_URL` and `SECRET_KEY` are required.

| Variable | Default | What it does |
| --- | --- | --- |
| `DATABASE_URL` | none, required | SQLAlchemy async database URL |
| `SECRET_KEY` | none, required | Signs JWT access tokens and reset tokens |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | How long a login token lasts |
| `RESET_TOKEN_EXPIRE_MINUTES` | `60` | How long a password reset link lasts |
| `FRONTEND_URL` | `http://localhost:8000` | Base URL used in password reset emails |
| `MAIL_SERVER` | `localhost` | SMTP host |
| `MAIL_PORT` | `587` | SMTP port |
| `MAIL_USERNAME` | empty | SMTP username, if your provider needs one |
| `MAIL_PASSWORD` | empty | SMTP password, if your provider needs one |
| `MAIL_FROM` | `noreply@example.com` | Sender address on outgoing mail |
| `MAIL_USE_TLS` | `true` | Use STARTTLS when talking to the SMTP server |
| `MAX_UPLOAD_SIZE_BYTES` | `5242880` | Maximum profile picture size (5 MB) |
| `POSTS_PER_PAGE` | `10` | Default page size for the HTML pages and API |

## Testing password reset emails locally

Password reset sends real email through SMTP, so you need something to catch it locally. Mailpit is the easiest option:

```bash
docker run --name fastapi-blog-mail -p 1025:1025 -p 8025:8025 -d axllent/mailpit
```

Then set these in `.env`:

```env
MAIL_SERVER=localhost
MAIL_PORT=1025
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=noreply@example.com
MAIL_USE_TLS=false
```

Go to <http://localhost:8025> to read the messages.

If you don't want Docker, you can run a plain SMTP debug server instead:

```bash
uvx --from aiosmtpd aiosmtpd -n -l 127.0.0.1:1025
```

It prints messages to the terminal rather than giving you a web inbox. Keep `MAIL_USE_TLS=false` with it, because the local server doesn't support STARTTLS.

For a hosted provider such as Mailtrap, use the host, port, username, and password they give you, set `MAIL_FROM` to an address the provider allows, and turn `MAIL_USE_TLS` back on if their port uses STARTTLS (usually port 587).

Then visit <http://127.0.0.1:8000/forgot-password>, enter a registered email, and check the inbox. The email contains a link back to `/reset-password?token=...`.

## Common commands

```bash
# Development server with auto-reload
uv run fastapi dev main.py

# Production-style server (no reload)
uv run fastapi run main.py

# Apply migrations
uv run alembic upgrade head

# Create a migration after changing models.py
uv run alembic revision --autogenerate -m "describe your change"

# Undo the last migration
uv run alembic downgrade -1

# Re-seed demo data (destructive)
uv run python populate_db.py
```

When you generate a migration, open the new file in `alembic/versions/` and read it before applying it. Autogenerate is a good first draft, not a guarantee.

## API overview

All API routes live under `/api`. Routes marked "Yes" need an `Authorization: Bearer <token>` header.

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/api/users` | No | Register a user |
| POST | `/api/users/token` | No | Log in; form field `username` is your email |
| GET | `/api/users/me` | Yes | Current user's profile |
| GET | `/api/users/{id}` | No | Public profile |
| GET | `/api/users/{id}/posts` | No | A user's posts, paginated |
| PATCH | `/api/users/{id}` | Yes | Update your own username or email |
| DELETE | `/api/users/{id}` | Yes | Delete your own account |
| PATCH | `/api/users/{id}/picture` | Yes | Upload your profile picture |
| DELETE | `/api/users/{id}/picture` | Yes | Remove your profile picture |
| PATCH | `/api/users/me/password` | Yes | Change your password |
| POST | `/api/users/forgot-password` | No | Request a reset email |
| POST | `/api/users/reset-password` | No | Set a new password with a token |
| GET | `/api/posts` | No | List posts; supports `skip` and `limit` |
| POST | `/api/posts` | Yes | Create a post |
| GET | `/api/posts/{id}` | No | Get one post |
| PUT | `/api/posts/{id}` | Yes | Replace your own post |
| PATCH | `/api/posts/{id}` | Yes | Partially update your own post |
| DELETE | `/api/posts/{id}` | Yes | Delete your own post |

Pagination uses `skip` and `limit`. `limit` is capped at 100.

### Pages

| Path | Page |
| --- | --- |
| `/` and `/posts` | Home feed |
| `/posts/{id}` | Single post |
| `/users/{id}/posts` | Posts by one user |
| `/login` | Login |
| `/register` | Register |
| `/account` | Account settings and profile picture |
| `/forgot-password` | Request a password reset |
| `/reset-password?token=...` | Set a new password |

## Project layout

```text
main.py              App setup, HTML routes, static mounts, error handlers
config.py            Settings loaded from .env
database.py          Async engine, session factory, Base
models.py            SQLAlchemy models
schemas.py           Pydantic request/response schemas
auth.py              Password hashing, JWT creation/verification
routers/
  users.py           User, auth, password reset, and picture endpoints
  posts.py           Post CRUD endpoints
templates/           Jinja2 pages and the reset email template
static/              CSS, JS, icons, and the default avatar
media/               Uploaded profile pictures (created locally, gitignored)
alembic/             Migration environment and versions
populate_db.py       Demo data seeder
populate_images/     Source images used by the seeder
```

## Troubleshooting

**`RuntimeError: Directory 'media' does not exist`**

Run `mkdir -p media/profile_pics` from the project root. The app checks for the directory at startup.

**`database_url Field required` or a validation error on startup**

`DATABASE_URL` is missing from `.env`. Copy `.env.example` again or add the line manually.

**`connection refused` when running migrations**

The database isn't running, the port is wrong, or the database name doesn't exist. Check the container with `docker ps` and `docker exec fastapi-blog-db pg_isready -U postgres -d fastapi_blog`.

**`password authentication failed`**

The username or password in `DATABASE_URL` doesn't match the container. The Docker command above uses `postgres` / `postgres`; change both places if you change one.

**Login says "Incorrect email or password"**

Use the email address, not the username. Demo passwords are case-sensitive. If you didn't seed the database, register an account first.

**The reset email never arrives**

Check that `MAIL_USE_TLS=false` when using Mailpit or `aiosmtpd` on port 1025, and look in the Mailpit inbox at <http://localhost:8025>. Email sending happens as a FastAPI background task, so SMTP errors usually show up in the server log after the request completes.

**A registration request returns 422**

Passwords need at least 8 characters, usernames are 1 to 50 characters, and the email must be valid.

**Profile picture upload returns 400**

The file must be a real image (JPEG, PNG, GIF, or WebP) under `MAX_UPLOAD_SIZE_BYTES` (5 MB by default). Pillow checks the file contents, not just the extension.

**Port 8000 is already in use**

Run `uv run fastapi dev main.py --port 8001` and update `FRONTEND_URL` if you want reset links to point at the new port.

## Before putting this online

This is a learning project, so a few things are set up for local development:

- Use a fresh `SECRET_KEY` and a real database password. Don't ship the demo values.
- Serve it over HTTPS and set `FRONTEND_URL` to the public URL.
- Use a real SMTP provider for password reset email.
- Back up the database and `media/` directory. Uploaded files are stored on local disk and are not in git.
- Run it with `uv run fastapi run main.py` behind a reverse proxy or process manager rather than the dev server.
