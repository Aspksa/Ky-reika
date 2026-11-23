"""Initialize and inspect Kyūreika's local core. No AI provider configured yet."""
import argparse
from core.database import DB_PATH, initialize, add_memory, list_memories, get_state
from core.personality import build_context

def main():
    parser = argparse.ArgumentParser(description='Kyūreika core')
    parser.add_argument('command', nargs='?', choices=['init','status','remember','remember-prompt','memories','context'], default='status')
    parser.add_argument('text', nargs='?')
    args = parser.parse_args()
    initialize()
    if args.command == 'init':
        print(f'База данных создана: {DB_PATH}')
    elif args.command == 'status':
        print(f'KYŪREIKA | SQLite: {DB_PATH}\nЭмоции: {get_state()}')
    elif args.command == 'remember':
        if not args.text:
            parser.error('Для remember укажите текст воспоминания')
        print(f'Сохранено воспоминание #{add_memory(args.text)}')
    elif args.command == 'remember-prompt':
        try:
            value = input('Текст воспоминания: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('Отменено.')
        else:
            if value:
                print(f'Сохранено воспоминание #{add_memory(value)}')
            else:
                print('Пустой текст не сохранён.')
    elif args.command == 'memories':
        for item in list_memories():
            print(f'#{item["id"]} [{item["category"]}] {item["content"]}')
    elif args.command == 'context':
        print(build_context())

if __name__ == '__main__':
    main()
