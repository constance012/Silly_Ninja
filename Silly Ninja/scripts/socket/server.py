import threading
import socket
import time

from datetime import datetime
from scripts.socket.client import ClientDisconnectException, MAX_CLIENT_COUNT

FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!leave"


class SocketServer:
	def __init__(self, ip, port):
		# Get the IP address of RadminVPN.
		self.ip = ip
		self.port = int(port)  # Internal port.

		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.clients = []
		self.nicknames = []
		self.running = True
		self.is_shutdown = False


	def shutdown(self):
		print(f"[SHUTTING DOWN]: Server is about to shut down, disconnect all clients.")
		self.running = False
		self.is_shutdown = True

		# Close all connection to clients.
		for client in self.clients:
			client.send(DISCONNECT_MESSAGE.encode(FORMAT))
			client.close()

		self.clients.clear()
		self.nicknames.clear()
		self.server.close()


	def client_count(self):
		return len(self.clients)


	def get_nickname_at(self, index):
		return self.nicknames[index]


	def broadcast(self, message):
		for client in self.clients:
			client.send(message.encode(FORMAT))


	# A method to handle each client, on each separated thread.
	def handle_client(self, client, address):
		while self.running:
			try:
				message = client.recv(1024).decode(FORMAT)
				if message.split(": ", 1)[1] == DISCONNECT_MESSAGE:
					raise ClientDisconnectException("Client disconnected.")
				else:
					self.broadcast(message)
			except Exception:
				if not self.is_shutdown:
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

		self.server.bind((self.ip, self.port))
		print(f"[LISTENING]: Server is listening for connections on {self.ip} - port: {self.port}")
		self.server.listen()

		self.running = True
		self.is_shutdown = False
		while self.running:
			client, address = self.server.accept()
			now = datetime.now()

			if len(self.clients) < MAX_CLIENT_COUNT:
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

				threading.Thread(target=self.handle_client, args=(client, address)).start()
			else:
				client.send(("[JOIN FAILED]: Connected successfully but the maximum number of clients has been reached. " +
							"Hence CAN NOT join the game.").encode(FORMAT))
				time.sleep(1)
				client.send(DISCONNECT_MESSAGE.encode(FORMAT))
				client.close()


class GameServer(SocketServer):
	def __init__(self, ip, port):
		super().__init__(ip, port)
		self.clients = {}
		self.client_ids = []
		self.client_sockets = []


	def client_count(self):
		return len(self.clients)


	def shutdown(self):
		print(f"[SHUTTING DOWN]: Server is about to shut down, disconnect all clients.")
		self.running = False
		self.is_shutdown = True
		
		# Close all connections to clients.
		for client_id in self.clients:
			self.clients[client_id].send(DISCONNECT_MESSAGE.encode(FORMAT))
			self.clients[client_id].close()

		self.clients.clear()
		self.nicknames.clear()
		self.server.close()


	def broadcast(self, sender_id, message):
		# Broadcast the message to all connected clients, except the sender.
		# Send to all clients if the message starts with an asterisk.
		sendall = False
		if message.startswith("*"):
			sendall = True
			message = message[1:]

		for client_id in self.clients:
			if client_id != sender_id or sendall:
				self.clients[client_id].send(message.encode(FORMAT))


	def remove_client(self, address, removed_id, removed_index):
		self.clients.pop(removed_id)
		
		nickname = self.nicknames[removed_index]
		print(f"[LEAVING]: {address} a.k.a \"{nickname}\" has left the game.")
		self.nicknames.remove(nickname)
		print(self.nicknames)
		
		self.broadcast(removed_id, f"PLAYER LEFT:{removed_index}|")
		
		""" Sort other clients up only if the removed the client is not the host
		or the most recently connected one. """
		if removed_index in range(1, MAX_CLIENT_COUNT - 1):
			for i in range(removed_index, MAX_CLIENT_COUNT):
				next_id = f"client_{i + 1}"
				if next_id in self.clients:
					next = self.clients.pop(next_id, None)
					if next is not None:
						self.clients[f"client_{i}"] = next

			self.client_ids = list(self.clients.keys())
			self.client_sockets = list(self.clients.values())

			index = 0
			names = ','.join(self.nicknames)
			ids = ','.join(self.client_ids)
			for client_id in self.clients:
				self.clients[client_id].send(f"RE_INITIALIZE:{index};{client_id};{names};{ids}|".encode(FORMAT))
				index += 1


	def handle_client(self, client, address):
		while self.running:
			try:
				message = client.recv(1024).decode(FORMAT)
				client_index = self.client_sockets.index(client)
				client_id = self.client_ids[client_index]

				if message == DISCONNECT_MESSAGE:
					raise ClientDisconnectException("Client disconnected.")
				else:
					self.broadcast(client_id, message)
			except Exception:
				if not self.is_shutdown:
					self.remove_client(address, client_id, client_index)
				break


	def accept_client(self, client, address, time):
		print(f"[NEW CONNECTION INBOUND - {time: %B %d, %Y - %H:%M:%S}]: {address} connected.")

		# Send a keyword that asks the client to send their nickname and id.
		client.send("[NICKNAME]".encode(FORMAT))
		nickname = client.recv(1024).decode(FORMAT)
		self.nicknames.append(nickname)
		print(self.nicknames)

		client.send("[CLIENT ID]".encode(FORMAT))
		client_id = client.recv(1024).decode(FORMAT)

		if client_id == "client_unverified":
			client_id = f"client_{self.nicknames.index(nickname)}"

		self.clients[client_id] = client
		self.client_ids = list(self.clients.keys())
		self.client_sockets = list(self.clients.values())

		print(f"[JOINED]: {address} joined the game as \"{nickname}\".")
		
		client_index = self.client_count() - 1
		print(f"Client Count: {self.client_count()}")
		print(f"Index for {nickname}: {client_index}")
		self.broadcast(client_id, f"*NEW PLAYERS JOINED:{client_index};{client_id};" +
								f"{','.join(self.nicknames)};" +
								f"{','.join(self.client_ids)}|")

		threading.Thread(target=self.handle_client, args=(client, address)).start()


	def start_server(self):
		print("[GREETING]: Welcome to Socket with Python, stranger.")
		print("[STARTING]: Server is starting...")

		self.server.bind((self.ip, self.port))
		print(f"[LISTENING]: Server is listening for connections on {self.ip} - port: {self.port}")
		self.server.listen()
		
		self.running = True
		self.is_shutdown = False
		while self.running:
			try:
				client, address = self.server.accept()
				now = datetime.now()

				if self.client_count() < MAX_CLIENT_COUNT:
					self.accept_client(client, address, now)
				else:
					client.send(("[JOIN FAILED]: Connected successfully but the maximum number of clients has been reached. " +
								"Hence CAN NOT join the game.").encode(FORMAT))
					time.sleep(1)
					client.send(DISCONNECT_MESSAGE.encode(FORMAT))
					client.close()
			except Exception:
				print("[SHUTDOWN]: Server shutdown successfully.")


if __name__ == "__main__":
	ip = socket.gethostbyname(socket.gethostname())
	port = 5050
	SocketServer(ip, port).start_server()