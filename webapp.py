import json
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from core import gateway, reasoning

ROOT=Path(__file__).resolve().parent
TOKEN=secrets.token_urlsafe(32)

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
        elif self.path=="/assets/avatar.png" and (ROOT/"assets/avatar.png").is_file():
            self.send_data((ROOT/"assets/avatar.png").read_bytes(),"image/png")
        else:
            self.reply({"error":"Not found"},404)
    def do_POST(self):
        if self.path!="/api/chat" or self.headers.get("X-Session-Token")!=TOKEN:
            return self.reply({"error":"Forbidden"},403)
        try:
            length=int(self.headers.get("Content-Length","0"))
            if not 0<length<=65536:
                return self.reply({"error":"Invalid size"},400)
            message=json.loads(self.rfile.read(length))["message"]
            if not isinstance(message,str) or not message.strip() or len(message)>12000:
                return self.reply({"error":"Invalid message"},400)
            self.reply({"answer":gateway.chat(message)})
        except Exception:
            self.reply({"error":"Ошибка модели или конфигурации Cloud.ru. Проверьте настройки."},502)

if __name__=="__main__":
    reasoning.setup()
    with ThreadingHTTPServer(("127.0.0.1",0),Handler) as server:
        url="http://127.0.0.1:"+str(server.server_port)+"/"
        print(url,flush=True)
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
