from socket import *
import os
import glob

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HELPER FUNCTIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

# check if a threadtitle does not exist, true if it exists, false otherwise
def check_threadTitle(socket, addr, threadTitle, errorMsg):
    if not os.path.exists(f"{threadTitle}"):
        print(errorMsg)
        socket.sendto(errorMsg.encode(), addr)
        return False  # exit out of func
    return True

# check if no less than a certain number of args have been provided
def argument_checker(socket, command, num, addr):
    min_args = 0
    if command == "crt" or command == "rdt" or command == "rmv":
        min_args = 2
    elif command == "lst": # jus list all the threadTitles lol
        min_args = 1
    elif command == "msg" or command == "dlt" or command == "upd" or command == "dwn":
        min_args = 3
    elif command == "edt":
        min_args = 4

    if num < min_args:
        error_msg = f"Error! Invalid command for command {command}"
        socket.sendto(error_msg.encode(), addr)
        print(error_msg)
        return False
    
    return True

# once user quits session, remove them 
def end_user_session(username, addr, client_handlers, active_users):
    print(f":0 Ending session for {username}")
    if addr in client_handlers:
        del client_handlers[addr]
    if username in active_users:
        del active_users[username]

    
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DISCUSSION FORUM OPERATIONS ~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MY FORUM OPERATIONS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def process_command(socket, client_queue, addr, client_handlers, active_users):
    server_ip, serverPort = socket.getsockname()
    while True:
        # msg_bytes, client_addr = self.socket.recvfrom(2048)
        msg = client_queue.get()
        clientMsg = msg.decode().strip()

        socket.sendto(f"ACK:{clientMsg}".encode(), addr)

        if not clientMsg:
            end_user_session(user, addr, client_handlers, active_users)
            break   
        # username_data.decode().strip()

        message_parts = clientMsg.split()  # splitting the msg
        user = message_parts[0] # username
        command = message_parts[1] # command
        # print("hehe", command)
        if not argument_checker(socket, command, len(message_parts) - 1, addr):
            continue

        if command == "xit":
            end_user_session(user, addr, client_handlers, active_users)
            break

        print(f"{user} issued {command.upper()} command\n")
        
        # the commands
        if command == "crt":
            threadTitle = message_parts[2]
            create_post(socket, addr, threadTitle, user)
        elif command == "lst": # jus list all the threadTitles lol
            list_posts(socket, addr)
        elif command == "msg":
            threadTitle = message_parts[2]
            message = " ".join(message_parts[3:])
            message_post(socket, addr, user, threadTitle, message)
        elif command == "dlt":
            threadTitle = message_parts[2]
            messageNum = message_parts[3]
            delete_post(socket, addr, user, threadTitle, messageNum)
        elif command == "rdt":
            threadTitle = message_parts[2]
            read_post(socket, addr, threadTitle)
        elif command == "edt":
            threadTitle = message_parts[2]
            messageNum = message_parts[3]
            new_message = " ".join(message_parts[4:])
            edit_post(socket, addr, user, threadTitle, messageNum, new_message)
        elif command == "upd":
            threadTitle = message_parts[2]
            filename = message_parts[3]
            upload_post(socket, addr, serverPort, user, threadTitle, filename)
        elif command == "dwn":
            threadTitle = message_parts[2]
            filename = message_parts[3]
            download_post(socket, addr, serverPort, user, threadTitle, filename)
        elif command == "rmv":
            threadTitle = message_parts[2]
            remove_post(socket, addr, user, threadTitle)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION FOR CREATING A NEW POST ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def create_post(socket, addr, threadTitle, user):
    # checking if file alr exists
    error_message = "Error! Thread with this title already exists.\n"

    if os.path.exists(f"{threadTitle}"):
        print(error_message)
        socket.sendto(error_message.encode(), addr)
        return False  # exit out of func
    

    # file doesn't exist
    with open(f"{threadTitle}", "w") as thread_file:
        # Write the username as the first line of the file
        thread_file.write(f"{user}\n")
    confirmation_message = f"Thread '{threadTitle}' created successfully by {user}.\n"
    print(confirmation_message)
    socket.sendto(confirmation_message.encode(), addr)  # Send confirmation to client
    return True

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION FOR POSTING A MSG ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def message_post(socket, addr, user, threadTitle, message):
    error_message = "Error! Thread with this title does not exist\n"
    if not check_threadTitle(socket, addr, threadTitle, error_message):
        return False  # exit out of func
    
    # thread exists!
    message_number = 1  # Default message number for the first message
    with open(f"{threadTitle}", "r") as f:
        lines = f.readlines()
        message_lines = [line for line in lines if line.strip() and line.strip().split()[0].isdigit()]
        if message_lines:
            last_line = message_lines[-1].strip()
            last_message_number = int(last_line.split()[0])  # The first part is the message number
            message_number = last_message_number + 1  # Increment the message number

    with open(f"{threadTitle}", "a") as f:
        f.write(f"{message_number} {user}: {message}\n")
            
    confirmation_message = f"Message successfully posted to {threadTitle} thread\n"
    print(confirmation_message)
    socket.sendto(confirmation_message.encode(), addr)

    return True
    
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION FOR DELETING A MSG ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def delete_post(socket, addr, user, threadTitle, messageNum):
    error_message = "Error! Thread with this title does not exist\n"
    if not check_threadTitle(socket, addr, threadTitle, error_message):
        return False  # exit out of func
    
    # thread exists
    try:
        messageNum = int(messageNum)
    except ValueError: # some error checking
        socket.sendto("Error! Message number must be an integer.\n".encode(), addr)
        return False

    with open(f"{threadTitle}", "r") as f:
        lines = f.readlines()

    if len(lines) <= 1:
        socket.sendto("Error! No messages in this thread.\n".encode(), addr)
        return False

    message_found = False
    new_lines = [lines[0]]  # keep the creator username line
    new_message_index = 1

    for line in lines[1:]:
        parts = line.strip().split(' ', 1)
        if len(parts) < 2:
            continue  # skipping the weird lines
        
        # adjustment for uploading file :3
        if not parts[0].isdigit():
        # not a numbered message 
            new_lines.append(line)
            continue

        current_msg_num = int(parts[0])
        content = parts[1]
        author, _ = content.split(":", 1)

        if current_msg_num == messageNum:
            if author != user:
                socket.sendto("Error! You can only delete your own messages.\n".encode(), addr)
                return False
            message_found = True
            continue  # Skip this line to delete
        else:
            new_lines.append(f"{new_message_index} {content}\n")
            new_message_index += 1

    if not message_found:
        socket.sendto("Error! Message number does not exist.\n".encode(), addr)
        return False

    # Write back the updated thread
    with open(f"{threadTitle}", "w") as f:
        f.writelines(new_lines)

    confirmation_message = "Message successfully deleted.\n"
    print(confirmation_message)
    socket.sendto(confirmation_message.encode(), addr)
    return True


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION FOR EDITING A MSG ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def edit_post(socket, addr, user, threadTitle, messageNum, new_message):
    # lets' geddittt
    error_message = "Error! Thread with this title does not exist\n"
    if not check_threadTitle(socket, addr, threadTitle, error_message):
        return False  # exit out of func
    
    with open(f"{threadTitle}", "r") as f:
        lines = f.readlines()

    if len(lines) <= 1:
        error_message = "Error! No messages to edit\n"
        print(error_message)
        socket.sendto(error_message.encode(), addr)
        return False

    try:
        messageNum = int(messageNum)
    except ValueError: # some error checking
        socket.sendto("Error! Message number must be an integer.\n".encode(), addr)
        return False
    
    message_found = False
    # Loop through lines starting from the second line (ie index 1)
    for i in range(1, len(lines)):
        parts = lines[i].strip().split(' ', 2)
        if len(parts) >= 3 and parts[0].isdigit():
            current_num = int(parts[0])
            author = parts[1][:-1]  # extract the user who posted it
            if current_num == messageNum:
                if author == user:
                    lines[i] = f"{messageNum} {user}: {new_message}\n"
                    message_found = True
                else:
                    error_message = "Error! You can only edit your own messages\n"
                    print(error_message)
                    socket.sendto(error_message.encode(), addr)
                    return False
                break

    if not message_found:
        error_message = "Error! Message number not found\n"
        print(error_message)
        socket.sendto(error_message.encode(), addr)
        return False

    with open(f"{threadTitle}", "w") as f:
        f.writelines(lines)

    success_message = "Message edited successfully!! \n"
    print(success_message)
    socket.sendto(success_message.encode(), addr)
    return True


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION FOR LISTING THE POSTS ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def list_posts(socket, addr):
    # all files in cwd
    thread_titles = [
    f for f in os.listdir(".")
    if os.path.isfile(f) and "-" not in f and "." not in f
    ]

    if thread_titles:
        thread_list = "~~~~~ LIST OF THREAD TITLES ~~~~~~\n" + "\n".join(thread_titles) + "\n"
        print("Sending thread list to client\n")
        socket.sendto(thread_list.encode(), addr)
    else:
        msg = "No active threads available.\n"
        print("No threads to list")
        socket.sendto(msg.encode(), addr)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FUNCTION FOR READING A THREAD ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def read_post(socket, addr, threadTitle): # the user doesn't matter.
    error_message = f"Error! Thread {threadTitle} does not exist\n"
    if not check_threadTitle(socket, addr, threadTitle,error_message):
        return  # exit out of func

    with open(f"{threadTitle}", "r") as f:
        lines = f.readlines()

    if len(lines) <= 1:
        # Only the creator line exists, no messages
        empty_message = "This thread is currently empty!\n"
        socket.sendto(empty_message.encode(), addr)
        return

    # Join and send all lines except the the usr line
    thread_contents = f"~~~~~~~~~~ THREAD {threadTitle} ~~~~~~~~~~\n" + "".join(lines[1:]) + "\n"
    print(f"Thread {threadTitle} read\n")
    socket.sendto(thread_contents.encode(), addr)
    
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~ FUNCTION FOR UPLOADING A FILE TO A THREAD ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def upload_post(serverSocket, addr, serverPort, user, threadTitle, filename):

    # ~~~~~~~~~~~~~~~~~~~~~~ Error checking ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    error_message = f"Error! Thread {threadTitle} does not exist\n"
    if not check_threadTitle(serverSocket, addr, threadTitle, error_message):
        return  # exit out of func
    
    no_file_msg = f"Error! File {filename} does not exist in cwd\n"
    if not os.path.exists(f"{filename}"):
        print(no_file_msg)
        serverSocket.sendto(no_file_msg.encode(), addr)
        return  # exit out of func
    
    
    with open(f"{threadTitle}", "r") as f:
        if f"{filename}" in f.read():
            serverSocket.sendto(f"Error! File {filename} already uploaded to thread {threadTitle}\n".encode(), addr)
            return
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # past all the errors :3
    serverSocket.sendto("Proceed with TCP file upload".encode(), addr)

    # start tcp connection
    tcp_server = socket(AF_INET, SOCK_STREAM)
    tcp_server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    tcp_server.bind(('127.0.0.1', serverPort))  # same port as UDP, totally fine
    tcp_server.listen(1)

    conn, addr = tcp_server.accept()
        
    with open(f"{threadTitle}-{filename}", "wb") as f:
        while True:
            data = conn.recv(2048)
            if not data:
                break
            f.write(data)

    conn.close()
    tcp_server.close()

    print(f"{user} uploaded file {filename} to {threadTitle} thread\n")

    with open(f"{threadTitle}", "a") as thread_file:
        thread_file.write(f"{user} uploaded {filename}\n")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~ FUNCTION FOR DOWNLOADING A FILE FROM A THREAD ~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def download_post(serverSocket, addr, serverPort, user, threadTitle, filename):

    # ~~~~~~~~~~~~~~~~~~~~~~ Error checking ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    error_message = f"Error! Thread {threadTitle} does not exist\n"
    if not check_threadTitle(serverSocket, addr, threadTitle, error_message):
        return  # exit out of func
    
    # wait nvm its valid????
    no_file_msg = f"Error! File {filename} does not exist in cwd\n"
    full_path = f"{threadTitle}-{filename}"

    if not os.path.exists(full_path):
        print(no_file_msg)
        serverSocket.sendto(no_file_msg.encode(), addr)
        return  # exit out of func
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # WARNING THE CLIENT
    serverSocket.sendto("Starting file transfer...\n".encode(), addr)

    tcp_server = socket(AF_INET, SOCK_STREAM)
    tcp_server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    tcp_server.bind(('127.0.0.1', serverPort))
    tcp_server.listen(1)

    conn, addr = tcp_server.accept()
    with open(full_path, "rb") as f:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
            conn.send(chunk)

    conn.close()
    tcp_server.close()

    print(f"File {filename} from {threadTitle} sent to {user}\n")
    

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# ~~~~~~~~~~~~~~~~~~~~~~ FUNCTION FOR REMOVING AN ENTIRE THREAD ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
def remove_post(socket, addr, user, threadTitle):
    error_message = f"Error! Thread {threadTitle} does not exist\n"
    if not check_threadTitle(socket, addr, threadTitle, error_message):
        return  # exit out of func
    
    thread_path = f"{threadTitle}"
    with open(thread_path, "r") as f:
        lines = f.readlines()

    first_line = lines[0].strip()  
    if first_line == user:
        os.remove(thread_path)
        for file in glob.glob(f"{threadTitle}-*"):
            os.remove(file)
        success_msg = f"Thread {threadTitle} successfully removed.\n"
        print(success_msg)
        socket.sendto(success_msg.encode(), addr)
        # delete the whole ahh thread i suppose in threads dir
        # delete all files that start with threadTitle-
    else:
        socket.sendto(f"Error! Thread {threadTitle} doesn't belong to user {user}\n".encode(), addr)