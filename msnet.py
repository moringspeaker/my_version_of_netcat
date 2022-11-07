#!/usr/bin/env python3
import sys
import socket
import getopt
import threading
import subprocess
import pdb

#define some global variables
listen = False
command = False
upload = False
secret = False
execute = ""
target = ""
upload_destination = ""
port= ""


def usage():
    print("Welcome to MS Net Tool")
    print("\n")
    print("Usage: msnet.py -s target_host -p port")
    print("Usage: msnet.py -t target_host -p target_port")
    print("-l --listen              - listen on [host]:[port] for \n incoming connections\n")
    print("-e --execute=file_to_run -execute the given file upon \n receiving a conneciton\n")
    print("-c --command             -initialize a command shell\n")
    print("-u --upload=destination  -upon receiving connection upload a \n file and write to [destination]\n")
    print("Examples:\n")
    print("msnet.py -t 192.168.0.1 -p 5555 -l -c")
    print("msnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
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

    if not len(sys.argv[1:]):       #if argument variable is not null
        usage()

    try:
        opts,args=getopt.getopt(sys.argv[1:],"hle:t:p:cu:s",["help","listen","execute","target","port","command","upload","secret"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for i,a in opts:
        if i in ("-h","--help"):
            usage()
        elif i in ("-s","--secret"):
            secret=True
        elif i in ("-l","--listen"):
            listen = True
        elif i in ("-e","--execute"):
            execute = a
        elif i in ("-c","--commandshell"):
            command = True
        elif i in ("-u","--upload"):
            upload_destination = a
        elif i in ("-t","--target"):
            target=a
        elif i in ("-p","--port"):
            port=int(a)
        else:
            assert False,"Unhandled Option"

    if secret:
        secret_detect()

    if not listen and len(target) and port >0 :#if we don't want to listen a port but just send data through standard input

        buffer = input("send:")
        #send datan
        client_sender(buffer)

    if listen:
        server_loop()



def calculte_digits(buffer):
    sum=0
    res=""
    for i in buffer:
        if i.isdigit():
            sum+=1
            res+=i
    return sum,res

def secret_detector(client_socket):
    global secret
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
                break
            else:
                client_socket.send("Secret code not found.".encode())

def secret_detect():
    global target
    global port
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
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
                sys.exit(0)
            buffer += "\n"

            client.send(buffer.encode())
            print("sent!")
    except:
        print("[*] Exception! Exiting...")
        client.close()

def server_loop():
    global target

    if not len(target):
        target = "0.0.0.0"

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((target,port))

        server.listen(5)    #listen 5 connections

    while True:
        client_socket, addr=server.accept()
        #   divide a thread to manipulate a new client

        client_thread = threading.Thread(target=client_handler,args=(client_socket,))
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

    if len(upload_destination):
        file_buffer=""

        while True:
            data = client_socket.recv(1024)

            if not data:
                break

            else:
                file_buffer += data

    try:#   write our file into target system
        file_descriptor = open(upload_destination,"wb")
        file_descriptor.write(file_buffer)
        file_descriptor.close()

        #   make sure file is written
        client_socket.send("Successfully saved file to %s\r\n" %upload_destination)
    except:
        client_socket.send("Failed to save file to %s\r\n" %upload_destination)


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