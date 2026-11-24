import json
import os
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import logging
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from core import gateway, reasoning, sleep
from core.resource_priority import foreground

ROOT=Path(__file__).resolve().parent
TOKEN=secrets.token_urlsafe(32)
CLOUD_BASE='https://foundation-models.api.cloud.ru/v1'
CLOUD_LOCK=threading.Lock()

def cloud_models(key):
    if not isinstance(key,str) or not key.strip() or len(key)>8192 or any(c in key for c in '\r\n'):
        raise ValueError('Invalid key')
    req=Request(CLOUD_BASE+'/models',headers={'Authorization':'Bearer '+key.strip()})
    with urlopen(req,timeout=30) as response:
        data=json.loads(response.read(8*1024*1024))
    return sorted({m['id'] for m in data['data'] if isinstance(m.get('id'),str)})

class Handler(BaseHTTPRequestHandler):
    def send_data(self,data,kind,status=200):
        self.send_response(status)
        self.send_header("Content-Type",kind)
        self.send_header("Content-Length",str(len(data)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.end_headers()
        self.wfile.write(data)
    def reply(self,obj,status=200):
        self.send_data(json.dumps(obj,ensure_ascii=False).encode(),"application/json; charset=utf-8",status)
    def do_GET(self):
        if self.path=="/":
            html=(ROOT/"index.html").read_text(encoding="utf-8").replace("</head>",'<meta name="session-token" content="'+TOKEN+'"></head>')
            self.send_data(html.encode(),"text/html; charset=utf-8")
        elif self.path=="/api/initiative":
            if self.headers.get("X-Session-Token")!=TOKEN:
                return self.reply({"error":"Forbidden"},403)
            from core.initiative import pending
            return self.reply({"initiatives":pending()[:1]})
        elif self.path=="/assets/avatar.png" and (ROOT/"assets/avatar.png").is_file():
            self.send_data((ROOT/"assets/avatar.png").read_bytes(),"image/png")
        else:
            self.reply({"error":"Not found"},404)
    def stream_reply(self,message):
        self.send_response(200)
        self.send_header("Content-Type","application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control","no-store")
        self.send_header("Connection","close")
        self.end_headers()
        self.close_connection=True
        def emit(event):
            self.wfile.write((json.dumps(event,ensure_ascii=False)+"\n").encode())
            self.wfile.flush()
        try:
            emit({"stage":"context"})
            for chunk in gateway.stream_chat(message,progress=lambda stage: emit({"stage":stage})):
                emit({"delta":chunk})
            emit({"done":True})
        except (BrokenPipeError,ConnectionResetError):
            return
        except HTTPError as exc:
            emit({"error":f"Cloud.ru HTTP {exc.code}"})
        except (URLError,TimeoutError):
            emit({"error":"Соединение с Cloud.ru прервано. Повторите запрос."})
        except Exception as exc:
            logging.error("Chat stream failed: %s",type(exc).__name__)
            try:
                emit({"error":"Ошибка потока Cloud.ru или когнитивного ядра."})
            except OSError:
                pass
    def do_POST(self):
        if self.path not in ("/api/chat","/api/chat/stream","/api/cloud/models","/api/cloud/connect") or self.headers.get("X-Session-Token")!=TOKEN:
            return self.reply({"error":"Forbidden"},403)
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=65536:
                return self.reply({"error":"Invalid size"},400)
            payload=json.loads(self.rfile.read(length))
            if self.path.startswith("/api/cloud/"):
                key=payload["key"]
                models=cloud_models(key)
                if self.path=="/api/cloud/models":
                    return self.reply({"models":models})
                model=payload["model"]
                if model not in models:
                    return self.reply({"error":"Модель недоступна"},400)
                req=Request(CLOUD_BASE+'/chat/completions',data=json.dumps({"model":model,"messages":[{"role":"user","content":"Ответь: OK"}],"max_completion_tokens":512,"stream":False}).encode(),headers={"Authorization":"Bearer "+key.strip(),"Content-Type":"application/json"})
                with urlopen(req,timeout=90) as response:
                    probe=json.loads(response.read(8*1024*1024))
                if not (probe.get("choices") or [{}])[0].get("message",{}).get("content"):
                    return self.reply({"error":"Модель не вернула текст. Выберите другую модель чата."},422)
                with CLOUD_LOCK:
                    os.environ.update(CLOUD_API_BASE=CLOUD_BASE,CLOUD_API_KEY=key.strip(),CLOUD_MODEL=model)
                return self.reply({"connected":True,"model":model})
            message=payload["message"]
            if not isinstance(message,str) or not message.strip() or len(message)>12000:
                return self.reply({"error":"Invalid message"},400)
            with foreground():
                if self.path=="/api/chat/stream":
                    return self.stream_reply(message)
                self.reply({"answer":gateway.chat(message)})
        except HTTPError as exc:
            return self.reply({"error":f"Cloud.ru HTTP {exc.code}: проверьте ключ, доступ к модели, баланс и параметры запроса."},502)
        except (URLError,TimeoutError):
            return self.reply({"error":"Cloud.ru недоступен или истекло время ожидания."},502)
        except Exception as exc:
            logging.error("Request failed: %s",type(exc).__name__)
            self.reply({"error":"Ошибка модели или конфигурации Cloud.ru. Проверьте настройки."},502)

if __name__=="__main__":
    reasoning.setup()
    with ThreadingHTTPServer(("127.0.0.1",0),Handler) as server:
        url="http://127.0.0.1:"+str(server.server_port)+"/"
        print(url,flush=True)
        webbrowser.open(url)
        stop,worker=sleep.start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()
            worker.join(timeout=5)
