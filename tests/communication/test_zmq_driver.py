# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from concurrent.futures import ThreadPoolExecutor, as_completed
import unittest
import os

from maro.communication import ZmqDriver, SessionMessage


def message_receive(driver):
    for received_message in driver.receive(is_continuous=False):
        return received_message.payload

@unittest.skipUnless(os.environ.get("test_with_zmq", False), "require zmq")
class TestDriver(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        print(f"The ZMQ driver unit test start!")
        cls.peer_list = ["receiver_1", "receiver_2", "receiver_3"]
        # send driver
        cls.sender = ZmqDriver()
        sender_address = cls.sender.address

        # receive drivers
        cls.receivers = {}
        receiver_addresses = {}
        for peer in cls.peer_list:
            peer_driver = ZmqDriver()
            peer_driver.connect({"sender": sender_address})
            cls.receivers[peer] = peer_driver
            receiver_addresses[peer] = peer_driver.address

        cls.sender.connect(receiver_addresses)

    @classmethod
    def tearDownClass(cls) -> None:
        print(f"The ZMQ driver unit test finished!")

    def test_send(self):
        for peer in self.peer_list:
            message = SessionMessage(tag="unit_test",
                                     source="sender",
                                     destination=peer,
                                     payload="hello_world")
            self.sender.send(message)

            for received_message in self.receivers[peer].receive(is_continuous=False):
                self.assertEqual(received_message.payload, message.payload)

    def test_broadcast(self):
        executor = ThreadPoolExecutor(max_workers=len(self.peer_list))
        all_task = [executor.submit(message_receive, (self.receivers[peer])) for peer in self.peer_list]

        message = SessionMessage(tag="unit_test",
                                 source="sender",
                                 destination="*",
                                 payload="hello_world")
        self.sender.broadcast(message)

        for task in as_completed(all_task):
            res = task.result()
            self.assertEqual(res, message.payload)


if __name__ == "__main__":
    unittest.main()
