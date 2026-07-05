import os

name = os.environ.get("NAME", "Welt")
print(f"Hallo {name}, ich laufe in einem Docker-Container!")
