
from ast import ListComp, Try
from concurrent.futures import thread
from email import header
from fileinput import filename
from http import client
from multiprocessing import connection
from os import sendfile
import socket
import threading
import io
from urllib import request

from matplotlib.style import available

WAIT_TIMEOUT = 50  # in ms
HEADER_LEN = 8
BUFFER_SIZE = 1400
CONTINOUS_PACKETS = 4
FORMAT = 'utf-8'
ACCEPT_CONNECTION = b"connect_accept"
DENY_CONNECTION = b"connect_deny"
DISCONNECT_MESSAGE = b"!DISCONNECT"
SEP = b" "
FILE_REQUEST = b"req_FILE"
ERR_INVALID_REQ = b"ERR_inv_req"
ERR_EXPECT_ACK = b"ERR_exp_ack"

def REDIRECT_PORT(port: int): return b"to_" + str(port).encode(FORMAT)
def ACK(n): return b"ACK" + SEP + str(n).encode(FORMAT)

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

    def handle_tcp_client(prot, client_socket: socket.socket, client_adress):
        # in my protocol the one requesting the tcp connection can just request files

        # perform handshake
        prot.send_mssg(ACCEPT_CONNECTION, client_socket)
        connected = True

        # manage acks
        prot.ack_recv[client_socket] = 0

        while connected:
            request_packet = client_socket.recv(BUFFER_SIZE)
            request = request_packet.split(SEP)
            if request[0] == FILE_REQUEST:
                filename = str(request[1])
                sendfile(filename, client_socket)
            else:
                prot.send_mssg(ERR_INVALID_REQ)

    def get_contents(prot, packet: bytes):

        packet_header = packet[:HEADER_LEN]
        packet_contents = packet[HEADER_LEN + 1:]
        packet_convention = int(packet_header[:4])
        last_ack = int(packet_header[5:])
        return packet_convention, last_ack, packet_contents

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
        packet_buffer = [bytes]
        sent_packets = 0
        received_ACKS = 0
        mssg_contents = bytes_stream.read(available_space)
        while mssg_contents != b'':

            # read from the stream and send send packets
            mssg_header = prot.make_header(received_ACKS)
            mssg = mssg_header + mssg_contents

            dest_socket.send(bytes_stream)
            packet_buffer.append(mssg_contents)
            sent_packets += 1

            # check reception
            if sent_packets == CONTINOUS_PACKETS:
                last_recv = prot.recv_ack(dest_socket)
                while (last_recv != sent_packets):
                    mssg_contents = packet_buffer[last_recv + 1]
                    mssg_header = prot.make_header(last_recv)
                    mssg = mssg_header + mssg_contents
                    dest_socket.send(bytes_stream)
                    last_recv = prot.recv_ack(dest_socket)
            
            #continue
            mssg_contents = bytes_stream.read(available_space)

    def recv_ack(prot, source_socket: socket.socket) -> int:
        packet = source_socket.recv(BUFFER_SIZE)
        _, _, ack_mssg = prot.get_contents(ack_mssg)
        
        mssg = ack_mssg.split(SEP)
        if mssg[0] != ACK:
          prot.send_mssg(ERR_EXPECT_ACK)
        else :
          try :
            return int(mssg[1])
          except:
            prot.send_mssg(ERR_EXPECT_ACK)
