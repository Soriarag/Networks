#inspired from : https://www.techwithtim.net/tutorials/socket-programming/
import socket # low level implementation
import os
#import module # blockchain module
import tcp
class Server:
  active_socket: socket.socket
  def __init__(this) -> None:
    port = 5000
    IP = socket.gethostbyname(socket.gethostname())
    this.adress = (IP,port)
    
    this.active_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    this.active_socket.bind(this.adress)
    
   
  def start(this):
    pass
  
        


if __name__ == "__main__":
  
  tcp.listen_req("127.0.1.1",9100)
  
  print("[STARTING] server is starting...")
  myServer = Server()
  myServer.start()
