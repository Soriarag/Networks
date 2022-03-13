# inspired from : https://www.techwithtim.net/tutorials/socket-programming/
from email.headerregistry import Address
from genericpath import isfile
import socket  # low level implementation
# import module # blockchain module
import tcp
import glob
import threading
from client import *

all_agents = ["Carl", "Juan", "Julie", "Hans"]

class Server:
    active_socket: socket.socket

    available_agents = {str: Agent}
    available_agents["Serv"] = Agent((host, 9100), (host, 162))
    available_agents["Carl"] = Agent((host, 99), (host, 139))
    available_agents["Juan"] = Agent((host, 5000), (host, 5001))
    available_agents["Julie"] = Agent((host, 5002), (host, 5003))
    available_agents["Hans"] = Agent((host, 5004), (host, 5005))


    def __init__(this, name="DEFAULT", IP = "127.0.1.1", port =  9100) -> None:

        this.file_use_history = {str:[]}
        this.file_use_history["a.jpg"] = all_agents
        this.file_use_history["p.pdf"] = all_agents[1:2]
        this.file_use_history["w.txt"] = []
        this.def_path = "test_files/"
        
        #building file tracking
        l = len(this.def_path)
        
        for name in glob.glob(this.def_path + '*'):
          this.file_use_history[name[l:]] = []

        adress = (IP, port)  # 9100 is the default TCP port number
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.bind(adress)
        tcp_sock.listen()
        active_tcp = 0
        
        print(f"SERVER {name} ONLINE")
        while True:
            client_socket, client_adress = tcp_sock.accept()
            request_handler = threading.Thread(
                target=this.handle_client, args=[client_socket, client_adress])
            request_handler.start()
            active_tcp += 1
            print(
                f"tcp req accepted, now handling {active_tcp} tcp connections")

    def handle_client(this, client_socket: socket.socket, client_adress):
        
        
        
       # request credentials
        mssg = tcp.CREDENTIAL_REQUEST
        client_socket.send(tcp.make_packet(body=mssg))
        
        answer_packet_contents = client_socket.recv(tcp.BUFFER_SIZE)
        name =  answer_packet_contents.split(tcp.SEP)[0].decode(tcp.FORMAT)
        print ("recieved " + name)
       # perform handshake
        mssg = tcp.ACCEPT_CONNECTION
        client_socket.send(tcp.make_packet(body=mssg))
        connected = True
        
        while connected:
            request_packet = client_socket.recv(tcp.BUFFER_SIZE)
            while (request_packet == b''):
                request_packet = client_socket.recv(tcp.BUFFER_SIZE)

            reques_mssg = tcp.get_body(request_packet)
            print(f"received {reques_mssg}")
            request_parse = reques_mssg.split(tcp.SEP)

            request = request_parse[0]
            if request == tcp.FILE_REQUEST:
                filename = request_parse[1].decode(tcp.FORMAT)
                if (isfile(this.def_path + filename)):
                  this.file_use_history[filename].append(client_adress[0])
                tcp.send_file(filename, client_socket, this.def_path)
                
            elif request == tcp.LS_REQUEST:
                regex = "*"
                if len(request_parse) > 1:
                  regex = request_parse[1].decode(tcp.FORMAT)
                this.send_files_list(client_socket,pattern=regex,path=this.def_path)
                
            elif request == tcp.DISCONNECT_MESSAGE:
                client_socket.close()
                connected = False
            else:
                tcp.send_mssg(tcp.ERR_INVALID_REQ, client_socket)
                
    def send_files_list(this, dest_socket:socket.socket, pattern= "*", path=""):
      files_ls = '\n'.join(glob.glob('test_files/*'))
      tcp.send_mssg(files_ls.encode(tcp.FORMAT), dest_socket)


if __name__ == "__main__":


    print("[STARTING] server is starting...")
    myServer = Server(port= 9100)
