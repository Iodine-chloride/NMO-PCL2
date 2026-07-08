# AGENTS

This repository is primarily a Python-based magazine/news synchronization and XAML generation utility.

## Key project facts
- Primary executable script: `Files/Customhelps/news.py`
- Main commands are:
  - `python news.py dev` — start a local development HTTP server from the `dev` directory
  - `python news.py run` — build/copy `dev` to `run`, rewrite local HTTP URLs to production URLs, then start the server from `run`
  - `python news.py check` — sync magazine content from the remote service and update local `main.xaml`
- The script is written for Python 3 and uses `requests` and `PyMuPDF` (`fitz`).

## Important paths and structure
- `Files/Customhelps/news.py` — central logic for downloading magazines, converting PDFs to PNGs, generating XAML/JSON, and serving content
- `Files/Customhelps/dev/` — source directory for local content and server assets
- `Files/Customhelps/dev/pages/magazine/` — expected location for magazine UUID folders and generated `main.xaml`/`origin.json`
- `Files/Customhelps/run/` — generated production-ready copy of `dev` after URL rewriting
- `Files/Customhelps/dev/staticpages/` — static page examples used by the project

## Development conventions
- Path handling in `news.py` is relative to the script's working directory, so prefer editing or running it from `Files/Customhelps` unless you adjust paths.
- Generated XAML embeds local URLs like `http://127.0.0.1:8000/...`; the `run` command rewrites them to `https://cus.nmo.net.cn:25569`.
- Magazine data is stored per UUID with `origin.json`, `main.json`, and `main.xaml`.
- The current repository has no CI/test configuration in the workspace, so assume manual execution and local validation.

## Guidance for AI coding agents
- Focus on `Files/Customhelps/news.py` for feature changes, bug fixes, or workflow updates.
- Preserve the existing `dev`/`run` URL rewrite behavior unless the change explicitly targets deployment URL handling.
- Do not assume any other Python package management file exists; if dependencies are needed, mention `requests` and `PyMuPDF` explicitly.
- When modifying generated XAML, keep indentation and XAML structure stable to avoid breaking the view rendering.

## Reference
- See `README.md` for the current project status note.
