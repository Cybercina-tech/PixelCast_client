"""
Resolve .env file locations for Docker vs local development.

Docker: host ./.env is mounted at /config/.env (isolated from ./BackEnd:/app).
Set PIXELCAST_SIGNAGE_ENV_FILE=/config/.env in compose (see docker-compose.yml).
"""
import os
from pathlib import Path


def resolve_env_file_paths(base_dir: Path) -> tuple[Path, Path]:
    """
    Return (.env path, .env.template path).

    Resolution order for .env:
    1. PIXELCAST_SIGNAGE_ENV_FILE if set (canonical in Docker: /config/.env; file may be missing until wizard runs).
    2. /config/.env if it exists (when env var omitted but mount present).
    3. base_dir.parent / '.env' (monorepo root, local without Docker).
    4. base_dir / '.env' (BackEnd-only local layout).
    5. Default for new writes: base_dir.parent / '.env'.

    Template: prefer base_dir then base_dir.parent (not stored under /config).
    """
    explicit = (
        os.environ.get('PIXELCAST_SIGNAGE_ENV_FILE', '').strip()
        or os.environ.get('SCREENGRAM_ENV_FILE', '').strip()  # legacy deployments
    )
    if explicit:
        env_path = Path(explicit)
    else:
        config_path = Path('/config/.env')
        parent_env = base_dir.parent / '.env'
        base_env = base_dir / '.env'
        if config_path.exists():
            env_path = config_path
        elif parent_env.exists():
            env_path = parent_env
        elif base_env.exists():
            env_path = base_env
        else:
            env_path = parent_env

    tmpl_base = base_dir / '.env.template'
    tmpl_parent = base_dir.parent / '.env.template'
    if tmpl_base.exists():
        tmpl_path = tmpl_base
    elif tmpl_parent.exists():
        tmpl_path = tmpl_parent
    else:
        tmpl_path = tmpl_base

    return env_path, tmpl_path
