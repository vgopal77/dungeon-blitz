import websocket
import json
import threading
import queue


class NetworkClient:
    def __init__(self, url):
        self._url = url
        self._send_q = queue.Queue()
        self._recv_q = queue.Queue()
        self._ws = None
        self.connected = False
        self.player_id = None
        self.room_code = None
        self.error = None

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        def on_open(ws):
            self.connected = True
            while not self._send_q.empty():
                ws.send(json.dumps(self._send_q.get()))

        def on_message(ws, raw):
            self._recv_q.put(json.loads(raw))

        def on_error(ws, err):
            self.error = str(err)

        self._ws = websocket.WebSocketApp(
            self._url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
        )
        self._ws.run_forever()

    def send(self, data):
        if self._ws and self.connected:
            try:
                self._ws.send(json.dumps(data))
            except Exception:
                pass
        else:
            self._send_q.put(data)

    def relay(self, data):
        self.send({'type': 'relay', 'data': data})

    def poll(self):
        msgs = []
        while not self._recv_q.empty():
            msgs.append(self._recv_q.get())
        return msgs
