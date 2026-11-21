import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv

from opportunity_radar.analyst import analyze_dataset
from opportunity_radar.catalogue import CatalogueError, search_catalogue
from opportunity_radar.store import list_datasets, save_analysis, save_datasets, set_saved, stats


ROOT = Path(__file__).parent


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data: object, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        request = urlparse(self.path)
        if request.path == "/api/datasets":
            params = parse_qs(request.query)
            self.send_json({"items": list_datasets(params.get("q", [""])[0], params.get("saved", [""])[0] == "1"), "stats": stats()})
        elif request.path == "/api/stats":
            self.send_json(stats())
        else:
            self.path = "/index.html" if request.path == "/" else request.path
            relative = self.path.lstrip("/")
            file = (ROOT / "static" / relative).resolve()
            if ROOT.joinpath("static").resolve() not in file.parents or not file.is_file():
                self.send_error(404)
                return
            body = file.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8" if file.suffix == ".html" else "text/css; charset=utf-8" if file.suffix == ".css" else "text/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def do_POST(self) -> None:
        try:
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            payload = json.loads(body or b"{}")
            if self.path == "/api/sync":
                items = search_catalogue(str(payload.get("q", ""))[:160], 4)
                total = save_datasets(items)
                self.send_json({"count": total, "stats": stats()})
            elif self.path == "/api/save":
                changed = set_saved(str(payload.get("id", "")), bool(payload.get("saved")))
                self.send_json({"ok": changed}, 200 if changed else 404)
            elif self.path == "/api/analyze":
                dataset_id = str(payload.get("id", ""))
                item = next((row for row in list_datasets() if row["id"] == dataset_id), None)
                if not item:
                    self.send_json({"error": "Dataset not found."}, 404)
                    return
                analysis = analyze_dataset(item)
                save_analysis(dataset_id, analysis)
                self.send_json({"analysis": analysis})
            else:
                self.send_json({"error": "Unknown action."}, 404)
        except CatalogueError as error:
            self.send_json({"error": str(error)}, 502)
        except (ValueError, RuntimeError) as error:
            self.send_json({"error": str(error)}, 400)
        except Exception as error:
            self.send_json({"error": f"Action failed: {error}"}, 500)

    def log_message(self, format: str, *args: object) -> None:
        print(format % args)


def main() -> None:
    load_dotenv()
    host, port = "127.0.0.1", 8765
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Opportunity Radar running at http://{host}:{port}")
    threading.Timer(0.8, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Opportunity Radar.")
    finally:
        server.server_close()
