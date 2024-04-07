import socket

HEADER = 64
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "clt-disconnect"

class Client:
	def __init__(self):
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_ip = ""
		self.port = 5050
		self.address = ()

	def send_message(self, msg):
		send_message = msg.encode(FORMAT)
		send_length = str(len(send_message)).encode(FORMAT)

		# Pad the message with "blank" bytes to match the HEADER size.
		send_length += b" " * (HEADER - len(send_length))
		self.client_socket.send(send_length)
		self.client_socket.send(send_message)
		print(self.client_socket.recv(2048).decode(FORMAT))


	def start(self):
		while True:
			connection_scope = input("Enter connection scope (\"Local\" or \"Public\"): ").strip().lower()
			if connection_scope != "local" and connection_scope != "public":
				print("[ERROR]: Please enter a valid scope (\"Local\" or \"Public\").")
			else:
				break

		while True:
			try:
				self.server_ip = input(F"Enter server's {connection_scope} IP: ").strip()
				self.port = int(input("Enter port number.\n(DEFAULT: '5050' for local connection, '5001' for public connection): ").strip())
				self.server_address = (self.server_ip, self.port)
				break
			except ValueError:
				print("[ERROR]: Port number must be an integer.")

		try:
			print("[CONNECTING]: Attempting to connect to Server...")
			self.client_socket.connect(self.server_address)
			print(self.client_socket.recv(2048).decode(FORMAT))

			while True:
				message = input("Enter message: ").strip()
				if message != "":
					self.send_message(message)
				if message == DISCONNECT_MESSAGE:
					break
		except ConnectionRefusedError:
			print("[ERROR]: Connect failed, please check the server's IP and Port, then try again.")
		except ConnectionResetError:
			print("[ERROR]: Connection disrupted, possibly due to a forcibly closed session from the server side or network error.")
		finally:
			self.client_socket.close()


if __name__ == "__main__":
	Client().start()