# inspired from : https://www.techwithtim.net/tutorials/socket-programming/
import socket  # low level implementation
# import module # blockchain module
import tcp

import threading


class Server:
    active_socket: socket.socket

    def __init__(this, name= "DEFAULT") -> None:

        this.file_use_history = {}
        
        adress = ("127.0.1.1", 9100)  # 9100 is the default TCP port number
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.bind(adress)
        tcp_sock.listen()
        print(f"SERVER {name} ONLINE")
        while True:
            client_socket, client_adress = tcp_sock.accept()
            request_handler = threading.Thread(
                target=this.handle_client, args=[client_socket,client_adress])
            request_handler.start()
            active_tcp += 1
            print(
                f"tcp req accepted, now handling {active_tcp} tcp connections")

    def handle_client(this,client_socket,client_adress):
       # perform handshake
      mssg = tcp.ACCEPT_CONNECTION
      client_socket.send(tcp.make_packet(body= mssg))
      connected = True


      # manage acks

      while connected:
          request_packet = client_socket.recv(tcp.BUFFER_SIZE)
          while (request_packet == b''):
            request_packet = client_socket.recv(tcp.BUFFER_SIZE)
          
          reques_mssg = tcp.get_body(request_packet)  
          
          request_parse = reques_mssg.split(tcp.SEP)
          
          if request_parse[0] == tcp.FILE_REQUEST:
              filename = request_parse[1].decode(tcp.FORMAT)
              tcp.send_file(filename, client_socket)
          elif request_parse[0] == tcp.DISCONNECT_MESSAGE:
              client_socket.close()
              connected = False
          else:
              tcp.send_mssg(tcp.ERR_INVALID_REQ, client_socket)

if __name__ == "__main__":

    tcp.listen_req("127.0.1.1", 9100)

    print("[STARTING] server is starting...")
    myServer = Server()
    myServer.start()
