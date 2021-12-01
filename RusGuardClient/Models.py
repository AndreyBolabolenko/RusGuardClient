from xml.etree.ElementTree import Element


class LogMessage:
    ContentData = str
    ContentType = str

    DateTime = str

    Details = str
    DriverID = str
    DriverName = str

    EmployeeID = str
    EmployeeFirstName = str
    EmployeeLastName = str
    EmployeeSecondName = str

    EmployeeGroupId = str
    EmployeeGroupFullName = str
    EmployeeGroupName = str

    Id = int

    LogMessageSubType = str
    LogMessageType = str

    Message = str

    OperatorFullName = str
    OperatorID = str
    OperatorLogin = str

    ServerId = str
    ServerName = str

    def __init__(self, document=None):
        if isinstance(document, Element):
            url = "http://schemas.datacontract.org/2004/07/VVIInvestment.RusGuard.DAL.Entities.Entity.Log"
            try:
                for element in document:
                    element_tag = element.tag.replace("{"+url+"}", "")
                    setattr(self, element_tag, element.text)
            except Exception:
                raise TypeError("type xml.etree.ElementTree.Element only")


class Messages:
    def __init__(self, document=None, namespace=None):
        self.LogMessages = []  # type:[LogMessage]
        if isinstance(document, Element):
            try:
                result = document.find("a:Messages", namespace)
                for element_message in result:
                    self.LogMessages.append(LogMessage(element_message))

            except Exception:
                raise TypeError("type xml.etree.ElementTree.Element only")


class AdditionalFieldInfo:
    FieldType = str
    ID = str
    IsNotForShow = str
    IsRequired = str
    Name = str
    Order = str
    OwnerType = str
    DefaultValue = str

    def __init__(self, document, namespace):
        if isinstance(document, Element):
            try:
                for key in document:
                    key_tag = key.tag.replace("{" + namespace['b'] + "}", "")
                    setattr(self, key_tag, key.text)

            except Exception:
                raise TypeError("type xml.etree.ElementTree.Element only")


class EmployeePassageNotification:
    Data = str

    DateTime = str
    Details = str
    DriverId = str
    EmployeeId = str
    IsKeyEvent = str
    LogMessageId = str

    Message = str
    MessageSubType = str
    MessageType = str
    OperatorId = str

    AddFields = [AdditionalFieldInfo]

    EmployeeFirstName = str
    EmployeeLastName = str
    EmployeeSecondName = str

    EmployeePosition = str

    EmployeeGroupFullPath = str

    __namespace = {
        'b': "http://schemas.datacontract.org/2004/07/VVIInvestment.RusGuard.DAL.Entities.Entity.AdditionalFields",
        'a': "http://schemas.datacontract.org/2004/07/VVIInvestment.RusGuard.DAL.Entities.Notifications"
    }

    def __init__(self, document=None):
        self.AddFields = []
        if isinstance(document, Element):
            try:
                for key in document:
                    key_tag = key.tag.replace("{"+self.__namespace['a']+"}", "")

                    if key_tag == "AddFields":
                        fields = key.findall('b:Fields/b:AdditionalFieldValue/b:AdditionalFieldInfo', self.__namespace)
                        for field in fields:
                            self.AddFields.append(AdditionalFieldInfo(field, self.__namespace))
                        continue

                    setattr(self, key_tag, key.text)

            except Exception:
                raise TypeError("type xml.etree.ElementTree.Element only")


class LogMessageTypeSlimInfo:
    LogMesssageType = str
    Name = str
    OrderNumber = int
    Publish = bool

    _namespace = "http://schemas.datacontract.org/2004/07/VVIInvestment.RusGuard.DAL.Entities.Entity.Log"

    def __init__(self, document):
        if isinstance(document, Element):
            try:
                for element in document:
                    tag = element.tag.replace("{"+self._namespace+"}", "")
                    setattr(self, tag, element.text)

            except Exception:
                raise TypeError("type xml.etree.ElementTree.Element only")


class LogMessageSubtypeSlimInfo:
    LogMessageSubtype = str
    LogMesssageType = str
    Name = str
    OrderNumber = int
    Publish = bool

    _namespace = "http://schemas.datacontract.org/2004/07/VVIInvestment.RusGuard.DAL.Entities.Entity.Log"

    def __init__(self, document):
        if isinstance(document, Element):
            try:
                for element in document:
                    tag = element.tag.replace("{"+self._namespace+"}", "")
                    setattr(self, tag, element.text)
            except Exception:
                raise TypeError("type xml.etree.ElementTree.Element only")


class LNetInfo:
    GatewayUrl: str
    Id = str
    IsAttached = bool

    _namespace = "http://schemas.datacontract.org/2004/07/VVIInvestment.RusGuard.DAL.Entities.Entity"

    def __init__(self, document):
        if isinstance(document, Element):
            try:
                for element in document:
                    tag = element.tag.replace("{"+self._namespace+"}", "")
                    setattr(self, tag, element.text)
            except Exception:
                raise TypeError("type xml.etree.ElementTree.Element only")


class LServerInfo:
    Id = str
    IdNet = str
    IsAttached = str
    ServerType = str
    Url = str

    _namespace = "http://schemas.datacontract.org/2004/07/VVIInvestment.RusGuard.DAL.Entities.Entity"

    def __init__(self, document):
        if isinstance(document, Element):
            try:
                for element in document:
                    tag = element.tag.replace("{"+self._namespace+"}", "")
                    setattr(self, tag, element.text)
            except Exception:
                raise TypeError("type xml.etree.ElementTree.Element only")


class LDriverFullInfo:
    DeviceServerId = str
    Id = str
    ParentId = str

    DriverType = str

    IsActive = bool
    IsUnknownID = bool

    Name = str
    ParentPropertyName = str

    Properties = None

    State = str
    States = None

    _namespace = "http://schemas.datacontract.org/2004/07/VVIInvestment.RusGuard.DAL.Entities.Entity"

    def __init__(self, document):
        if isinstance(document, Element):
            self.Properties = {}
            self.States = {}
            for element in document:
                tag = element.tag.replace("{"+self._namespace+"}", "")

                if tag == "Properties":
                    for sub_element in element:
                        key = sub_element.find("{"+self._namespace+"}PropertyName").text
                        value = sub_element.find("{"+self._namespace+"}Value").text
                        self.Properties[key] = value
                    continue

                if tag == "States":
                    for sub_element in element:
                        key = sub_element.find("{"+self._namespace+"}PropertyName").text
                        value = sub_element.find("{"+self._namespace+"}Value").text
                        self.States[key] = value
                    continue

                setattr(self, tag, element.text)
