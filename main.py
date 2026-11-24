"""Initialize and inspect Kyūreika's local core. No AI provider configured yet."""
import argparse
import json
import time
from core import cognition
from core.database import DB_PATH, initialize, add_memory, list_memories, get_state
from core.personality import build_context

def main():
    parser = argparse.ArgumentParser(description='Kyūreika core')
    parser.add_argument('command', nargs='?', choices=['init','status','remember','remember-prompt','memories','context','sleep','worker','proposals','approve','rollback','audit'], default='status')
    parser.add_argument('text', nargs='?')
    args = parser.parse_args()
    cognition.setup()
    if args.command == 'init':
        print(f'База данных создана: {DB_PATH}')
    elif args.command == 'status':
        print(f'KYŪREIKA | SQLite: {DB_PATH}\nЭмоции: {get_state()}')
    elif args.command == 'remember':
        if not args.text:
            parser.error('Для remember укажите текст воспоминания')
        print(f'Сохранено воспоминание #{cognition.experience(args.text)}')
    elif args.command == 'remember-prompt':
        try:
            value = input('Текст воспоминания: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('Отменено.')
        else:
            if value:
                print(f'Сохранено воспоминание #{cognition.experience(value)}')
            else:
                print('Пустой текст не сохранён.')
    elif args.command == 'memories':
        for item in list_memories():
            print(f'#{item["id"]} [{item["category"]}] {item["content"]}')
    elif args.command == 'context':
        print(build_context())
        print(json.dumps(cognition.CONSTITUTION, ensure_ascii=False))
        print(json.dumps(cognition.affect({}), ensure_ascii=False))
    elif args.command == "sleep":
        from core.sleep import consolidate
        print(consolidate())
    elif args.command == "worker":
        from core.sleep import start
        stop, worker = start()
        try:
            while worker.is_alive():
                worker.join(1)
        except KeyboardInterrupt:
            stop.set()
            worker.join(5)
    elif args.command in ("approve", "rollback"):
        if not args.text or not args.text.isdecimal():
            parser.error("Укажите ID предложения")
        getattr(cognition, args.command)(int(args.text))
    elif args.command in ("proposals", "audit"):
        table = "cognition_proposal" if args.command == "proposals" else "cognition_audit"
        with cognition.connect() as db:
            for row in db.execute("SELECT * FROM " + table + " ORDER BY id DESC LIMIT 100"):
                print(json.dumps(dict(row), ensure_ascii=False))

if __name__ == '__main__':
    main()
