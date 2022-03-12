from nis import cat
import socket
import threading

from click import command
from tcp import *
import sys  # for arguments retrieval from terminal

DISCONNECT_MESSAGE = "!DISCONNECT"



class Client:
    active_socket: socket.socket
    server_IP = "127.0.1.1"
    commands = {"gf"}

    def __init__(this) -> None:
        this.active_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 5001 + int(sys.argv[2])
        this.address = (this.server_IP, port)
        this.active_socket.connect(this.address)

    def send(this, msg):
        message = formatted(message)
        send_size(message, this.active_socket)
        this.active_socket.send(message)

    #todo open tcp

    def start(this):
      #run multiple threds receive and make actions
      while True:
        args = input().split()
      
        if args[0] == "gf" or args[0] == "GF" :
          try:
            file_name = args[1]
            thread = getFile(args[1],)
          except IndexError:
              print("missing file name") 
          
        else :
            print("command not found")
      