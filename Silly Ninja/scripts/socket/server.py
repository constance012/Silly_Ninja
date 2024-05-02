import threading
import socket
import requests
from datetime import datetime

FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!leave"


class ClientDisconnectException(Exception):
	pass


class SocketServer:
	def __init__(self, ip, port):
		# Get the IP address of RadminVPN.
		self.ip = ip
		self.port = port  # Internal port.
		self.clients = []
		self.nicknames = []


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
			client.send(message.encode(FORMAT))


	# A method to handle each client, on each separated thread.
	def handle(self, client, address):
		while True:
			try:
				message = client.recv(1024).decode(FORMAT)
				if message.split(": ", 1)[1] == DISCONNECT_MESSAGE:
					raise ClientDisconnectException("Client disconnected.")
				else:
					self.broadcast(message)
			except Exception:
				index = self.clients.index(client)
				client.send(DISCONNECT_MESSAGE.encode(FORMAT))
				self.clients.remove(client)
				client.close()
				nickname = self.nicknames[index]
				print(f"[LEAVING]: {address} a.k.a \"{nickname}\" has left the chat.")
				self.broadcast(f"[LEAVING]: {nickname} has left the chat.")
				self.nicknames.remove(nickname)
				break


	def start_server(self):
		print("[GREETING]: Welcome to Socket with Python, stranger.")
		# print(f"[PUBLIC IP]: {self.get_public_ip()}")
		print("[STARTING]: Server is starting...")

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
			server.bind((self.ip, self.port))
			print(f"[LISTENING]: Server is listening for connections on {self.ip} - port: {self.port}")
			server.listen()

			while True:
				client, address = server.accept()
				now = datetime.now()
				print(f"[NEW CONNECTION INBOUND - {now: %B %d, %Y - %H:%M:%S}]: {address} connected.")

				# Send a keyword that asks the client to enter their nickname.
				client.send("NICKNAME".encode(FORMAT))
				nickname = client.recv(1024).decode(FORMAT)
				self.nicknames.append(nickname)
				self.clients.append(client)

				print(f"[JOINING]: {address} joined the chat as {nickname}.")
				self.broadcast(f"[JOINING]: {nickname} joined the chat!")
				client.send((f"[CONNECTED]: Welcome to the Chat Room, {nickname}!\n" +
							"[RECEIVING INPUT]: Now, you can enter messages and send them to other people.").encode(FORMAT))

				threading.Thread(target=self.handle, args=(client, address)).start()


if __name__ == "__main__":
	ip = socket.gethostbyname(socket.gethostname())
	port = 5050
	SocketServer(ip, port).start_server()