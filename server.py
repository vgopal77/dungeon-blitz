import asyncio
import websockets
import json
import random
import string
import os

rooms = {}


def make_code():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=4))


async def handler(ws):
    room_code = None
    pid = None

    try:
        async for raw in ws:
            msg = json.loads(raw)
            t = msg.get('type')

            if t == 'create':
                code = make_code()
                while code in rooms:
                    code = make_code()
                rooms[code] = [ws, None]
                room_code = code
                pid = 0
                await ws.send(json.dumps({'type': 'created', 'code': code, 'pid': 0}))

            elif t == 'join':
                code = msg.get('code', '').upper()
                if code not in rooms or rooms[code][1] is not None:
                    await ws.send(json.dumps({'type': 'error', 'msg': 'Room not found or full'}))
                else:
                    rooms[code][1] = ws
                    room_code = code
                    pid = 1
                    await ws.send(json.dumps({'type': 'joined', 'pid': 1}))
                    host = rooms[code][0]
                    if host:
                        await host.send(json.dumps({'type': 'p2_joined'}))

            elif t == 'relay' and room_code and room_code in rooms:
                msg['pid'] = pid
                payload = json.dumps(msg)
                for p in rooms[room_code]:
                    if p and p != ws:
                        await p.send(payload)

    except Exception:
        pass
    finally:
        if room_code and room_code in rooms:
            slots = rooms[room_code]
            new_slots = [p if p != ws else None for p in slots]
            for p in new_slots:
                if p:
                    try:
                        await p.send(json.dumps({'type': 'p_left'}))
                    except Exception:
                        pass
            if not any(new_slots):
                del rooms[room_code]
            else:
                rooms[room_code] = new_slots


async def main():
    port = int(os.environ.get('PORT', 8765))
    print(f"Dungeon Blitz server running on port {port}")
    async with websockets.serve(handler, '0.0.0.0', port):
        await asyncio.Future()


asyncio.run(main())
