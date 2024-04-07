import socket
import threading
import requests
from datetime import datetime
from threading import Thread


HEADER = 64  # A fixed-length message header of 64 bytes.
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "clt-disconnect"


class ThreadedClientHandler(Thread):
	def __init__(self, connection, address):
		Thread.__init__(self)
		self.connection = connection
		self.address = address
		self.start()

		print(f"[CURRENT ACTIVE CONNECTIONS]: {threading.activeCount() - 1} connections.")


	def message_from_server(self, message):
		self.connection.send(f"SERVER: {message.encode(FORMAT)}")


	def run(self):
		now = datetime.now()
		print(f"[NEW CONNECTION INBOUND - {now:%B %d, %Y - %H:%M:%S}]: {self.address} connected.")
		self.message_from_server("----- Connected to Server -----")

		connected = True
		while connected:
			msg_length = self.connection.recv(HEADER).decode(FORMAT)
			
			if msg_length:
				msg_length = int(msg_length)
				msg = self.connection.recv(msg_length).decode(FORMAT)
				now = datetime.now()

				if msg == DISCONNECT_MESSAGE:
					print(f"[{self.address} - Client Disconnected At {now:%H:%M:%S}]")
					self.message_from_server("----- Disconnected -----")
					connected = False
				else:
					print(f"[{self.address} - At {now:%H:%M:%S}]: {msg}")
					self.message_from_server("----- Message Received -----")

		self.connection.close()


class SocketServer:
	def __init__(self):
		# Get the address of a network interface used for internet access.
		checker_sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		checker_sk.connect(("8.8.8.8", 80))

		self.port = 5050  # Internal port.
		self.ip = checker_sk.getsockname()[0]  # Get the IP address.
		self.address = (self.ip, self.port)
		self.clients = set()

		checker_sk.close()


	def get_public_ip(self):
		try:
			response = requests.get("https://httpbin.org/ip")
			if response.status_code == 200:
				response_json = response.json()
				return response_json["origin"]
			else:
				print(f"Failed to retrieve IP - Status Code: {response.status_code}")
		except Exception as e:
			print(f"An Error occurs: {e}")


	def broadcast(self, message):
		for client in self.clients:
			client.message_from_server(message)


	def start_server(self):
		print("[GREETING]: Welcome to Socket with Python, stranger.")
		print("[STARTING]: Server is starting...")

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
			server.bind(self.address)

			# Start listening for new connections.
			server.listen()
			print(f"[LISTENING]: Server is listening for connections on {self.ip} - port: {self.port}")

			try:
				while True:
					connection, address = server.accept()
					if connection != None:
						self.clients.add(ThreadedClientHandler(connection, address))

					message = input("Enter broadcast message: ").strip()
					if message != "":
						self.broadcast(message)
			finally:
				self.clients.clear()


server = SocketServer()
print(server.get_public_ip())
server.start_server()