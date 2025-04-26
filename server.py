from socket import *
import sys
from threading import Thread
import queue
from functions import *

client_handlers = {}  # addr -> Queue
active_users = {}

# Check arguments
if len(sys.argv) != 2:
    print("\nError usage, python server.py SERVER_PORT\n")
    exit(0)

serverPort = int(sys.argv[1])  # Server IP add
serverAddress = ('127.0.0.1', serverPort)

# Define UDP!!!! server socket
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(serverAddress)

print("\nWaiting for clients :)\n")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION FOR LOGGING IN ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def process_login():
    username_data, address = serverSocket.recvfrom(2048)
    username = username_data.decode().strip()

    serverSocket.sendto(f"ACK:{username}".encode(), address)

    if username in active_users:
        serverSocket.sendto(f"Error! {username} already logged in\n".encode(), address)
        print(f"Error! {username} already logged in\n")
        return False
    else:
        serverSocket.sendto(f"Authenticating client {username}.\n".encode(), address)


    password_data, addr = serverSocket.recvfrom(2048)
    received_password = password_data.decode().strip()

    serverSocket.sendto(f"ACK:{received_password}".encode(), addr)

    stored_password = None
    with open("credentials.txt", "r") as f:
        for line in f:
            parts = line.strip().split()
            stored_username = parts[0]
            if username == stored_username:
                stored_username, password = parts
                stored_password = password
                # print(f"Password on file: {stored_password}")
                break

    if stored_password is not None:
        if received_password == stored_password:
            serverSocket.sendto("Welcome!".encode(), address)
        else:
            serverSocket.sendto("Error! Incorrect Password.\n".encode(), address)
            print("Incorrect password.\n")
            return False
    else:
        with open("credentials.txt", "a") as f:
            f.write(f"\n{username} {received_password}")
        serverSocket.sendto("Welcome!".encode(), address)

    active_users[username] = addr
    print(f"{username} logged in successfully\n") 
    return username


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~ THE HANDLER OF INDIVIDUAL CLIENTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def client_handler():
    while True:
        msg, addr = serverSocket.recvfrom(2048)

        # xcheck if this address is logged in
        if addr not in client_handlers:
            print(f"!!! New client entered.")

            username = process_login()
            while not username:
                username = process_login()


            # successful login!!!
            # create a queue and thread a
            q = queue.Queue()
            client_handlers[addr] = q
            active_users[username] = addr

            # Start command processing thread
            Thread(target=process_command, args=(serverSocket, q, addr, client_handlers, active_users)).start()

        else:
            client_handlers[addr].put(msg)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    print("🌐 Server listening on port", serverPort)
    Thread(target=client_handler).start()
    
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~