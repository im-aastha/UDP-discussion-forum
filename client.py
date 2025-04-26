from socket import *
import sys

if len(sys.argv) != 2:
    print("\n~~~~~~ Error usage, python3 TCPClient.py SERVER_IP SERVER_PORT ~~~~~~\n")
    exit(0)

serverPort = int(sys.argv[1])  # Server Port
serverAddress = ('127.0.0.1', serverPort)

# Define a UDP socket for the client side
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.sendto("Greetings".encode('utf-8'), serverAddress)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~THE FUNCTIONS~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# function for interacting with user at the time of login(authentication)
def userLogin():
    username = input("Enter your username: ")
    if not reliable_send(clientSocket, username, serverAddress):
        print("Failed to deliver username due to packet loss.")
        return False

    response, _ = clientSocket.recvfrom(2048)
    if response.decode() == f"Error! {username} already logged in\n":
        print(response.decode())
        return False

    
    password = input("Enter your password: ")
    if password == "":
        print("Enter valid password!")
        return False

    # clientSocket.sendto(password.encode('utf-8'), serverAddress)
    if not reliable_send(clientSocket, password, serverAddress):
        print("Failed to deliver password due to packet loss.")
        return False

    final_response, _ = clientSocket.recvfrom(2048)

    if final_response.decode() == "Welcome!":
        return username  # SUCCESS
    else:
        print(final_response.decode())
        print("Please try logging in again.\n")
    return False

# function for printing out all the options available
def display_menu():
    print("Please select one of the available commands:")
    print("crt - Create post")
    print("lst - List posts")
    print("msg - Message post")
    print("dlt - Delete post")
    print("rdt - Read post")
    print("edt - Edit post")
    print("upd - Update post")
    print("dwn - Download post")
    print("rmv - Remove post")
    print("xit - Exit the system")

# for dealing with losses
def reliable_send(sock, message, server_address, max_retries=5, timeout=1.0):
    sock.settimeout(timeout)

    for attempt in range(max_retries):
        sock.sendto(message.encode(), server_address)
        try:
            ack, _ = sock.recvfrom(2048)
            if ack.decode().strip() == f"ACK:{message}":
                # acknowledgement received heree
                sock.settimeout(None)  # restore default
                return True
        except socket.timeout:
            print("Timeout!!! Retrying...")

    print(":0 No ACK received after retries")
    sock.settimeout(None)
    return False


# MAIN STUFF
username = False
username = userLogin()
while not username:
    username = userLogin()

# we now move on
print("~~~~~~~~~~~~~~~~~~~~ Welcome to the Forum! :D ~~~~~~~~~~~~~~~~~~~~~~")

while True:
    display_menu()

    # Get user command input
    command = input("Enter a command: ").strip()
    print("\n")
    user_command = command.split()[0].lower()

    if user_command == "xit":
        print("Goodbye\n")
        # clientSocket.sendto(f"{username} {user_command}".encode(), serverAddress)
        if not reliable_send(clientSocket, f"{username} {user_command}", serverAddress):
            print("Failed to deliver command due to packet loss.")
            continue
        break  # exiting the loop

    elif (user_command == "crt" or user_command == "lst" or user_command == "msg" or user_command == "dlt"
        or user_command == "rdt" or user_command == "edt" or user_command == "rmv"):
        # clientSocket.sendto(f"{username} {command}".encode(), serverAddress)
        if not reliable_send(clientSocket, f"{username} {command}", serverAddress):
            print("Failed to deliver command due to packet loss.")
            continue  # send username and then command stuff
        command_response, _ = clientSocket.recvfrom(2048)
        print(command_response.decode())

    #  ~~~~~~~~~~~~~~~~~~~~~~ TCP RELIANT OPERATIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
    elif user_command == "upd":

        # clientSocket.sendto(f"{username} {command} {serverPort}".encode(), serverAddress)  # udp
        if not reliable_send(clientSocket, f"{username} {command}", serverAddress):
            print("Failed to deliver command due to packet loss.")
            continue  # send username and then command stuff
        command_response, _ = clientSocket.recvfrom(2048)
        print(command_response.decode())

        if "Error!" in command_response.decode():
            continue  # don't proceed to TCP if there's an error

        # start tcp connection
        tcp_client = socket(AF_INET, SOCK_STREAM)
        tcp_client.connect(('127.0.0.1', serverPort))

        if len(command.split()) < 3:
            print("Usage: upd <threadTitle> <filename>")
            continue

        threadTitle = command.split()[1]
        filename = command.split()[2]

        with open(filename, "rb") as f:
            while True:
                chunk = f.read(2048)
                if not chunk:
                    break
                tcp_client.send(chunk)  # client must transfer file's content to server

        tcp_client.close()  # file transfer done
        print(f"File {filename} successfully uploaded to thread {threadTitle}\n")

    elif user_command == "dwn":
        # clientSocket.sendto(f"{username} {command} {serverPort}".encode(), serverAddress)  # udp
        if not reliable_send(clientSocket, f"{username} {command}", serverAddress):
            print("Failed to deliver command due to packet loss.")
            continue  # send username and then command stuff
        
        command_response, _ = clientSocket.recvfrom(2048)
        print(command_response.decode())

        if "Error!" in command_response.decode():
            continue  # don't proceed to TCP if there's an error

        # start tcp connection
        tcp_client = socket(AF_INET, SOCK_STREAM)
        # newPort = serverPort + 1000
        tcp_client.connect(('127.0.0.1', serverPort))

        if len(command.split()) < 3:
            print("Usage: dwn <threadTitle> <filename>")
            continue

        threadTitle = command.split()[1]
        filename = command.split()[2]

        with open(filename, "wb") as f:
            while True:
                data = tcp_client.recv(2048)
                if not data:
                    break
                f.write(data)

        tcp_client.close()
        print(f"File {filename} successfully downloaded from thread {threadTitle}\n")

    else:
        print("Error! Invalid command.\n")

# close UDP socket
clientSocket.close()
