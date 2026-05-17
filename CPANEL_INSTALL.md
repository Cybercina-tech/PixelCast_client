# cPanel Installation Guide (Shared Hosting / Passenger)

This package supports cPanel Python hosting (Phusion Passenger) with a browser-based installer.

## Before You Start

- Ensure your host provides **Setup Python App**.
- Create a MySQL/PostgreSQL database and user in cPanel first.
- Keep your purchase code ready.

## Buyer Flow (No Terminal Required)

1. Upload and extract `main.zip`.
2. In **Setup Python App**, create a Python app that points to the extracted `app` folder.
3. Ensure `passenger_wsgi.py` exists in the app root (already included).
4. Visit your domain.
5. Complete the installer wizard:
   - Enter purchase code.
   - Confirm detected domain.
   - Enter DB credentials created in cPanel.
   - Create admin account.
6. The installer validates license and DB, writes `.env`, runs migrations, creates admin, and triggers Passenger restart via `tmp/restart.txt`.

## Safety Defaults Included

- `.htaccess` in app root blocks direct access to:
  - `.env` and `.env.*`
  - log/db-like files (`*.log`, `*.sqlite`, `*.sqlite3`, `*.db`)
  - sensitive runtime paths (`logs`, `tmp`, `backups`, `installation_state`)
- This protects accidental extraction inside `public_html`.

## Release Packaging Requirements (For Seller)

For CodeCanyon-ready delivery, build releases with:

- Frontend already compiled (`npm run build` output embedded in Django static source).
- `collectstatic` already executed in release bundle.
- Buyer only needs Python app setup + dependency install from `requirements.txt`.

Use:

```bash
./build-cpanel-release.sh
```

The script generates `release/main.zip`.

## Troubleshooting

- **DisallowedHost / CORS issues**: confirm installer domain matches your real host.
- **DB auth errors**: cPanel DB names/users are usually prefixed (for example `cpaneluser_dbname`).
- **License validation failed**: verify purchase code format and outbound network access.
- **No restart effect**: restart Python app from cPanel panel once manually.
