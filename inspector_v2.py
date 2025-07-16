import pkgutil
import websockets

print(f"Inspecting websockets package installed at: {websockets.__path__[0]}\n")

print("Found submodules:")
for submodule in pkgutil.walk_packages(path=websockets.__path__, prefix='websockets.'):
    print(submodule.name)