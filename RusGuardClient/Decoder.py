import base64
from xml.etree.ElementTree import fromstring, iterparse
from xml.dom.minidom import Document, Element
from RusGuardClient.Models import LogMessage, Messages, EmployeePassageNotification

from io import StringIO
import logging


def get_namespaces(raw_string):
    namespaces = dict([
        node for _, node in iterparse(
            StringIO(raw_string), events=['start-ns']
        )
    ])
    return namespaces


def JsonToXML(json_object, key=None) -> Element:
    """
    Преобразование JSON документа для отправки для сервера
    :param json_object: JSON Документ
    :param key:
    :return:
    """
    if key is None:
        key = next(iter(json_object))

    element = Document().createElement(key)  # type: Element
    value = json_object[key]

    for key_x in value:
        if key_x == "_attributes":
            attributes = value[key_x]
            for key_i in attributes:
                element.setAttribute(key_i, str(attributes[key_i]))
            continue

        if isinstance(value[key_x], dict):
            element.appendChild(JsonToXML(value, key_x))
        else:
            node = Document().createElement(key_x)  # type: Element
            node.appendChild(
                Document().createTextNode(str(value[key_x]))
            )
            element.appendChild(node)

    return element


def ErrorDecode(message: str):
    """
    Декодирование сообщения об ошибке
    :param message:
    :return:
    """
    logging.basicConfig(format='[%(asctime)s] DECODER: %(message)s', datefmt='%d/%b/%y %H:%M:%S')

    try:
        root = fromstring(message)

        body = root.find('s:Body', get_namespaces(message))
        fault = body.find("s:Fault", get_namespaces(message))
        message_block = {}

        for item in fault:
            message_block[item.tag] = item.text

        return message_block
    except Exception:
        logging.error("Ошибка парсинга ответа от сервера")
        logging.error(message)
        exit(500)


def ConnectionDecode(message: str) -> str:
    """
    Получение UUID сессии
    :param message: сообщение от сервера
    :return: UUID
    """
    namespace = get_namespaces(message)

    body = fromstring(message).find("s:Body", namespace)
    ConnectionUUID = body.find(
        "{http://www.rusguardsecurity.ru}ConnectResponse/{http://www.rusguardsecurity.ru}ConnectResult", namespace)

    if ConnectionUUID is None:
        raise ValueError

    return ConnectionUUID.text


def GetVariable(message: str):
    namespace = get_namespaces(message)

    VariableResult = fromstring(message).find(
        "s:Body/{http://www.rusguardsecurity.ru}GetVariableResponse/{http://www.rusguardsecurity.ru}GetVariableResult",
        namespace
    )

    return VariableResult.find("a:Name", namespace).text, VariableResult.find("a:Value", namespace).text


def GetEvents(message: str) -> [LogMessage]:
    """
    Получаем объект эвентов сервера
    :param message: XML документ с сервера
    :return: Список сообщений
    """
    namespace = get_namespaces(message)
    events = fromstring(message).find(
        "s:Body/{http://www.rusguardsecurity.ru}GetEventsResponse/{http://www.rusguardsecurity.ru}GetEventsResult",
        namespace
    )
    list_messages = Messages(events, namespace)
    return list_messages.LogMessages


def GetLastEvent(message: str) -> LogMessage:
    """
    Получение последнего сообщения с сервера
    :param message: XML ответ с сервера
    :return:
    """
    namespace = get_namespaces(message)
    LastEvent = fromstring(message).find(
        "s:Body/{http://www.rusguardsecurity.ru}GetLastEventResponse/{http://www.rusguardsecurity.ru}GetLastEventResult",
        namespace
    )
    lastMessage = LastEvent.find("a:Messages/a:LogMessage", namespace)

    return LogMessage(lastMessage)


def GetNotification(message: str) -> [EmployeePassageNotification]:
    """
    Обработка полученного сообщения от сервера
    :param message:
    :return:
    """
    namespace = get_namespaces(message)

    notify = fromstring(message).find(
        "s:Body/{http://www.rusguardsecurity.ru}GetNotificationResponse/{http://www.rusguardsecurity.ru}GetNotificationResult",
        namespace
    )

    PassageNotifications = notify.findall("a:EmployeePassageNotifications/a:EmployeePassageNotification", namespace)
    EmployeePassageNotifications = []

    for item in PassageNotifications:
        EmployeePassageNotifications.append(
            EmployeePassageNotification(item)
        )
    return EmployeePassageNotifications


def GetAcsEmployeePhoto(message: str):
    """
    Обработка ответа от сервера, получение фотографии владельца карты доступа
    :param message:
    :return:
    """

    namespace = get_namespaces(message)

    photo_element = fromstring(message).find(
        "s:Body/{http://www.rusguardsecurity.ru}GetAcsEmployeePhotoResponse/"
        "{http://www.rusguardsecurity.ru}GetAcsEmployeePhotoResult",
        namespace
    )
    photo = photo_element.text

    return photo


def GetFilteredEvents(message: str):
    """
    Получаем объект эвентов сервера
    :param message: XML документ с сервера
    :return: Список сообщений
    """
    namespace = get_namespaces(message)
    events = fromstring(message).find(
        "s:Body/{http://www.rusguardsecurity.ru}GetFilteredEventsResponse/"
        "{http://www.rusguardsecurity.ru}GetFilteredEventsResult",
        namespace
    )
    list_messages = Messages(events, namespace)
    return list_messages.LogMessages
