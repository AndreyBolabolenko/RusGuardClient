import xml.dom.minidom
from datetime import datetime, timedelta


class xml_document:
    document = xml.dom.minidom.Document()

    header = None  # type: xml.dom.minidom.Element
    security = None  # type: xml.dom.minidom.Element
    body = None  # type: xml.dom.minidom.Element
    root = None  # type: xml.dom.minidom.Element

    def __init__(self):
        self.root = self.xml_root()
        self.header = self.document.createElement("s:Header")
        self.body = self.document.createElement("s:Body")
        self.security = self.xml_security()

    def xml_root(self) -> xml.dom.minidom.Element:
        """
        Создание главных заголовков XML файла
        :return: XML Document
        """
        root = self.document.createElementNS('http://schemas.xmlsoap.org/soap/envelope/', 's:Envelope')
        root.setAttribute('xmlns:s', "http://schemas.xmlsoap.org/soap/envelope/")
        root.setAttribute('xmlns:u',
                          "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd")

        return root

    def xml_security(self, mustUnderstand=1) -> xml.dom.minidom.Element:
        """
        Возвращает элемент документа Безопасности
        :param mustUnderstand:
        :return:
        """
        root = self.document.createElement('o:Security')
        root.setAttribute("xmlns:o",
                          "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd")
        root.setAttribute("s:mustUnderstand", str(mustUnderstand))
        return root

    def xml_timestamp(self, uId="_0") -> xml.dom.minidom.Element:
        """
        Возвращает дату создания документа и его время жизни
        :param uId:
        :return: XML Document
        """

        elements = self.security.getElementsByTagName("u:Timestamp")
        if len(elements) > 0:
            for item in elements: self.security.removeChild(item)

        root = self.document.createElement('u:Timestamp')
        root.setAttribute('u:Id', uId)

        currentDate = datetime.utcnow()
        expiresDate = currentDate + timedelta(minutes=5)

        created = self.document.createElement("u:Created")
        created.appendChild(
            self.document.createTextNode(
                currentDate.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            )
        )

        expires = self.document.createElement("u:Expires")
        expires.appendChild(
            self.document.createTextNode(
                expiresDate.strftime("%Y-%m-%dT%H:%M:%S.%f3Z")
            )
        )
        root.appendChild(created)
        root.appendChild(expires)

        self.security.appendChild(root)
        return root

    def xml_usernametoken(self, usrname, passwd, uId="") -> xml.dom.minidom.Element:
        """
        Возвращает документ с логином и паролем пользователя
        :param usrname: Имя пользователя
        :param passwd: Пароль
        :param uId:
        :return: XML Document
        """
        root = self.document.createElement('o:UsernameToken')
        root.setAttribute("u:Id", uId)

        username = self.document.createElement("o:Username")
        username.appendChild(self.document.createTextNode(usrname))

        password = self.document.createElement("o:Password")
        password.setAttribute("Type",
                              "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText")
        password.appendChild(self.document.createTextNode(passwd))

        root.appendChild(username)
        root.appendChild(password)
        self.security.appendChild(root)
        return root

    def xml_simple(self, element) -> xml.dom.minidom.Element:
        root = self.root

        header = self.header
        header.appendChild(self.security)

        root.appendChild(header)
        body = self.document.createElement("s:Body")

        body.appendChild(element)

        root.appendChild(body)
        del body, header
        return root

    def xml_method(self, element, attribute, node=None) -> xml.dom.minidom.Element:
        root = self.root

        header = self.header
        header.appendChild(self.security)

        root.appendChild(header)
        body = self.document.createElement("s:Body")

        method = self.document.createElement(element)
        for key in attribute:
            method.setAttribute(key, attribute[key])

        if not node is None:
            for item in node:
                method.appendChild(item)

        body.appendChild(method)

        root.appendChild(body)
        del body, header
        return root
