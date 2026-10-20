# aitherios.cloud

A personal project showcase built with [Wagtail](https://wagtail.org/) (Django CMS), in English, Traditional Chinese and Spanish.

- **Stack:** Python 3.13, Django 6.1, Wagtail 7.4, wagtail-localize, MariaDB 11.4, Gunicorn, Docker
- **Hosting:** Docker on a Hostinger VPS, behind Caddy (HTTPS)
- **Languages:** `/en/` (default), `/zh-hant/`, `/es/`

## Quick start (on the server)

```bash
git clone https://github.com/tw168/aitherios-site.git
cd aitherios-site
cp .env.example .env        # then edit .env and set real values
docker network create proxy # once; shared with Caddy
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

The site is then at `http://127.0.0.1:8000/` on the VPS, and the editor at `/admin/`.
Point Caddy at it (see the developer guide).

## Documentation

- [Developer guide](docs/DEVELOPER.md): setup, structure, deployment, tests, how to extend
- [User guide](docs/USER_GUIDE.md): editing content and translations in the admin
- [Changelog](CHANGELOG.md)

## Secrets

All passwords and keys live in `.env` on the server. `.env` is ignored by git, and every push is scanned for leaked secrets. Never commit real values.
