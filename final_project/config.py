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
    return str(raw) if raw is not None else None


def load_config() -> Config:
    cfg: dict[str, object] = {}
    has_yaml = os.path.exists('config.yaml')

    if has_yaml:
        with open('config.yaml', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}

    has_env = bool(os.environ.get('API_KEY') or os.environ.get('API_HOST'))

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

    limit_message_s = _env_or_yaml('LIMIT_MESSAGE', cfg, 'limit_message')
    limit_message = int(limit_message_s) if limit_message_s else None

    limit_chars_s = _env_or_yaml('LIMIT_CHARS', cfg, 'limit_chars')
    limit_chars = int(limit_chars_s) if limit_chars_s else None

    temperature_s = _env_or_yaml('TEMPERATURE', cfg, 'temperature')
    temperature = float(temperature_s) if temperature_s else 0.7

    system_prompt_raw = cfg.get('system_prompt')
    system_prompt = str(system_prompt_raw) if system_prompt_raw else None

    return Config(
        api_key=api_key,
        api_host=api_host,
        model=model,
        temperature=temperature,
        limit_message=limit_message,
        limit_chars=limit_chars,
        system_prompt=system_prompt,
    )
