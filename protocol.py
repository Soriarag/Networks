
from ast import ListComp
from concurrent.futures import thread
from email import header
from http import client
import socket
import threading
import io

from matplotlib.style import available

WAIT_TIMEOUT = 50  # in ms
HEADER_LEN = 8
BUFFER_SIZE = 1400
CONTINOUS_PACKETS = 4
FORMAT = 'utf-8'
ACCEPT_CONNECTION = "connect_accept"
DENY_CONNECTION = "connect_deny"
DISCONNECT_MESSAGE = "!DISCONNECT"
SEP = "|"
def REDIRECT_PORT(port): return "to_" + str(port)
def ACK(n): return "ACK_" + str(n)

# protocol :
# CONTINOUS_PACKETS 4 | N_ACKS 4


def wait_ack() -> int:
    pass


class TCP_prot:

    def __init__(prot) -> None:
        prot.ack_recv = dict()
        prot.ack_sent = dict()

    def make_header(prot, nAcks):
        header_str = str(CONTINOUS_PACKETS) + str(nAcks)
        return header_str.encode(FORMAT)

    def listen_tcp_req(prot, ip: str, port=9100): 
        
        adress = (ip, port)  # 9100 is the default TCP port number
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect(adress)
        tcp_sock.listen()

        while True:
            client_socket, client_adress = tcp_sock.accept()

    def handle_tcp_client(prot, client_socket, client_adress):
      # in my protocol the one requesting the tcp connection can just request files
      # perform handshake
      prot.send_mssg(ACCEPT_CONNECTION,client_socket)

    def send_mssg(prot, mssg: str, dest_socket: socket.socket):
        stream = io.BytesIO(mssg)
        prot.send_stream(stream)
        stream.close()

    def send_file(prot, filename: str, dest_socket: socket.socket):
        stream = open(filename, "rb")
        prot.send_stream(stream)
        stream.close()

    # TCP connection already opened
    def send_stream(prot, bytes_stream: io.BytesIO, dest_socket: socket.socket):

        available_space = BUFFER_SIZE - HEADER_LEN
        packet_queue = [bytes]
        sent_packets = 0
        received_ACKS = 0
        mssg_contents = bytes_stream.read(available_space)
        while mssg != b'':

            # read from the stream and send send packets
            mssg_header = prot.make_header(received_ACKS)
            mssg = mssg_header + mssg_contents

            dest_socket.send(bytes_stream)
            packet_queue.append(mssg_contents)
            sent_packets += 1

            # check reception
            if sent_packets == CONTINOUS_PACKETS:
                last_recv = wait_ack()
                while (last_recv != sent_packets):
                    for mssg_contents in packet_queue[last_recv:]:
                        mssg_header = prot.make_header(last_recv)
                        mssg = mssg_header + mssg_contents
                        dest_socket.send(bytes_stream)
                    last_recv = wait_ack()
