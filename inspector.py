import websockets
import inspect

print('--- dir(websockets) ---')
print(dir(websockets))

if hasattr(websockets, 'client'):
    print('\n--- dir(websockets.client) ---')
    print(dir(websockets.client))

if hasattr(websockets, 'asyncio'):
    print('\n--- dir(websockets.asyncio) ---')
    print(dir(websockets.asyncio))

if hasattr(websockets, 'connect'):
    print('\n--- websockets.connect is a function ---')
    print(inspect.getsource(websockets.connect))