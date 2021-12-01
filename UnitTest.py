import logging
import asyncio

from RusGuardClient.ANetwork import AsyncNetworkClient
from RusGuardClient.Models import *


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


if __name__ == '__main__':
    main_loop = asyncio.get_event_loop()
    Client = AsyncNetworkClient("acs1.osetrovo.int", 'dmhf', 'C373oa97rus')
    Client.get_version()

    servers = main_loop.run_until_complete(
        Client.get_net_servers()
    )

    server_id = ""

    for server in servers:  # type: LServerInfo
        if server.ServerType == "DeviceServer":
            server_id = server.Id

    response = main_loop.run_until_complete(
        Client.get_server_drivers_full_info(server_id)
    )

    for i in response:  # type: LDriverFullInfo

        if i.ParentPropertyName == "Controllers":
            print(f"\n{i.Name}")
            for state in i.States:
                print(f"    Параметр {state}: {i.States[state]}")
            print('')
            for y in i.Properties:
                print(f"    Установка {y}: {i.Properties[y]}")


    # main_loop.run_until_complete(loop())

    Client.disconnect()