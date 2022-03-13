from nis import cat
from re import L
import socket
from urllib import request
import tcp

from click import command
import tcp
import sys  # for arguments retrieval from terminal

DISCONNECT_MESSAGE = "!DISCONNECT"


class Client:
    active_socket: socket.socket
    server_IP = "127.0.1.1"
    commands = "f <FILENAME>, ls <PATTERN> (Server only)"

    def __init__(this, actions=[]) -> None:

        adress = (this.server_IP, 9110)

        if actions:
            tcp.open_connection(adress, actions)
        else:
            dest_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Handshake
            dest_sock.connect(adress)
            # checking answer
            answer_packet = dest_sock.recv(tcp.BUFFER_SIZE)
            while answer_packet == b'':  # must get a valid answer
                answer_packet = dest_sock.recv(tcp.BUFFER_SIZE)
            answer_packet_contents = tcp.get_body(answer_packet)
            result = answer_packet_contents.split(tcp.SEP)[0]

            # connection accepted !
            print("receiver : connection  ")
            if result != tcp.ACCEPT_CONNECTION:
                if tcp.DEBUG:
                    print("connection denied !")
                dest_sock.close()
                return
            else:
                if tcp.DEBUG:
                    print("connection accepted !")

                rq = input()
                while(rq != "close"):

                    data = rq.split()
                    if data[0] == "f":
                        tcp.get_file(data[1], dest_sock)
                    elif data[0] == "ls":
                        try:
                            this.get_files_info(dest_sock, data[1])
                        except:
                            this.get_files_info(dest_sock)
                    else:
                        print(f"command {rq} not understood")
                        
                        
                    rq = input()

                dest_sock.send(tcp.take_packet(body=DISCONNECT_MESSAGE))
                dest_sock.close()

    def get_files_info(this, dest_sock :socket.socket, pattern=""):
        request = tcp.LS_REQUEST + tcp.SEP + (pattern.encode(tcp.FORMAT))
        packet = tcp.make_packet(body=request)
        dest_sock.send(packet)
        result = tcp.get_message(dest_sock)
        print(result)


if __name__ == "__main__":
    Client()
