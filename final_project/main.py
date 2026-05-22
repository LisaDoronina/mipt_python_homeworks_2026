from __future__ import annotations

import codecs
import json as _json
import os
import re
import sys
from typing import Any, Literal, TypedDict, Union

import httpx

from config import Config, load_config

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
_QUIT = frozenset((r'\q', r'/q'))
_UTF8 = 'utf-8'
_PROMPT = '>>> '
_SURROGATES = re.compile('[\ud800-\udfff]')


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


def _clean(s: str) -> str:
    return _SURROGATES.sub('', s)


def _extract_delta(obj: Any) -> str:
    raw_delta = obj['choices'][0]['delta'].get('content')
    delta = _clean(raw_delta or '')
    return delta


def _parse_delta(line: str) -> str:
    if not line.startswith('data: ') or line == 'data: [DONE]':
        return ''
    try:
        return _extract_delta(_json.loads(line[6:]))
    except (KeyError, IndexError, _json.JSONDecodeError):
        return ''


def _read_stream(resp: httpx.Response) -> str:
    dec = codecs.getincrementaldecoder(_UTF8)(errors='replace')
    buf = b''
    parts: list[str] = []
    for raw in resp.iter_bytes():
        buf += raw
        while b'\n' in buf:
            line_b, buf = buf.split(b'\n', 1)
            delta = _parse_delta(dec.decode(line_b).strip())
            if delta:
                parts.append(delta)
                print(delta, end='', flush=True)
    tail = _clean(dec.decode(b'', final=True).strip())
    if tail:
        parts.append(tail)
        print(tail, end='', flush=True)
    return ''.join(parts)


def _stream_chat(config: Config, messages: list[Message]) -> str:
    host = config.api_host.rstrip('/')
    url = f'{host}/chat/completions'
    headers = {'Authorization': f'Bearer {config.api_key}', 'Content-Type': 'application/json'}
    payload: dict[str, object] = {
        'model': config.model,
        'messages': list(messages),
        'temperature': config.temperature,
        'stream': True,
    }
    with httpx.stream('POST', url, json=payload, headers=headers, timeout=300.0) as resp:
        result = _read_stream(resp)
    print()
    return result


def call_api(config: Config, messages: list[Message]) -> str | None:
    try:
        return _stream_chat(config, messages)
    except KeyboardInterrupt:
        print()
        print('[Запрос прерван]')
        return None
    except Exception as e:
        print()
        print(f'Ошибка API: {_clean(str(e))}')
        return None


def clear_screen() -> None:
    os.system('cls' if os.name == 'nt' else 'clear')


def _attach_file(path: str, original: str) -> str:
    try:
        size = os.path.getsize(path)
    except OSError as e:
        print(f'Ошибка чтения файла {path}: {e}')
        return original
    if size > MAX_FILE_SIZE:
        print(f'Файл {path}: размер превышает 5 МБ, пропускается.')
        return original
    try:
        with open(path, encoding=_UTF8) as f:
            return f.read()
    except OSError as e:
        print(f'Ошибка чтения файла {path}: {e}')
        return original


def process_file_attachments(text: str) -> str:
    def replacer(match: re.Match[str]) -> str:
        return _attach_file(match.group(1), match.group(0))

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
            msgs_chars = sum(len(m['content']) for m in result)
            total = len(new_content) + msgs_chars
            while total > limit_chars and result:
                total -= len(result.pop(0)['content'])

    return result, new_content


def build_messages(history: list[Message], system_prompt: str | None) -> list[Message]:
    msgs: list[Message] = []
    if system_prompt:
        msgs.append(_SystemMsg(role='system', content=system_prompt))
    msgs.extend(history)
    return msgs


def split_chunks(text: str, mode: str, size: int) -> list[str]:
    if mode == 'len':
        indices = range(0, len(text), size)
        chunks: list[str] = []
        for i in indices:
            chunks.append(text[i : i + size])
        return chunks

    paragraphs: list[str] = []
    for p in re.split(r'\n{2,}', text):
        if p.strip():
            paragraphs.append(p.strip())
    if not paragraphs:
        for p in text.split('\n'):
            if p.strip():
                paragraphs.append(p.strip())

    sep = '\n\n'
    indices = range(0, len(paragraphs), size)
    result: list[str] = []
    for i in indices:
        result.append(sep.join(paragraphs[i : i + size]))
    return result


def _load_file(filepath: str) -> str | None:
    try:
        size = os.path.getsize(filepath)
    except OSError as e:
        print(f'Ошибка доступа к файлу {filepath}: {e}')
        return None
    if size > MAX_FILE_SIZE:
        print('Файл превышает максимальный размер 5 МБ.')
        return None
    try:
        with open(filepath, encoding=_UTF8) as f:
            return f.read()
    except OSError as e:
        print(f'Ошибка чтения файла: {e}')
        return None


def _parse_chunk_args(command: str) -> tuple[str, int, bool]:
    auto = '-y' in command
    m_len = re.search(r'len=(\d+)', command)
    m_par = re.search(r'paragraph=(\d+)', command)
    if m_len:
        return 'len', int(m_len.group(1)), auto
    if m_par:
        return 'paragraph', int(m_par.group(1)), auto
    return 'paragraph', 1, auto


def _run_chunk_loop(chunks: list[str], prompt: str, config: Config, auto: bool) -> None:
    for i, chunk in enumerate(chunks):
        messages: list[Message] = []
        if config.system_prompt:
            messages.append(_SystemMsg(role='system', content=config.system_prompt))
        messages.append(_UserMsg(role='user', content=f'{chunk}\n\n{prompt}'))
        if call_api(config, messages) is None:
            return
        if i < len(chunks) - 1 and not auto:
            if input(_PROMPT).strip() in _QUIT:
                print('Обработка файла прервана.')
                return


def handle_file_chunk(command: str, config: Config) -> None:
    mode, size, auto = _parse_chunk_args(command)

    print('Введите путь до файла')
    filepath = input(_PROMPT).strip()
    if filepath in _QUIT:
        return

    text = _load_file(filepath)
    if text is None:
        return

    print('Принято. Что нужно сделать для каждого фрагмента (User Prompt)?')
    prompt = input(_PROMPT).strip()
    if prompt in _QUIT:
        return

    chunks = split_chunks(text, mode, size)
    if not chunks:
        print('Файл пуст или не удалось разбить на чанки.')
        return

    print('Принято. Начинаю обработку:')
    _run_chunk_loop(chunks, prompt, config, auto)
    print('Обработка файла завершена.')


def check(
    user_input: str,
    history: list[Message],
    config: Config,
) -> tuple[str, list[Message], str | None]:
    content = process_file_attachments(user_input)
    history, content = trim_context(history, content, config.limit_message, config.limit_chars)
    history.append(_UserMsg(role='user', content=content))
    answer = call_api(config, build_messages(history, config.system_prompt))
    return content, history, answer


def _handle_reset(history: list[Message]) -> list[Message]:
    clear_screen()
    print('История очищена.')
    return []


def _handle_message(
    user_input: str,
    history: list[Message],
    config: Config,
) -> list[Message]:
    content, history, answer = check(user_input, history, config)
    if answer is None:
        history.pop()
        return history
    history.append(_AssistantMsg(role='assistant', content=answer))
    return history


def process(config: Config, history: list[Message]) -> None:
    while True:
        try:
            user_input = input(_PROMPT)
        except EOFError:
            break

        stripped = user_input.strip()
        if not stripped:
            continue
        if stripped in _QUIT:
            print('До свидания!')
            break
        if stripped == '/reset':
            history = _handle_reset(history)
            continue
        if re.match(r'^/file_?chunk', stripped):
            handle_file_chunk(stripped, config)
            continue

        history = _handle_message(user_input, history, config)


def main() -> None:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding=_UTF8, errors='replace')

    config = load_config()
    history: list[Message] = []
    print(r'ИИ-ассистент запущен. Введите \q для выхода, /reset для сброса чата.')

    process(config, history)


if __name__ == '__main__':
    main()
