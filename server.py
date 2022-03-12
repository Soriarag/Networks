#inspired from : https://www.techwithtim.net/tutorials/socket-programming/
import socket # low level implementation
import threading # threading synchronous processes
#import module # blockchain module
import json
from unicodedata import name # encode json objects in block generation
from tcp import *

class Server:
  active_socket: socket.socket
  def __init__(this) -> None:
    port = 5000
    IP = socket.gethostbyname(socket.gethostname())
    this.adress = (IP,port)
    
    this.active_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    this.active_socket.bind(this.adress)
    
   
      
    
  def start(this):
    this.active_socket.listen()
    print(f"[LISTENING] Server is listening on {this.adress[1]}")
    while True:
      
        #listen for tcp connections
        tcp_thread = threading.Thread(target)
        client_socket, client_addr = this.active_socket.accept()
        thread = threading.Thread(target=this.handle_client, args=(client_socket, client_addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

  
      
    
  
  def handle_client(client_socket, addr):
      print(f"[NEW CONNECTION] {addr} connected.")

      connected = True
      while connected:
          msg_length = client_socket.recv(BUFFER_SIZE).decode(FORMAT)
          if msg_length:
              msg_length = int(msg_length)
              
              
              msg = client_socket.recv(msg_length).decode(FORMAT)
              
              if msg == DISCONNECT_MESSAGE:
                  connected = False

              print(f"[{addr}] {msg}")
              client_socket.send("Msg received".encode(FORMAT))

      client_socket.close()
        


if __name__ == "__main__":
  print("[STARTING] server is starting...")
  myServer = Server()
  myServer.start()
