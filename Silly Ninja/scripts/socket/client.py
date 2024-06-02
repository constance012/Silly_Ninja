import socket
import threading
import traceback
import time
import os
import pygame


FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!leave"
MAX_CLIENT_COUNT = 4
BUFFER_SIZE = 1024
os.system("")  # Enable ANSI escape characters in terminal.


def recvall(socket):
	try:
		data = b""
		while True:
			segment = socket.recv(BUFFER_SIZE)
			data += segment
			if len(segment) < BUFFER_SIZE:
				break
		return data
	except (ConnectionError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError):
		print("[CLOSED]: Server has shutdown.")
		return b""
	except Exception:
		print(f"[ERROR]: An error occurred when trying to disconnect from the server.\n{traceback.format_exc()}")
		return b""


class ClientDisconnectException(Exception):
	pass


class ChatClient:
	def __init__(self, ip="", port=5050, nickname="Default_Client"):
		self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_ip = ip
		self.port = port
		self.nickname = nickname
		self.running = True


	def receive(self):
		while self.running:
			try:
				message = recvall(self.client_socket).decode(FORMAT)
				if message == "NICKNAME":
					self.client_socket.send(self.nickname.encode(FORMAT))
				elif message == DISCONNECT_MESSAGE:
					raise ClientDisconnectException("You have disconnected from the server.")
				else:
					print(message)
			
			except ClientDisconnectException as cde:
				self.running = False
				print(f"[DISCONNECTED]: {cde}")
				self.client_socket.close()
			
			except Exception:
				self.running = False
				print(f"[ERROR]: An unexpected error occurred!\n{traceback.format_exc()}")
				self.client_socket.close()


	def send(self):
		while self.running:
			try:
				user_input = input().strip()
				message = f"{self.nickname}: {user_input}"
				print("\033[1A" + "\033[K", end='')  # Clear the submitted input line using ANSI escape characters.
				self.client_socket.send(message.encode(FORMAT))
				
				if user_input == DISCONNECT_MESSAGE:
					raise ClientDisconnectException("Closing connection...")
			
			except ClientDisconnectException as cde:
				self.running = False
				print(f"[DISCONNECTING]: {cde}")
				self.client_socket.close()

			except Exception:
				self.running = False
				print(f"[ERROR]: An unexpected error occurred!\n{traceback.format_exc()}")
				self.client_socket.close()


	def send_manually(self, message):
		self.client_socket.send(str(message).encode(FORMAT))


	def connect(self):
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
				break
			
			except ValueError:
				print("[ERROR]: Port number must be an integer.")

		try:
			self.nickname = input("Choose a nickname: ")
			print(f"[CONNECTING]: Attempting to connect to Server ({self.server_ip} - port {self.port})...")
			self.client_socket.connect((self.server_ip, self.port))

			threading.Thread(target=self.receive).start()
			threading.Thread(target=self.send).start()
		
		except ConnectionRefusedError:
			print("[ERROR]: Connect failed, please check the server's IP and Port, then try again.")
			print(traceback.format_exc())
			self.client_socket.close()
		
		except (ConnectionResetError, ConnectionAbortedError):
			print("[ERROR]: Connection disrupted, possibly due to a forcibly closed session from the server side or network error.")
			print(traceback.format_exc())
			self.client_socket.close()


class GameClient(ChatClient):
	def __init__(self, game, client_id, ip="", port=5050, nickname="Default_Client"):
		super().__init__(ip=ip, port=port, nickname=nickname)
		self.game = game
		self.entities = game.entities  # A list of entities to update.
		self.tilemap = game.tilemap

		self.fps = 60
		self.clock = pygame.time.Clock()

		self.client_id = client_id  # Host, Client1, Client2,...
		self.client_index = -1
		self.game_started = False


	def disconnect(self):
		if self.running:
			try:
				print(f"[DISCONNECTING]: You have disconnected from the server.")
				self.running = False
				self.game_started = False
				time.sleep(0.1)
				self.client_socket.send(DISCONNECT_MESSAGE.encode(FORMAT))
				self.client_socket.close()
			except (ConnectionError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError):
				print("[CLOSED]: Server has shutdown.")
			except Exception:
				print(f"[ERROR]: An error occurred when trying to disconnect from the server.\n{traceback.format_exc()}")


	def update_entity(self, sender_id, infos):
		# Only update other clients' players and enemies.
		for entity in self.entities.copy():
			if entity.id == infos[0]:
				# [player_ID, last_movement[0], last_movement[1], pos[0], pos[1], dashing, jump, is_dead]
				if entity.type == "player":
					#print(f"{self.client_id} updating player: {entity.id}")
					entity.dashing = int(infos[5])
					entity.died = infos[7] == "True"
					entity.update(self.tilemap, movement=tuple(map(int, infos[1:3])), override_pos=tuple(map(float, infos[3:5])))
					if infos[6] == "True":
						entity.jump()
				
				elif entity.type == "enemy" and sender_id == "host":
					# [enemy_ID, walking, facing_left]
					dead = entity.update(self.tilemap, walking=int(infos[1]), facing_left=infos[2] == "True")
					if dead:
						self.entities.remove(entity)
				return


	def receive(self):
		while self.running:
			try:
				message = recvall(self.client_socket).decode(FORMAT)
				#print(f"RECEIVED: {message}")
				message = message.split("|")[0]

				if message == DISCONNECT_MESSAGE:
					raise ClientDisconnectException()
				elif message == "[NICKNAME]":
					self.client_socket.send(self.nickname.encode(FORMAT))
				elif message == "[CLIENT ID]":
					self.client_socket.send(self.client_id.encode(FORMAT))
				elif message == "[START GAME]":
					self.game.start_game()
				elif "PLAYER READY" in message:
					self.game.ready_for_launch()

				elif "SYNCED MAP" in message:
					self.game.sync_map(message.split("::")[1])
				
				elif "NEW PLAYERS JOINED" in message:
					# [str(index), str(client_id), str(nicknames), str(client_ids)]
					player_infos = message.split(":")[1].split(";")
					index = int(player_infos[0])

					if self.client_index == -1:
						self.client_index = index
						self.client_id = player_infos[1]

					# [int(index), str(client_id), list(nicknames), list(client_ids)]
					self.game.on_connection_made(index, player_infos[2].split(","), player_infos[3].split(","))
					
				elif "PLAYER LEFT" in message:
					player_index = int(message.split(":")[1])
					self.entities[player_index].unregister_client(player_index)

				elif "RE_INITIALIZE" in message:
					# [str(index), str(client_id), str(nicknames), str(client_ids)]
					infos = message.split(":")[1].split(";")
					index = int(infos[0])
					self.client_index = index
					self.client_id = infos[1]
					self.game.on_connection_made(index, infos[2].split(","), infos[3].split(","), re_initialized=True)
				
				elif self.game_started:
					message_segments = message.split(";")
					sender_id = message_segments[0]
					for segment in message_segments[1:]:
						infos = segment.split(",")
						self.update_entity(sender_id, infos)

				self.clock.tick(self.fps)
		
			except ClientDisconnectException:
				self.game.disconnect_from_server()
			
			except (ConnectionError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError):
				print("[INTERRUPTED]: Connection has been interrupted. Disconnecting...")
				self.game.disconnect_from_server()

			except Exception:
				print(f"[ERROR]: An unexpected error occurred!\n{traceback.format_exc()}")
				self.game.disconnect_from_server()


	def send(self):
		while self.running:
			try:
				if self.game_started:
					message = [self.client_id]
					
					# Send info of both entity types if this is the host.
					# Otherwise only send info of the corresponding client's player.
					# [player_ID, last_movement[0], last_movement[1], pos[0], pos[1], dashing, jump, is_dead]
					main_player = self.game.get_main_player()
					message.append(f"player_{self.client_index + 1}," +
									f"{main_player.last_movement[0]},{main_player.last_movement[1]}," +
									f"{main_player.pos[0]:.1f},{main_player.pos[1]:.1f}," +
									f"{main_player.dashing}," +
									f"{main_player.jumped}," +
									f"{main_player.died}")

					if self.client_id == "host":
						for entity in self.entities[4:]:
							# [enemy_ID, walking, facing_left]
							message.append(f"{entity.id},{entity.walking},{entity.facing_left}")
							if entity.is_dead:
								self.entities.remove(entity)

					# Add a delimeter between each message to avoid duplication.
					message = f"{';'.join(message)}|"
					#print(f"SENT: {message}")
					self.client_socket.send(message.encode(FORMAT))

				self.clock.tick(self.fps)

			except (ConnectionError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError, AttributeError):
				print("[INTERRUPTED]: Connection has been interrupted. Disconnecting...")
				self.game.disconnect_from_server()

			except Exception:
				print(f"[ERROR]: An unexpected error occurred!\n{traceback.format_exc()}")
				self.game.disconnect_from_server()


	def connect(self):
		try:
			print(f"[CONNECTING]: Attempting to connect to Server ({self.server_ip} - port {self.port})...")
			self.client_socket.connect((self.server_ip, self.port))

			threading.Thread(target=self.receive).start()
			threading.Thread(target=self.send).start()

			return True
		
		except (ConnectionRefusedError, TimeoutError):
			print("[ERROR]: Connect failed, please check the server's IP and Port, then try again.")
			print(traceback.format_exc())
			self.game.disconnect_from_server()
		
		except (ConnectionResetError, ConnectionAbortedError):
			print("[ERROR]: Connection disrupted, possibly due to a forcibly closed session from the server side or network error.")
			print(traceback.format_exc())
			self.game.disconnect_from_server()


if __name__ == "__main__":
	ChatClient().connect()