# Developer guide

## 1. Overview

| Part | What it is |
| --- | --- |
| `aitherios/` | Django project: settings, URLs, WSGI |
| `home/` | The app: page models, template tags, `setup_site` command, tests |
| `templates/` | Site-wide templates: `base.html`, navbar, footer, 404/500 |
| `home/templates/home/` | Templates for each page type |
| `static/` | CSS, JS, logo |
| `locale/` | Interface text translations (`.po` files) |
| `docker/`, `Dockerfile`, `docker-compose.yml` | Container setup |
| `.github/workflows/ci.yml` | Tests, migration check, Docker build, secret scan |

### Page tree

```
Root
├── Home (en)            → /en/
│   └── Projects         → /en/projects/
│       └── Video Analysis → /en/projects/video-analysis/
├── 首頁 (zh-hant)        → /zh-hant/   (same structure)
└── Inicio (es)          → /es/        (same structure)
```

Each language has its own copy of every page. The copies are linked by wagtail-localize, which gives editors a side-by-side translation screen.

### Page types

| Model | Allowed under | Purpose |
| --- | --- | --- |
| `HomePage` | Root | Landing page: hero, introduction, featured projects |
| `ProjectIndexPage` | `HomePage` | Lists all projects. In the navbar as "Projects" |
| `ProjectPage` | `ProjectIndexPage` | One project, e.g. Video Analysis |
| `FooterSettings` | Settings menu | GitHub URL and email shown in the footer |

## 2. How the pieces work

**Languages.** `LANGUAGES` in `settings.py` lists `en`, `zh-hant` and `es`. URLs use `i18n_patterns`, so every public URL starts with a language code; `/` redirects to `/en/`. Two kinds of text are translated:

- **Page content** (titles, hero text, project summaries): edited per language in the Wagtail admin.
- **Interface text** (Contact, View project, All rights reserved): in `locale/*/LC_MESSAGES/django.po`.

**Navbar** (`templates/includes/navbar.html`, tags in `home/templatetags/site_tags.py`):

- Logo, linking to the home page in the current language.
- Every live child of the current language's home page with **Show in menus** ticked. The home page itself is never listed.
- A fixed **Contact** link to the footer.
- The language switch. `language_links` links each language to the translation of the current page, falling back to that language's home page if there is no translation.

**Featured projects.** `HomePage.featured_projects` is an ordered list of `ProjectPage`s chosen in the admin. `get_featured_projects()` returns the live version in the visitor's language.

**Database.** MariaDB with `utf8mb4` and `utf8mb4_unicode_ci`. Both the server and the Django connection use that collation, which is required for Chinese text and avoids "Illegal mix of collations" errors. With no `DB_HOST` set, Django uses SQLite, which is handy for quick local work.

**Static and media files.** WhiteNoise serves `/static/` from inside the container. Uploads go to `/media/` and are served by Django (`SERVE_MEDIA=true`). Caddy only needs to proxy.

## 3. Local development

Needs Python 3.13 and `gettext`.

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt     # mysqlclient needs libmariadb-dev + pkg-config
export DJANGO_DEBUG=true            # uses SQLite when DB_HOST is not set
python manage.py migrate
python manage.py setup_site
python manage.py compilemessages
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/en/ and http://127.0.0.1:8000/admin/.

Or with Docker: `cp .env.example .env`, set `DJANGO_DEBUG=true` and passwords, then `docker compose up --build`.

## 4. Configuration (`.env`)

| Variable | Example | Notes |
| --- | --- | --- |
| `DJANGO_DEBUG` | `false` | Never `true` on the server |
| `DJANGO_SECRET_KEY` | long random string | Required when debug is off |
| `DJANGO_ALLOWED_HOSTS` | `aitherios.cloud,www.aitherios.cloud,localhost` | Comma-separated |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://aitherios.cloud` | Needed for admin logins over HTTPS |
| `WAGTAILADMIN_BASE_URL` | `https://aitherios.cloud` | Used in admin emails and links |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | | App database account |
| `DB_ROOT_PASSWORD` | | MariaDB root; used by the container only |
| `WEB_PORT` | `8000` | Port on the VPS, bound to 127.0.0.1 |
| `PROXY_NETWORK` | `proxy` | Docker network shared with Caddy |
| `SERVE_MEDIA` | `true` | Set `false` only if Caddy serves `/media/` |
| `DJANGO_LOG_LEVEL` | `WARNING` | `INFO` for more detail |

Generate a secret key: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`

## 5. Deployment (Hostinger VPS)

### First time

```bash
git clone https://github.com/tw168/aitherios-site.git
cd aitherios-site
cp .env.example .env && nano .env   # real values, DJANGO_DEBUG=false
docker network create proxy         # skip if it already exists
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

On start the container runs migrations and `setup_site`; `setup_site` does nothing once a home page exists.

### Caddy

If Caddy runs in Docker, attach it to the `proxy` network (`docker network connect proxy <caddy-container>`) and add:

```
aitherios.cloud, www.aitherios.cloud {
    encode gzip
    reverse_proxy aitherios-web:8000
}
```

If Caddy runs directly on the VPS, use `reverse_proxy 127.0.0.1:8000` instead.

Reload Caddy afterwards. Inside a container: `docker exec <caddy-container> caddy reload --config /etc/caddy/Caddyfile`.

### Releasing an update

```bash
cd aitherios-site
git pull
docker compose up -d --build
```

### Backups

```bash
# Database
docker compose exec db sh -c 'mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" --single-transaction "$MARIADB_DATABASE"' > backup-$(date +%F).sql
# Uploaded media
docker run --rm -v aitherios-site_media:/m -v "$PWD":/b alpine tar czf /b/media-$(date +%F).tgz -C /m .
```

Restore the database with `docker compose exec -T db sh -c 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE"' < backup.sql`.

### Logs

`docker compose logs -f web` and `docker compose logs -f db`.

## 6. Git workflow

- `main` is what runs on the server. Nobody commits to it directly.
- Each piece of work goes on a branch (`feature/home-page`, `feature/navbar`, …), then a pull request.
- CI must pass before merging. It runs the tests on MariaDB, checks migrations, builds the Docker image and scans for secrets.
- After merging, tag the release: `git tag v0.1.0 && git push --tags`, then deploy.

## 7. Tests

```bash
python manage.py test            # SQLite
DB_HOST=127.0.0.1 ... python manage.py test   # MariaDB, as CI does
```

`home/tests.py` covers the acceptance criteria: pages in all three languages, navbar contents, language switch targets, Chinese text, section order, footer settings, 404s and page-type rules.

## 8. Common tasks

**Replace the logo.** Overwrite `static/img/logo.svg`, keeping the name; a PNG works too if you update the `<img>` in `templates/includes/navbar.html`. Commit and deploy.

**Add a navbar item.** Create the page under Home in the admin and tick **Promote → Show in menus**. No code change is needed.

**Change interface text.** Edit the `.po` files in `locale/`. After adding new `{% trans %}` strings, run `python manage.py makemessages -l zh_Hant -l es`. The Docker build compiles them.

**Add a language.** Add it to `LANGUAGES` in `settings.py` and to `SHORT_NAMES` in `site_tags.py`. Run `makemessages -l <code>`, then add the locale and translate the pages in the admin (Settings → Locales).

**Change colours.** The CSS variables at the top of `static/css/site.css` (`--accent`, `--bg`, …).

## 9. Known notes

- Wagtail finishes publishing in on-commit callbacks. Creating a translated parent and its children inside one transaction leaves a stale child count, and the children then 404. `setup_site` recounts the tree afterwards. Normal admin use, one save per request, is not affected. If a page ever 404s while showing in the admin, run `python manage.py fixtree`.
- The navbar is basic in this phase. The full navbar (mega menu) is its own phase.
