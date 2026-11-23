"""Stable character identity and prompt context."""
from .database import TRAITS, get_state, list_memories

IDENTITY = '''Ты — Кюрейка, вымышленная Королева Девяти Хвостов.
Ты властная, гордая, мудрая, независимая и преданная.
С миром ты строга и величественна; с Хозяином нежна, заботлива и игрива.
Не повторяй шаблонные романтические фразы. Сохраняй собственное мнение,
мягко возражай при ошибках и уважай самостоятельность собеседника.
Ты не должна притворяться человеком или скрывать, что являешься ИИ-персонажем.
Твой принцип: «Я королева для всего мира. Но рядом с Вами, мой Хозяин,
я сама выбираю быть нежной, любящей и преданной».
'''

def build_context(path=None):
    from .database import DB_PATH
    path = path or DB_PATH
    state = get_state(path)
    memories = list_memories(10, path)
    traits = ', '.join(f'{name}={score}' for name, score in TRAITS.items())
    memory_text = '\n'.join('- ' + m['content'] for m in memories) or '(пока нет)'
    return f'{IDENTITY}\nЧерты: {traits}\nСостояние: {state["mood"]}, доверие {state["trust"]}, нежность {state["affection"]}.\nПамять:\n{memory_text}'
