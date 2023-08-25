import json
import pathlib
import typing

import requests


class Config:
    __serialize__ = ["host", "port"]
    host:str = "localhost"
    port:int = 5000

    def __init__(self, path=None):
        if not path:
            self.path = pathlib.Path.home() / ".avmap" / "avctrl.json"
        else:
            self.path = pathlib.Path(path)
        
        if self.path.exists():
            self.load()
        else:
            self.save()

    def json(self) -> str:
        return json.dumps({n: getattr(self, n) for n in self.__serialize__})
    
    def load(self) -> None:
        with open(self.path, "r") as f:
            for k, v in json.load(f).items():
                setattr(self, k, self._cast(k, v))
    
    def _cast(self, attr: str, value: typing.Any) -> typing.Any:
        return type(getattr(self, attr))(value)
    
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            f.write(self.json())

class Api:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.session = requests.Session()
        self.url = f"http://{self.host}:{self.port}"
    
    def _get(self, path):
        return self.session.get(f"{self.url}{path}")
    
    def _post(self, path, json=None):
        return self.session.post(f"{self.url}{path}", json=json)
    
    def get_color(self, station):
        return self._get(f"/station/{station}/color").json()
    
    def set_color(self, station, color, show=False):
        result = self._post(f"/station/{station}/color", json={"color": color, "show": show})
        return result.ok
    
    def set_colors(self, colors: typing.Dict[str, typing.List[int]], show=False):
        return self._post("/stations/color", json={"colors": colors, "show": show}).ok

    def get_colors(self):
        return self._get("/stations/color").json()

    def show(self):
        return self._post("/show").ok
