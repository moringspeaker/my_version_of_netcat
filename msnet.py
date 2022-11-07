#!/usr/bin/env python3
import sys
import socket
import getopt
import threading
import os
import subprocess
import pdb


#define some global variables
listen = False
command = False
upload = False
Secret=False
secret = ""
execute = ""
target = ""
upload_destination = ""
port= ""
file_name=""

def usage():
    print("Welcome to MS Net Tool")
    print("\n")
    print("Usage: msnet.py -p port -s target_host")
    print("Usage: msnet.py -t target_host -p port -l -u destination")
    print("Usage: msnet.py -t target_host -p port -f file_name ")
    print("Usage: msnet.py -t target_host -p target_port")
    print("Usage: msnet.py -t target_host -p target_port -l -c")

    print("\n")
    print("-S -S or --Secret \nwill not specified listening ip\n")
    print("-l --listen              - listen on [host]:[port] for \n incoming connections\n")
    print("-e --execute=file_to_run -execute the given file upon \n receiving a conneciton\n")
    print("-c --command             -initialize a command shell\n")
    print("-u --upload=destination  -upon receiving connection upload a \n file and write to [destination]\n")
    print("Examples:\n")
    print("msnet.py -t 10.10.10.3 -p 5555")
    print("msnet.py -p 5555 -s 10.10.10.2")
    print("msnet.py -p 5555 -S")
    print("msnet.py -t localhost -p 5555 -f hello.txt")
    print("msnet.py -t localhost -p 5555 -l -u ./target/")
    print("msnet.py -t 192.168.0.1 -p 5555 -l -c")
    print("echo 'ABCDEFG' | ./msnet.py -t 192.168.11.12 -p -123")
    sys.exit(0)

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target
    global secret
    global file_name
    global Secret

    if not len(sys.argv[1:]):       #if argument variable is not null
        usage()
    try:
        opts,args=getopt.getopt(sys.argv[1:],"hle:t:p:s:f:cu:S",["help","listen","execute","target","port","file","secret","command","upload","Secret"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for i,a in opts:
        if i in ("-h","--help"):
            usage()
        elif i in ("-l","--listen"):
            listen = True
        elif i in ("-e","--execute"):
            execute = a
        elif i in ("-c","--commandshell"):
            command = True
        elif i in ("-u","--upload"):
            upload_destination = a
        elif i in ("-S","--Secret"):
            Secret = True
        elif i in ("-t","--target"):
            target=a
        elif i in ("-s", "--secret"):
            secret = a
        elif i in ("-f", "--file"):
            file_name = a
        elif i in ("-p","--port"):
            port=int(a)
        else:
            assert False,"Unhandled Option"

    if len(secret):
        secret_detect()
        sys.exit(0)
    if Secret:
        secret_detect()
        sys.exit(0)
    if len(file_name):
        file_send()
        sys.exit(0)
    if listen:
        server_loop()
    if not listen and len(target) and len(upload_destination) == 0 and port > 0:  # if we don't want to listen a port but just send data through standard input
        buffer = input("send:")
        # send datan
        client_sender(buffer)

def file_send():    #send file
    global file_name
    global port
    global target
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((target, port))
    try:
        with open(file_name, "rb") as in_file:
            data = in_file.read(1024)
            client.send(file_name.encode())  # send file name
            response=client.recv(1024).decode() # wait for response
            if response=="OK":
                while data:
                    client.send(data)
                    data = in_file.read(1024)
                print("File sent")
                client.close()
    except:
        print("send error")
        client.close()


def calculte_digits(buffer):
    sum=0
    res=""
    for i in buffer:
        if i.isdigit():
            sum+=1
            res+=i
    return sum,res

def secret_detector(client_socket):
    global execute

    while True:
        client_buffer=client_socket.recv(1024).decode()
        print(client_buffer)
        if client_buffer:
            if "SECRET" in client_buffer:
                sum,res=calculte_digits(client_buffer)
                message="Digits: "+res+"    Count: "+str(sum)
                try:
                    client_socket.send(message.encode())
                except:
                    print("client closed")
            elif "EXIT" in client_buffer:
                print("client closed")
                client_socket.send("バイバイ".encode())
                client_socket.close()
                sys.exit(0)
            else:
                client_socket.send("Secret code not found.".encode())

def secret_detect():
    global secret
    global port
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if not len(secret):
        secret = "0.0.0.0"
    server.bind((secret, port))
    server.listen(1)
    while True:
        client_socket, addr = server.accept()
        client_thread = threading.Thread(target=secret_detector, args=(client_socket,))
        client_thread.start()


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((target,port))
        if len(buffer):
            client.send(buffer.encode())
        while True:
            #   now wait for data postback
            recv_len = 1
            response=""

            while recv_len:
                data = client.recv(1024).decode()
                recv_len = len(data)
                response+= data
                if recv_len < 1024:
                    break
            print("received:"+response)
            #wait for more input
            buffer = input("send:")
            if buffer == "EXIT":
                client.send(buffer.encode())
                lastone = client.recv(1024).decode()
                print("received:"+lastone)
                break
            buffer += "\n"
            client.send(buffer.encode())
        client.close()
        sys.exit(0)
    except:
        print("[*]Exiting...")
        client.close()

def server_loop():
    global target
    global port
    if not len(target):
        target = "0.0.0.0"
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target,port))
    server.listen(5)    #listen 5 connections
    # while True:
    #     client_socket, addr=server.accept()
    #     #   divide a thread to manipulate a new client
    #     client_thread = threading.Thread(target=client_handler,args=(client_socket,))
    #     client_thread.start()
    #     print("client connected")
    client_socket, addr = server.accept()
    #   divide a thread to manipulate a new client
    client_thread = threading.Thread(target=client_handler, args=(client_socket,))
    client_thread.start()

def run_command(command):
    command=command.rstrip()

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"

    result=output.decode()

    return result


def client_handler(client_socket):
    global upload
    global execute
    global command
    save_name=""

    if len(upload_destination):
        file_buffer=""
        save_name=client_socket.recv(1024).decode()
        client_socket.send("OK".encode())#send OK to client as a handshake
        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            else:
                file_buffer += data
    try:#   write our file into target system
        path= os.path.join(upload_destination,save_name)
        file_descriptor = open(path,"w")
        file_descriptor.write(file_buffer+"\n")
        file_descriptor.close()

        #   make sure file is written
        print("Successfully saved file to %s\r\n" %upload_destination)
        #client_socket.send("Successfully saved file to %s\r\n" %upload_destination) #send a message back
    except:
        print("Failed to save file to %s\r\n" %upload_destination)


    if len(execute):
        #   run the command
        output = run_command(execute)

        client_socket.send(output)

    if command:
        while True:
            #   jump out of a shell
            client_socket.send("<MSP:#>")
            cmd_buffer=""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
                response = run_command(cmd_buffer)
                #response the data
                client_socket.send(response)
if __name__=='__main__':
    main()