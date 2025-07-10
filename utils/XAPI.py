import requests
import json
import uuid
import urllib3
from datetime import datetime, timezone
from typing import Dict, Any
from dotenv import load_dotenv
import os

load_dotenv()
USERNAME=os.getenv("3X-UI_USERNAME")
PASSWORD=os.getenv("3X-UI_PASSWORD")
PATH=os.getenv("3X-UI_PATH")



# Отключаем предупреждения о небезопасном SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



class X3:
    """Класс для работы с API сервиса X3."""
    BASE_URL = PATH
    AUTH_DATA = {"username": USERNAME, "password": PASSWORD}

    def __init__(self):
        self.session = requests.Session()
        self.authenticate()

    def authenticate(self) -> None:
        """Аутентификация пользователя."""
        response = self.session.post(f"{self.BASE_URL}/login", json=self.AUTH_DATA, verify=False)
        response.raise_for_status()

    @staticmethod
    def _calculate_expiry_time(days: int, current_time: int = None) -> int:
        """Вычисляет время окончания подписки в миллисекундах."""
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        return (current_time or now) + days * 86400000 - 10800000

    def add_connection(self, days: int, tg_id: str, user_id: str) -> Dict[str, Any]:
        """Добавляет нового клиента."""
        expiry_time = self._calculate_expiry_time(days)
        client_data = {
            "id": str(uuid.uuid4()),
            "alterId": 90,
            "email": str(user_id),
            "limitIp": 2,
            "totalGB": 0,
            "expiryTime": expiry_time,
            "enable": True,
            "flow": "xtls-rprx-vision",
            "tgId": tg_id,
            "subId": ""
        }
        data = {"id": 1, "settings": json.dumps({"clients": [client_data]})}

        response = self.session.post(f"{self.BASE_URL}/panel/api/inbounds/addClient", json=data, verify=False)
        response.raise_for_status()
        return response.json()

    def list_clients(self) -> Dict[str, Any]:
        """Возвращает список клиентов."""
        response = self.session.get(f"{self.BASE_URL}/panel/api/inbounds/list", json=self.AUTH_DATA, verify=False)
        response.raise_for_status()
        return response.json()

    def link(self, user_id: str) -> str:
        """Генерирует ссылку для клиента."""
        connections = self.list_clients()
        clients = json.loads(connections['obj'][0]['settings'])['clients']
        client = next((c for c in clients if c['email'] == user_id), None)

        if not client:
            raise ValueError(f"Клиент с email {user_id} не найден.")

        client_id = client['id']
        stream_settings = json.loads(connections['obj'][0]['streamSettings'])
        tcp = stream_settings['network']
        security = stream_settings['security']

        return (
            f"vless://{client_id}@193.33.153.161:443?type={tcp}&security={security}"
            f"&pbk=7fltbrCdesXNPod2g6uW8_ZCahOUFz3m9DeoauvrCF8&fp=chrome&sni=google.com"
            f"&sid=ff25479867ca7d&spx=%2F&flow=xtls-rprx-vision#ProtegoVPN-{user_id}"
        )




    def update_client(self, days: int, user_id: str) -> requests.Response:
        """Обновляет информацию о клиенте."""
        connections = self.list_clients()
        clients = json.loads(connections['obj'][0]['settings'])['clients']
        client = next((c for c in clients if c['email'] == user_id), None)

        if not client:
            raise ValueError(f"Клиент с email {user_id} не найден.")

        client_id = client['id']
        current_expiry = client.get('expiryTime', 0)
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        if current_expiry < now:
            expiry_time = self._calculate_expiry_time(days, now)
        else:
            expiry_time = self._calculate_expiry_time(days, current_expiry)

        updated_data = {
            "id": 1,
            "settings": json.dumps({
                "clients": [{
                    "id": client_id,
                    "alterId": 90,
                    "email": str(user_id),
                    "limitIp": 2,
                    "totalGB": 0,
                    "expiryTime": expiry_time,
                    "enable": True,
                    "flow": "xtls-rprx-vision",
                    "tgId": str(user_id),
                    "subId": ""
                }]
            })
        }



        response = self.session.post(f"{self.BASE_URL}/panel/api/inbounds/updateClient/{client_id}", json=updated_data, verify=False)
        response.raise_for_status()
        return response

    def get_time(self, user_id: str) -> int:
        """Возвращает количество оставшихся дней подписки у клиента."""
        connections = self.list_clients()
        clients = json.loads(connections['obj'][0]['settings'])['clients']
        client = next((c for c in clients if c['email'] == user_id), None)

        if not client:
            raise ValueError(f"Клиент с email {user_id} не найден.")

        expiry_timestamp = client.get("expiryTime", 0)
        if not expiry_timestamp:
            return 0

        expiry_date = datetime.utcfromtimestamp(expiry_timestamp / 1000).replace(tzinfo=timezone.utc)
        today = datetime.now(timezone.utc)

        return max((expiry_date - today).days + 1, 0)
