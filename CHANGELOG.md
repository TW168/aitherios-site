# Changelog

## v0.1.0 — Home page (unreleased)

- Wagtail project with English, Traditional Chinese and Spanish (`/en/`, `/zh-hant/`, `/es/`)
- Home page: navbar, hero, introduction, featured projects, footer
- Projects page and the Video Analysis project page (content only; the analysis feature comes later)
- Navbar lists pages marked "Show in menus" plus Contact; Home and About are not listed
- Language switch that keeps the visitor on the same page
- Dark theme inspired by jpl.nasa.gov; works on phone, tablet and desktop
- Docker setup with MariaDB (utf8mb4), Gunicorn and WhiteNoise
- `setup_site` command that creates the starting pages and translations
- GitHub Actions: tests on MariaDB, migration check, Docker build, secret scan
