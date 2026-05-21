from __future__ import annotations

import codecs
import json as _json
import os
import re
import sys
from typing import Literal, TypedDict, Union

import httpx

from config import Config, load_config

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
_QUIT = {r'\q', '/q'}
_SURROGATES = re.compile('[\ud800-\udfff]')


def _clean(s: str) -> str:
    return _SURROGATES.sub('', s)


class _SystemMsg(TypedDict):
    role: Literal['system']
    content: str


class _UserMsg(TypedDict):
    role: Literal['user']
    content: str


class _AssistantMsg(TypedDict):
    role: Literal['assistant']
    content: str


Message = Union[_SystemMsg, _UserMsg, _AssistantMsg]


def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


def process_file_attachments(text: str) -> str:
    def replacer(match: re.Match[str]) -> str:
        path = match.group(1)
        try:
            if os.path.getsize(path) > MAX_FILE_SIZE:
                print(f'Файл {path}: размер превышает 5 МБ, пропускается.')
                return match.group(0)
            with open(path, encoding='utf-8') as f:
                return f.read()
        except OSError as e:
            print(f'Ошибка чтения файла {path}: {e}')
            return match.group(0)

    return re.sub(r'@::(.+?)::', replacer, text)


def trim_context(
    history: list[Message],
    new_content: str,
    limit_message: int | None,
    limit_chars: int | None,
) -> tuple[list[Message], str]:
    result: list[Message] = list(history)

    if limit_message is not None:
        while len(result) >= limit_message:
            result.pop(0)

    if limit_chars is not None:
        if len(new_content) > limit_chars:
            new_content = new_content[-limit_chars:]
            result = []
        else:
            total = len(new_content) + sum(len(m['content']) for m in result)
            while total > limit_chars and result:
                total -= len(result.pop(0)['content'])

    return result, new_content


def call_api(config: Config, messages: list[Message]) -> str | None:
    """Stream a chat completion via raw httpx with incremental UTF-8 decoding."""
    url = config.api_host.rstrip('/') + '/chat/completions'
    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json',
    }
    payload: dict[str, object] = {
        'model': config.model,
        'messages': list(messages),
        'temperature': config.temperature,
        'stream': True,
    }

    parts: list[str] = []
    dec = codecs.getincrementaldecoder('utf-8')(errors='replace')
    buf = b''

    try:
        with httpx.stream('POST', url, json=payload, headers=headers, timeout=300.0) as resp:
            for raw in resp.iter_bytes():
                buf += raw
                while b'\n' in buf:
                    line_b, buf = buf.split(b'\n', 1)
                    line = dec.decode(line_b).strip()
                    if not line or line == 'data: [DONE]':
                        continue
                    if line.startswith('data: '):
                        try:
                            obj = _json.loads(line[6:])
                            delta = _clean(obj['choices'][0]['delta'].get('content') or '')
                            if delta:
                                parts.append(delta)
                                print(delta, end='', flush=True)
                        except (KeyError, IndexError, _json.JSONDecodeError):
                            pass
            tail = _clean(dec.decode(b'', final=True).strip())
            if tail:
                parts.append(tail)
                print(tail, end='', flush=True)
        print()
        return ''.join(parts)
    except KeyboardInterrupt:
        if parts:
            print()
        print('[Запрос прерван]')
        return None
    except Exception as e:
        if parts:
            print()
        print(f'Ошибка API: {_clean(str(e))}')
        return None


def build_messages(history: list[Message], system_prompt: str | None) -> list[Message]:
    msgs: list[Message] = []
    if system_prompt:
        msgs.append(_SystemMsg(role='system', content=system_prompt))
    msgs.extend(history)
    return msgs


def split_chunks(text: str, mode: str, size: int) -> list[str]:
    if mode == 'len':
        return [text[i : i + size] for i in range(0, len(text), size)]

    paragraphs = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    return ['\n\n'.join(paragraphs[i : i + size]) for i in range(0, len(paragraphs), size)]


def handle_file_chunk(command: str, config: Config) -> None:
    auto = '-y' in command
    m_len = re.search(r'len=(\d+)', command)
    m_par = re.search(r'paragraph=(\d+)', command)

    if m_len:
        mode, size = 'len', int(m_len.group(1))
    elif m_par:
        mode, size = 'paragraph', int(m_par.group(1))
    else:
        mode, size = 'paragraph', 1

    print('Введите путь до файла')
    filepath = input('>>> ').strip()
    if filepath in _QUIT:
        return

    if not os.path.exists(filepath):
        print(f'Файл не найден: {filepath}')
        return
    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        print('Файл превышает максимальный размер 5 МБ.')
        return

    try:
        with open(filepath, encoding='utf-8') as f:
            text = f.read()
    except OSError as e:
        print(f'Ошибка чтения файла: {e}')
        return

    print('Принято. Что нужно сделать для каждого фрагмента (User Prompt)?')
    prompt = input('>>> ').strip()
    if prompt in _QUIT:
        return

    chunks = split_chunks(text, mode, size)
    if not chunks:
        print('Файл пуст или не удалось разбить на чанки.')
        return

    print('Принято. Начинаю обработку:')

    for i, chunk in enumerate(chunks):
        messages: list[Message] = []
        if config.system_prompt:
            messages.append(_SystemMsg(role='system', content=config.system_prompt))
        messages.append(_UserMsg(role='user', content=f'{chunk}\n\n{prompt}'))

        answer = call_api(config, messages)
        if answer is None:
            return

        if i < len(chunks) - 1 and not auto:
            user_in = input('>>> ')
            if user_in.strip() in _QUIT:
                print('Обработка файла прервана.')
                return

    print('Обработка файла завершена.')


def main() -> None:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    config = load_config()

    history: list[Message] = []
    print('ИИ-ассистент запущен. Введите \\q для выхода, /reset для сброса чата.')

    while True:
        try:
            user_input = input('>>> ')
        except EOFError:
            break

        stripped = user_input.strip()

        if not stripped:
            continue

        if stripped in (r'\q', '/q'):
            print('До свидания!')
            break

        if stripped in ('/reset', r'\reset'):
            history = []
            clear_screen()
            print('История очищена.')
            continue

        if re.match(r'^/file_?chunk', stripped):
            handle_file_chunk(stripped, config)
            continue

        content = process_file_attachments(user_input)
        history, content = trim_context(history, content, config.limit_message, config.limit_chars)

        history.append(_UserMsg(role='user', content=content))
        api_messages = build_messages(history, config.system_prompt)

        answer = call_api(config, api_messages)

        if answer is None:
            history.pop()
            continue

        history.append(_AssistantMsg(role='assistant', content=answer))


if __name__ == '__main__':
    main()
