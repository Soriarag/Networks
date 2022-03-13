from nis import cat
from re import L
import socket
from urllib import request

from matplotlib.style import available
import tcp

from click import command
import tcp
import sys  # for arguments retrieval from terminal

DISCONNECT_MESSAGE = "!DISCONNECT"


class Agent:
    def __init__(this, tcp_adress, udp_adress):
        this.tcp_adress = tcp_adress
        this.udp_adress = udp_adress

host = socket.gethostname()

class Client:
    active_socket: socket.socket
    UI_commands = "tcp <NAME> (not me), names, help"
    tcp_commands = "f <FILENAME>, ls <PATTERN> (lits files in Server only). d (disconnect)"
    available_agents = {str: Agent}
    available_agents["Serv"] = Agent((host, 9100), (host, 162))
    available_agents["Carl"] = Agent((host, 99), (host, 139))
    available_agents["Juan"] = Agent((host, 5000), (host, 5001))
    available_agents["Julie"] = Agent((host, 5002), (host, 5003))
    available_agents["Hans"] = Agent((host, 5004), (host, 5005))

    def __init__(this, name="Carl") -> None:
        
        while name == "Serv" or not name in this.available_agents.keys():
            name = input("You shouldn't be a server, choose a new name")

        this.name = name
        this.tcp_adress = this.available_agents[name].tcp_adress
        this.udp_adress = this.available_agents[name].tcp_adress
        print(f"Hi, I'm {name}, ready to go! type help to see commands")
        
        rq = input()
        while(rq != "d"):

            data = rq.split()
            l = len(data)
            if l > 0:
                if data[0] == "tcp":
                    if (l > 1):
                        name = data[1]
                        this.connect_tcp(name)
                    else:
                        print("missing_name")
                elif data[0] == "names":
                    print(f"My name is {name}")
                    for name in this.available_agents.keys():
                        print(name)
                elif data[0] == "help":
                    print(this.UI_commands)
                else:
                    print(f"command {rq} not understood")
            else :
                print("?")
            rq = input()


    def connect_tcp(this, name, actions=[]):
        
        while name == this.name:
            name = input("This can't be you! Choose a someone else")
        adress = this.available_agents[name].tcp_adress

        if actions:
            tcp.open_connection(adress, actions)
        else:
            dest_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Handshake
            dest_sock.connect(adress)
            # veryfying credentials
            
            answer_packet = dest_sock.recv(tcp.BUFFER_SIZE)
            while answer_packet == b'':  # must get a valid answer
                answer_packet = dest_sock.recv(tcp.BUFFER_SIZE)
                
            answer_packet_contents = tcp.get_body(answer_packet)
            results = answer_packet_contents.split(tcp.SEP)
            
            if results[0] == tcp.CREDENTIAL_REQUEST:
                print("sending name")
                mssg = this.name.encode(tcp.FORMAT)
                dest_sock.send(tcp.make_packet(body=mssg))
                print(mssg)
            else :
                print("missig credential request")
                return
            
            #answer verification
            answer_packet = dest_sock.recv(tcp.BUFFER_SIZE)
            answer_packet_contents = tcp.get_body(answer_packet)
            results = answer_packet_contents.split(tcp.SEP)

            # connection accepted !
            print(f"receiver : connection {results} ")
            if results[0] != tcp.ACCEPT_CONNECTION:
                if tcp.DEBUG:
                    print("connection denied !")
                dest_sock.close()
                return
            else:
                if tcp.DEBUG:
                    print("connection accepted !")
                
                
                rq = input()
                while(rq != "d"):

                    data = rq.split()
                    if data[0] == "f":
                        tcp.get_file(data[1], dest_sock)
                    elif data[0] == "ls":
                        try:
                            this.get_files_info(dest_sock, data[1])
                        except:
                            this.get_files_info(dest_sock)
                    elif data[0] == "help":
                        print(this.tcp_commands)
                    else:
                        print(f"command {rq} not understood")

                    rq = input()

                dest_sock.send(tcp.make_packet(body=DISCONNECT_MESSAGE))
                dest_sock.close()

    def get_files_info(this, dest_sock: socket.socket, pattern=""):
        request = tcp.LS_REQUEST + tcp.SEP + (pattern.encode(tcp.FORMAT))
        packet = tcp.make_packet(body=request)
        dest_sock.send(packet)
        result = tcp.get_message(dest_sock)
        print("FILES :\n" + result.decode(tcp.FORMAT))


if __name__ == "__main__":
    try :
        Client(sys.argv[1])
    except : Client()
