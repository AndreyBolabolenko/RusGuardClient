import uuid

import requests
import urllib3
import logging

from RusGuardClient import Decoder
from datetime import datetime as dt
from RusGuardClient.Models import LogMessage
from RusGuardClient.xml_creator import xml_document
from xml.dom.minidom import Document
from json import loads

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(format='[%(asctime)s] NetworkClient: %(message)s', datefmt='%d/%b/%y %H:%M:%S', level=logging.INFO)


class NetworkClient:
    url = None
    session_uuid = None
    client_uuid = None

    request_count = 0
    username = ""
    password = ""

    def __init__(self, host, username, password):
        self.url = f"https://{host}/LNetworkServer/LNetworkService.svc"
        self.client_uuid = str(uuid.uuid4())
        self.username = username
        self.password = password

        self.packet_count = 0

        self.Connect()

    def Socket(self, soapaction, data, timeout=60):
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'Soapaction': '"' + soapaction + '"',
            'Accept-Encoding': 'gzip, deflate'
        }
        try:
            time_start = dt.now()
            response = requests.post(self.url, verify=False, headers=headers, data=data.encode(), timeout=timeout)
            if response.status_code == 500:
                block = Decoder.ErrorDecode(response.text)
                logging.info("Time Wait: " + f"{dt.now()-time_start}")
                logging.error("%s - %s", block['faultcode'], block['faultstring'])
                raise SystemError

            return response.text
        except requests.ConnectionError:
            logging.error("Ошибка подключения к серверу: %s", self.url)
            exit(500)

    def SecureHeader(self, count) -> xml_document:
        root = xml_document()
        root.xml_timestamp()
        root.xml_usernametoken(self.username, self.password, "uuid-" + self.client_uuid + "-" + str(count))

        return root

    def Connect(self):
        """
        Отправка запроса с авторизацией на сервер и получения токена.
        :return: Ключ сессии
        """
        soapaction = "http://www.rusguardsecurity.ru/ILNetworkService/Connect"
        root = self.SecureHeader(self.packet_count + 1)
        data = root.xml_method("Connect", {"xmlns": "http://www.rusguardsecurity.ru"})

        logging.info("Попытка подключения к серверу.")
        response = self.Socket(soapaction, data.toxml())
        try:
            self.session_uuid = Decoder.ConnectionDecode(response)
        except ValueError:
            logging.error("Ошибка получения токена авторизации")

        self.packet_count += 1
        logging.info("Авторизация прошла успешно.")
        logging.info("SessionID - %s", self.session_uuid)

    def Disconnect(self):
        """
        Закрываем соединение с сервером
        :return:
        """
        soapaction = "http://www.rusguardsecurity.ru/ILNetworkService/Disconnect"

        root = self.SecureHeader(self.packet_count + 1)
        data = root.xml_method("Disconnect", {"xmlns": "http://www.rusguardsecurity.ru"})

        self.Socket(soapaction, data.toxml())
        logging.info("Соединение с сервером разорвано.")

    def GetVersion(self) -> str:
        """
        Получение версии сервера
        :return:
        """
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetVariable"

        root = self.SecureHeader(self.packet_count + 1)

        child = Document().createElement("name")
        child.appendChild(Document().createTextNode("Version"))

        data = root.xml_method("GetVariable", {"xmlns": "http://www.rusguardsecurity.ru"}, [child])
        response = self.Socket(soapaction, data.toxml())
        key, value = Decoder.GetVariable(response)

        logging.info("Версия сервера: %s", value)

        return value

    def GetLastEvent(self) -> LogMessage:
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetLastEvent"

        with open("./RusGuardClient/Templates/GetLastEvent.json", 'r') as file:
            json_file = loads(file.read())

        root = self.SecureHeader(self.packet_count + 1)
        data = root.xml_simple(Decoder.JsonToXML(json_file))

        response = self.Socket(soapaction, data.toxml())
        event = Decoder.GetLastEvent(response)

        logging.info("ID Последнего события %s", event.Id)
        logging.info("[%s] %s", event.Message, event.Details)

        self.packet_count += 1
        return event

    def GetEvents(self, fromMessageId=0) -> [LogMessage]:
        soapaction = "http://www.rusguardsecurity.ru/ILDataService/GetEvents"

        with open("./RusGuardClient/Templates/GetEvents.json", 'r') as file:
            json_file = loads(file.read())

        json_file['GetEvents']['fromMessageId'] = fromMessageId

        root = self.SecureHeader(self.packet_count + 1)
        data = root.xml_simple(Decoder.JsonToXML(json_file))

        response = self.Socket(soapaction, data.toxml())
        self.packet_count += 1
        return Decoder.GetEvents(response)

    async def GetNotification(self):
        soapaction = "http://www.rusguardsecurity.ru/ILNetworkService/GetNotification"

        with open("./RusGuardClient/Templates/GetNotification.json", 'r') as file:
            json_file = loads(file.read())

        json_file['GetNotification']['connectionId'] = self.session_uuid

        root = self.SecureHeader(self.packet_count + 1)
        data = root.xml_simple(Decoder.JsonToXML(json_file))

        response = self.Socket(soapaction, data.toxml(), 9)
        self.packet_count += 1

        return Decoder.GetNotification(response)
