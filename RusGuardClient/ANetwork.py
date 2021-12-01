import asyncio
import base64
import concurrent.futures
import logging
import uuid
from json import loads
from pathlib import Path

import requests
import urllib3
import aiohttp

from datetime import datetime, timedelta

from RusGuardClient import Decoder
from RusGuardClient.Models import LogMessage
from RusGuardClient.xml_creator import xml_document

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(format='[%(asctime)s] NetworkClient: %(message)s', datefmt='%d/%b/%y %H:%M:%S', level=logging.INFO)


class AsyncNetworkClient:
    _url = str
    _client_uuid = str
    _session_uuid = str

    _request_count = 0
    _username = str
    _password = str

    _template_dir = "./RusGuardClient/Templates"

    def __init__(self, host, username, password):
        self._url = f"https://{host}/LNetworkServer/LNetworkService.svc"
        self._client_uuid = str(uuid.uuid4())

        self._username = username
        self._password = password
        self._loop = asyncio.get_event_loop()

        self._connect()

    async def _socket(self, soapaction, data, timeout=15):
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'Soapaction': '"' + soapaction + '"',
            'Accept-Encoding': 'gzip, deflate'
        }

        try:
            http_connector = aiohttp.TCPConnector(verify_ssl=False)
            http_timeout = aiohttp.ClientTimeout(total=timeout)

            async with aiohttp.ClientSession(connector=http_connector, headers=headers,
                                             timeout=http_timeout) as session:
                async with session.post(self._url, data=data.encode()) as response:
                    if response.status == 500:
                        text = await response.text()
                        fault = Decoder.ErrorDecode(text)
                        logging.error("%s - %s", fault['faultcode'], fault['faultstring'])
                        raise SystemError

                    if response.status == 200:
                        text = await response.text()
                        return text
        except concurrent.futures.TimeoutError:
            raise TimeoutError

        except requests.ConnectionError:
            logging.error("Ошибка подключения к серверу: %s", self._url)
            exit(500)

    def _secure_header(self, count):
        xml_root = xml_document()
        xml_root.xml_timestamp()
        xml_root.xml_usernametoken(
            self._username,
            self._password,
            f"uuid-{self._client_uuid}-{count}"
        )

        return xml_root

    def _connect(self):
        """
        Подключение к сервру и получение токена авторизации
        :return: type: uuid
        """
        soapaction = "http://www.rusguardsecurity.ru/ILNetworkService/Connect"
        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_method(
            "Connect",
            {"xmlns": "http://www.rusguardsecurity.ru"}
        )

        logging.info("Попытка подключения к серверу.")
        response = self._loop.run_until_complete(
            self._socket(soapaction, data.toxml())
        )

        try:
            self._session_uuid = Decoder.ConnectionDecode(response)
            self._request_count += 1
            logging.info("Авторизация прошла успешно.")
            logging.info("SessionID - %s", self._session_uuid)

        except ValueError:
            logging.error("Ошибка получения токена авторизации")

    def disconnect(self):
        """
        Завершаем сеанс с сервером
        :return:
        """

        soapaction = "http://www.rusguardsecurity.ru/ILNetworkService/Disconnect"
        xml_root = self._secure_header(self._request_count + 1)

        data = xml_root.xml_method("Disconnect", {"xmlns": "http://www.rusguardsecurity.ru"})
        self._loop.run_until_complete(
            self._socket(soapaction, data.toxml())
        )
        logging.info("Соединение с сервером разорвано.")

    def get_version(self):
        """
        Запрос для получения версии сервера
        :return:
        """
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetVariable"

        with open(f"{self._template_dir}/GetVersion.json", 'r') as file:
            json_file = loads(file.read())

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = self._loop.run_until_complete(
            self._socket(soapaction, data.toxml())
        )
        self._request_count += 1
        key, value = Decoder.GetVariable(response)
        logging.info("Версия сервера: %s", value)

        return value

    async def get_last_event(self) -> LogMessage:
        """
        Запрос на получение идентификатора последнего события сервера
        :return:
        """
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetLastEvent"

        with open(f"{self._template_dir}/GetLastEvent.json", 'r') as file:
            json_file = loads(file.read())

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = await self._socket(soapaction, data.toxml())
        event = Decoder.GetLastEvent(response)

        logging.info("ID Последнего события %s", event.Id)
        logging.info("[%s] %s", event.Message, event.Details)

        self._request_count += 1
        return event

    async def get_events(self, last_event_id=None):
        """
        Возвращает все события произошедшие на сервере
        :param last_event_id: Идентификатор последнего сообщения
        :return:
        """
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetEvents"

        with open(f"{self._template_dir}/GetEvents.json", 'r') as file:
            json_file = loads(file.read())

        if last_event_id is None:
            event = await self.get_last_event()
            last_event_id = event.Id

        json_file['GetEvents']['fromMessageId'] = last_event_id

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = await self._socket(soapaction, data.toxml())
        self._request_count += 1

        return Decoder.GetEvents(response)

    async def get_notification(self):
        """
        Ожидание сообщения от сервера
        :return:
        """
        soapaction = "http://www.rusguardsecurity.ru/ILNetworkService/GetNotification"

        with open(f"{self._template_dir}/GetNotification.json", 'r') as file:
            json_file = loads(file.read())

        json_file['GetNotification']['connectionId'] = self._session_uuid

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = await self._socket(soapaction, data.toxml(), 9)
        self._request_count += 1

        return Decoder.GetNotification(response)

    async def get_employee_photo(self, employee_id, photo_number=1) -> str:
        """
        Формируем запрос на получение фотографии пользователя
        :param photo_number: Номер фотографии
        :param employee_id: Идентификатор владельца карты допуска
        :return:
        """
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetAcsEmployeePhoto"

        cache_photo = Path(f"./EmployeePhoto/{employee_id}.png")
        if cache_photo.exists():
            create_date = datetime.fromtimestamp(
                cache_photo.stat().st_ctime
            )

            create_date += timedelta(days=5)
            if datetime.now() < create_date:
                logging.info(f"Фотография пользователя ID:{employee_id}, загруженна с хранилища")
                with open(cache_photo, 'rb') as file:
                    byte_photo = file.read()
                    b64_encoded_photo = base64.b64encode(byte_photo)
                    self._request_count += 1
                    return b64_encoded_photo.decode('utf-8')

        with open(f"{self._template_dir}/GetAcsEmployeePhoto.json") as file:
            json_file = loads(file.read())

        json_file['GetAcsEmployeePhoto']['employeeId'] = employee_id
        json_file['GetAcsEmployeePhoto']['photoNumber'] = photo_number

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = await self._socket(soapaction, data.toxml())
        b64_encoded_photo = Decoder.GetAcsEmployeePhoto(response)

        if b64_encoded_photo is None:
            logging.info(f"Фотография пользователя ID:{employee_id} отсутсвует")
            with open(f"./EmployeePhoto/no_avatar.png", 'rb') as file:
                byte_photo = file.read()
                b64_encoded_photo = base64.b64encode(byte_photo)
                self._request_count += 1
                return b64_encoded_photo.decode('utf-8')

        with open(cache_photo, 'wb') as file:
            file.write(
                base64.b64decode(b64_encoded_photo)
            )

        logging.info(f"Фотография пользователя ID:{employee_id}, загруженна с сервера")
        self._request_count += 1

        return b64_encoded_photo

    def get_filtered_events(self, type, day):
        # TODO: Сделать полнофункциональный фильтр по эвентам
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetFilteredEvents"

        with open(f"{self._template_dir}/GetFilteredEvents.json", 'r') as file:
            json_file = loads(file.read())

        json_file['GetFilteredEvents']['msgSubTypes']['a:LogMsgSubType'] = type
        json_file['GetFilteredEvents']['fromDateTime'] = f"2021-10-{day}T00:00:00+08:00"
        json_file['GetFilteredEvents']['toDateTime'] = f"2021-10-{day}T23:59:59+08:00"

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = self._loop.run_until_complete(
            self._socket(soapaction, data.toxml())
        )

        self._request_count += 1
        return Decoder.GetFilteredEvents(response)

    async def get_log_message_types(self):
        """
        Формируем запрос на получения типов важности сообщения от сервера
        :return:
        """
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetLogMessageTypes"

        with open(f"{self._template_dir}/GetLogMessageTypes.json", 'r') as file:
            json_file = loads(file.read())

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = await self._socket(soapaction, data.toxml())
        self._request_count += 1
        return Decoder.GetLogMessageTypes(response)

    async def get_log_message_subtypes(self):
        """
        Формируем запрос на получения типов важности сообщения от сервера
        :return:
        """
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetLogMessageSubtypes"

        with open(f"{self._template_dir}/GetLogMessageSubtypes.json", 'r') as file:
            json_file = loads(file.read())

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = await self._socket(soapaction, data.toxml())
        self._request_count += 1
        return Decoder.GetLogMessageSubtypes(response)

    async def get_all_nets(self):
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetAllNets"

        with open(f"{self._template_dir}/GetAllNets.json", 'r') as file:
            json_file = loads(file.read())

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = await self._socket(soapaction, data.toxml())
        self._request_count += 1
        return Decoder.GetAllNets(response)

    async def get_net_servers(self, server_id=None):
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetNetServers"

        with open(f"{self._template_dir}/GetNetServers.json", 'r') as file:
            json_file = loads(file.read())

        if server_id is None:
            result = await self.get_all_nets()
            server_id = result.Id

        json_file['GetNetServers']['id'] = server_id

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = await self._socket(soapaction, data.toxml())
        self._request_count += 1

        return Decoder.GetNetServers(response)

    async def get_server_drivers_full_info(self, server_id):
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetServerDriversFullInfo"

        with open(f"{self._template_dir}/GetServerDriversFullInfo.json", 'r') as file:
            json_file = loads(file.read())

        json_file['GetServerDriversFullInfo']['serverID'] = server_id

        xml_root = self._secure_header(self._request_count + 1)
        data = xml_root.xml_simple(
            Decoder.JsonToXML(json_file)
        )

        response = await self._socket(soapaction, data.toxml())
        self._request_count += 1

        return Decoder.GetServerDriversFullInfo(response)

    async def process(self, action, controller_id):
        soapaction = "http://www.rusguardsecurity.ru/ILNetworkService/Process"

        with open(f"{self._template_dir}/Process.json", 'r') as file:
            json_file = loads(file.read())
