import base64
import logging
import asyncio
from pathlib import Path
from datetime import datetime as dt
from datetime import timedelta

from RusGuardClient.ANetwork import AsyncNetworkClient
from RusGuardClient.Models import EmployeePassageNotification, LogMessage


async def notification():
    while True:
        try:
            result = await Client.get_notification()
            for item in result:  # type: EmployeePassageNotification
                photo = await Client.get_employee_photo(item.EmployeeId)
                logging.info(f"{item.EmployeeFirstName} {item.EmployeeLastName} - {item.Message}")

                # logging.info("[NOTIF](%s) %s %s", item.EmployeeId, item.Message, item.Details)
        except TimeoutError:
            continue


async def logger():
    event = await Client.get_last_event()
    last_event_id = event.Id

    while True:
        try:
            Message = await Client.get_events(int(last_event_id))
            for item in Message:  # type: LogMessage
                if last_event_id < item.Id:
                    last_event_id = item.Id

                logging.info("(%s) %s %s", item.Id, item.Message, item.Details)
            await asyncio.sleep(1)
            del Message
        except KeyboardInterrupt:
            break


async def loop():
    tasks = [
        notification(),
        logger()
    ]

    await asyncio.gather(*tasks)


def enter_events(uID, message):
    enter_message = message
    # enter_message = Client.get_filtered_events("AccessPointEntryByKey")
    uID = uID.lower()

    last_enter = None

    for element in enter_message:
        if element.EmployeeID == uID:
            if last_enter is None:
                if element.Message == "Вход":
                    last_enter = element

            if element.Message == "Вход":
                date_current = dt.strptime(last_enter.DateTime, "%Y-%m-%dT%H:%M:%S")
                date_item = dt.strptime(element.DateTime, "%Y-%m-%dT%H:%M:%S")
                if date_current > date_item:
                    last_enter = element

    return last_enter


def exit_events(uID, message):
    enter_message = message
    # enter_message = Client.get_filtered_events("AccessPointExitByKey")
    uID = uID.lower()

    last_exit = None

    for element in enter_message:
        if element.EmployeeID == uID:
            if last_exit is None:
                if element.Message == "Выход":
                    last_exit = element

            if element.Message == "Выход":
                date_current = dt.strptime(last_exit.DateTime, "%Y-%m-%dT%H:%M:%S")
                date_item = dt.strptime(element.DateTime, "%Y-%m-%dT%H:%M:%S")
                if date_current < date_item:
                    last_exit = element

    return last_exit

if __name__ == '__main__':
    main_loop = asyncio.get_event_loop()
    Client = AsyncNetworkClient("acs1.osetrovo.int", 'dmhf', 'C373oa97rus')
    # Client = AsyncNetworkClient("10.0.20.21", 'dmhf', 'C373oa97rus')
    Client.get_version()
    employees = []

    with open("data", 'r', encoding='utf-8') as file:
        for line in file.readlines():
            employees.append(line.strip().split("	")[0:4])

    employees = employees[1::]

    empl = {}

    for date in range(15,16):
        if date < 10:
            date = f"0{date}"

        print(f"2021-10-{date}")
        enter_msg = Client.get_filtered_events("AccessPointEntryByKey", date)
        exit_msg = Client.get_filtered_events("AccessPointExitByKey", date)

        for employee in employees:
            uID, FirstName, LastName, MiddleName = employee
            empl[uID] = {
                'enter': None,  # type: LogMessage
                'exit': None  # type: LogMessage
            }

            empl[uID]['enter'] = enter_events(uID, enter_msg)  # type: LogMessage
            empl[uID]['exit'] = exit_events(uID, exit_msg) # type: LogMessage

            if empl[uID]['enter'] is None and empl[uID]['exit'] is None:
                print(f"{FirstName},{LastName},{MiddleName},--:--,--:--")
            elif empl[uID]['enter'] is None:
                print(f"{FirstName},{LastName},{MiddleName},--:--,{empl[uID]['exit'].DateTime}")
            elif empl[uID]['exit'] is None:
                print(f"{FirstName},{LastName},{MiddleName},{empl[uID]['enter'].DateTime},--:--")
            else:
                print(f"{FirstName},{LastName},{MiddleName},{empl[uID]['enter'].DateTime},{empl[uID]['exit'].DateTime}")

        print("")

    # main_loop.run_until_complete(loop())

    Client.disconnect()