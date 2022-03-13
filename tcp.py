
from os import sendfile
import socket
import threading
import io
import select

from matplotlib.style import available


DEBUG = True
WAIT_TIMEOUT = 50  # in ms
HEADER_LEN = 8
BUFFER_SIZE = 1400
CONTINOUS_PACKETS = 4
FORMAT = 'utf-8'
ACCEPT_CONNECTION = b"CONNECT_accept"
DENY_CONNECTION = b"CONNECT_deny"
END_OF_DATA = b"!END"
DISCONNECT_MESSAGE = b"!DISCONNECT"
SEP = b" "
FILE_REQUEST = b"REQ_FILE"
ERR_INVALID_REQ = b"ERR_inv_req"
ERR_EXPECT_ACK = b"ERR_exp_ack"


def REDIRECT_PORT(port: int): return b"to_" + str(port).encode(FORMAT)
def ACK(n): return b"ACK" + SEP + str(n).encode(FORMAT)

# protocol :
# CONTINOUS_PACKETS 4 | PACKET_INDEX 4
# N_ACKS goes as high as CONTINOUS_PACKETS then bakc to 0

# got from https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method


def recv_timeout(sock: socket.socket, timeout_seconds):
    sock.setblocking(0)
    ready = select.select([sock], [], [], timeout_seconds)
    if ready[0]:
        return sock.recv(BUFFER_SIZE)
    else:
        raise socket.timeout()


def make_header(index_seq, packets_for_ack=4):
    header_str = str(packets_for_ack) + str(index_seq)
    return header_str.encode(FORMAT)


# --------------------------------------------------------------------------------------------
# receiving tcp requests -sending files

def listen_req(ip: str, port=9100):

    adress = (ip, port)  # 9100 is the default TCP port number
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect(adress)
    tcp_sock.listen()
    active_tcp = 0

    while True:
        client_socket = tcp_sock.accept()
        request_handler = threading.Thread(
            target=handle_tcp_client, args=client_socket)
        request_handler.start()
        active_tcp += 1
        print(f"tcp req accepted, now handling {active_tcp} tcp connections")


def handle_tcp_client(client_socket: socket.socket):
    # in my protocol the one requesting the tcp connection can just request files

    # perform handshake
    send_mssg(ACCEPT_CONNECTION, client_socket)
    connected = True

    # manage acks

    while connected:
        request_packet = client_socket.recv(BUFFER_SIZE)
        request = request_packet.split(SEP)
        if request[0] == FILE_REQUEST:
            filename = str(request[1])
            sendfile(filename, client_socket)
        elif request[0] == DISCONNECT_MESSAGE:
            client_socket.close()
            connected = False
        else:
            send_mssg(ERR_INVALID_REQ)


def get_contents(packet: bytes):
    """returns packet_convention, last_ack, packet_contents"""
    packet_header = packet[:HEADER_LEN]
    packet_contents = packet[HEADER_LEN + 1:]
    packet_convention = int(packet_header[:4])
    last_ack = int(packet_header[5:])
    return packet_convention, last_ack, packet_contents


def send_mssg(mssg: str, dest_socket: socket.socket):
    stream = io.BytesIO(mssg)
    send_stream(stream)
    stream.close()


def send_file(filename: str, dest_socket: socket.socket):
    stream = open(filename, "rb")
    send_stream(stream)
    stream.close()


def recv_ack(source_socket: socket.socket) -> int:
    packet = source_socket.recv(BUFFER_SIZE)
    _, _, ack_mssg = get_contents(packet)

    mssg = ack_mssg.split(SEP)
    if mssg[0] != "ACK":
        send_mssg(ERR_EXPECT_ACK)
    else:
        try:
            return int(mssg[1])
        except:
            send_mssg(ERR_EXPECT_ACK)

# TCP connection already opened


def send_stream(bytes_stream, dest_socket: socket.socket):

    available_space = BUFFER_SIZE - HEADER_LEN
    packet_buffer = [bytes]
    sent_packets = 0
    mssg_contents = bytes_stream.read(available_space)
    while mssg_contents != b'':

        if DEBUG:
            print("sender: Sending packet")
        # read from the stream and send send packets

        sent_packets += 1
        mssg_header = make_header(sent_packets)
        mssg = mssg_header + mssg_contents

        dest_socket.send(bytes_stream)
        packet_buffer.append(mssg_contents)

        # check reception
        if sent_packets == CONTINOUS_PACKETS:
            if DEBUG:
                print("sender: checking acks")
            sent_packets = 0
            received_ACKS = recv_ack(dest_socket)
            while (last_recv != CONTINOUS_PACKETS):
                if DEBUG:
                    print(f"error last ack is {last_recv}")
                mssg_contents = packet_buffer[last_recv + 1]
                mssg_header = make_header(last_recv,1)
                mssg = mssg_header + mssg_contents
                dest_socket.send(mssg)

                received_ACKS = recv_ack(dest_socket)

        # continue
        mssg_contents = bytes_stream.read(available_space)

    # manage tail (remaning non Acked messages)
    dest_socket.send(make_header(last_recv) + b'',sent_packets)  # empty message demands ack
    while (last_recv != sent_packets):
        if DEBUG:
            print(f"error in tail last ack is {last_recv}, setn packets is ")
        mssg_contents = packet_buffer[last_recv + 1]
        mssg_header = make_header(last_recv)
        mssg = mssg_header + mssg_contents
        dest_socket.send(mssg)

        last_recv = recv_ack(dest_socket)

    dest_socket.send(END_OF_DATA)


# --------------------------------------------------------------------------------------------
# sending tcp requests -receiving files
""" opens a tcp connection and requests is a list of commands"""


def get_file(filename: str, source_sock: socket.socket):
    if DEBUG:
        print(f"getting file {filename}")
    new_file = open(filename,"wb")
    get_stream(new_file,source_sock)
    new_file.close()


def open_connection(adress, requests=[]):

    if DEBUG:
        print(f"attempting to connect to {adress}")
    dest_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Handshake
    dest_sock.connect(adress)
    answer_packet = dest_sock.recv(BUFFER_SIZE)
    _, _, answer_packet_contents = get_contents(answer_packet)
    result = answer_packet_contents.split(SEP)[0]
    if result != ACCEPT_CONNECTION:
        if DEBUG:
            print("connection denied !")
        dest_sock.close()
        return
    else:
        if DEBUG:
            print("connection accepted !")
        if requests:
            for rq in requests:
                data = rq.split()
                if data[0] == "f":
                    get_file(data[1], dest_sock)
                # elif data[0] == "ls":
                #     get_files_info(dest_sock)
                else:
                    print(f"command {rq} not understood")


def send_ack(n, dest_socket: socket.socket):
    mssg_header = make_header(0)
    mssg = mssg_header + ACK(n)
    dest_socket.send(mssg)


def get_stream(write_stream, source_socket: socket.socket):

    next_missing = 1
    remaining_data = True
    packet_buffer = [None] * CONTINOUS_PACKETS
    while remaining_data:

        if DEBUG:
            print("receiver :receiving packet")
        try:
            data = recv_timeout(source_socket, 1)
            if DEBUG:
                print("receiver : packet received")

            # check if packet is next in order
            packets_for_ack, seq_index, contents = get_contents(data)
            
            if contents == b'':
              send_ack(next_missing-1)
            
            if seq_index != next_missing:
                if DEBUG:
                    print(f"missing packet {seq_index}")
                packet_buffer[seq_index] = contents
            else:
                write_stream.write(contents)
                next_missing += 1
                # refill stream
                while next_missing <= packets_for_ack and packet_buffer[next_missing] != None:
                    write_stream.write(packet_buffer[next_missing])
                    packet_buffer[next_missing] = None
                    next_missing += 1

        except socket.timeout:
            send_ack(next_missing - 1)

        if DEBUG:
            print("receiver : packet_received")

        if next_missing == packets_for_ack + 1:

            send_ack(next_missing - 1)
            next_missing = 1

        else:
            next_missing += 1
