from nis import cat
import socket
import tcp

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
    #todo open tcp

    def start(this):
      #run multiple threds receive and make actions
      pass
    
    
if __name__ == "__main__":  
  tcp.open_connection(("127.0.1.1",9100),["f platonic_solid.pdf"]) 