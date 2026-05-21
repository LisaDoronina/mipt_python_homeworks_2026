from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import yaml  # type: ignore[import-untyped]


@dataclass
class Config:
    api_key: str
    api_host: str
    model: str
    temperature: float
    limit_message: int | None
    limit_chars: int | None
    system_prompt: str | None


def _env_or_yaml(env: str, cfg: dict[str, object], key: str) -> str | None:
    val = os.environ.get(env)
    if val is not None:
        return val
    raw = cfg.get(key)
    return None if raw is None else str(raw)  # WPS504: positive condition first


def _get_int(env: str, cfg: dict[str, object], key: str) -> int | None:
    val = _env_or_yaml(env, cfg, key)
    return int(val) if val else None


def _get_float(env: str, cfg: dict[str, object], key: str, default: float) -> float:
    val = _env_or_yaml(env, cfg, key)
    return float(val) if val else default


def load_config() -> Config:
    cfg: dict[str, object] = {}
    has_yaml = os.path.exists('config.yaml')

    if has_yaml:
        with open('config.yaml', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}

    has_env = 'API_KEY' in os.environ or 'API_HOST' in os.environ  # WPS221: simpler form

    if not has_yaml and not has_env:
        print('Ошибка: конфигурация не найдена.')
        print('Создайте config.yaml (см. config.yaml.example) или задайте переменные окружения.')
        sys.exit(1)

    api_key = _env_or_yaml('API_KEY', cfg, 'api_key')
    api_host = _env_or_yaml('API_HOST', cfg, 'api_host')

    if not api_key:
        print('Ошибка: не задан API ключ. Укажите API_KEY в переменных окружения или config.yaml.')
        sys.exit(1)
    if not api_host:
        print('Ошибка: не задан адрес сервера. Укажите API_HOST в окружении или config.yaml.')
        sys.exit(1)

    model = _env_or_yaml('MODEL', cfg, 'model') or 'gpt-4o-mini'
    system_prompt_raw = cfg.get('system_prompt')

    return Config(
        api_key=api_key,
        api_host=api_host,
        model=model,
        temperature=_get_float('TEMPERATURE', cfg, 'temperature', 0.7),
        limit_message=_get_int('LIMIT_MESSAGE', cfg, 'limit_message'),
        limit_chars=_get_int('LIMIT_CHARS', cfg, 'limit_chars'),
        system_prompt=None if system_prompt_raw is None else str(system_prompt_raw),
    )
