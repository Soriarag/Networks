
from distutils.log import debug
from email import message
from genericpath import isfile
import socket
import threading
import io
import select


DEBUG = True
WAIT_TIMEOUT = 50  # in ms
HEADER_LEN = 8
BUFFER_SIZE = 200
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
ERR_FILE_NF = b"ERR_fileNF"
SUCCESS = b"SUCCESS"


def ACK(n): return b"ACK" + SEP + str(n).encode(FORMAT)


bytes_CONTINOUS_PACKETS = 4
bytes_PACKET_INDEX = 4
# protocol :
# CONTINOUS_PACKETS 4 | PACKET_INDEX 4
# N_ACKS goes as high as CONTINOUS_PACKETS then bakc to 0

# got from https://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method


def wait():
    if DEBUG:
        input()


def recv_timeout(sock: socket.socket, timeout_seconds):
    sock.setblocking(0)
    ready = select.select([sock], [], [], timeout_seconds)
    if ready[0]:
        return sock.recv(BUFFER_SIZE)
    else:
        raise socket.timeout()


def format_bytes(data, due_bytes=4):
    return data + ' ' * (due_bytes - len(data))


def make_header(index_seq, packets_for_ack=4):
    header_str = format_bytes(str(packets_for_ack)) + \
        format_bytes(str(index_seq))
    return header_str.encode(FORMAT)


# --------------------------------------------------------------------------------------------
# receiving tcp requests -sending files

def listen_req(ip: str, port=9100):

    adress = (ip, port)  # 9100 is the default TCP port number
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind(adress)
    tcp_sock.listen()
    active_tcp = 0
    if DEBUG:
        print(f"Listening to tcp calls in port {port}")

    while True:
        client_socket, _ = tcp_sock.accept()
        request_handler = threading.Thread(
            target=handle_tcp_client, args=[client_socket])
        request_handler.start()
        active_tcp += 1
        print(f"tcp req accepted, now handling {active_tcp} tcp connections")


def make_packet(i=0, packets_for_ack=4, body=b''):
    return make_header(i, 4) + body


def handle_tcp_client(client_socket: socket.socket):
    # in my protocol the one requesting the tcp connection can just request files

    if DEBUG:
        print("accepting connection")
    # perform handshake
    mssg = ACCEPT_CONNECTION
    client_socket.send(make_packet(body=mssg))
    connected = True

    # manage acks

    while connected:
        request_packet = client_socket.recv(BUFFER_SIZE)
        while (request_packet == b''):
            request_packet = client_socket.recv(BUFFER_SIZE)

        _, _, reques_mssg = get_contents(request_packet)

        request_parse = reques_mssg.split(SEP)

        if request_parse[0] == FILE_REQUEST:
            filename = request_parse[1].decode(FORMAT)
            send_file(filename, client_socket)
        elif request_parse[0] == DISCONNECT_MESSAGE:
            client_socket.close()
            connected = False
        else:
            send_mssg(ERR_INVALID_REQ, client_socket)


def get_contents(packet: bytes):
    """returns packet_convention, last_ack, packet_contents"""
    packet_header = packet[:HEADER_LEN-1]
    packet_contents = packet[HEADER_LEN:]
    packet_convention = int(packet_header[:3].split()[0])
    last_ack = int(packet_header[4:].split()[0])
    return packet_convention, last_ack, packet_contents


def get_body(packet: bytes):
    return packet[HEADER_LEN:]


def send_mssg(mssg: bytes, dest_socket: socket.socket):

    if DEBUG:
        print(f"sending message {mssg}")
    stream = io.BytesIO(mssg)
    send_stream(stream, dest_socket)
    stream.close()


def send_file(filename: str, dest_socket: socket.socket):
    try:
        stream = open("test_files/" + filename, "rb")
        send_mssg(SUCCESS, dest_socket)
        send_stream(stream, dest_socket)
        stream.close()
    except FileNotFoundError:
        send_mssg(ERR_FILE_NF, dest_socket)


def recv_ack(source_socket: socket.socket) -> int:
    packet = source_socket.recv(BUFFER_SIZE)
    while packet == b'':
        packet = source_socket.recv(BUFFER_SIZE)
    ack_mssg = get_body(packet)

    mssg = ack_mssg.split(SEP)
    if mssg[0] != b"ACK":
        send_mssg(ERR_EXPECT_ACK, source_socket)
    else:
        try:
            return int(mssg[1])
        except:
            send_mssg(ERR_EXPECT_ACK, source_socket)

# TCP connection already opened


def send_stream(bytes_stream, dest_socket: socket.socket):

    available_space = BUFFER_SIZE - HEADER_LEN
    packet_buffer = [None] * CONTINOUS_PACKETS
    sent_packets = 0
    mssg_contents = bytes_stream.read(available_space)
    while mssg_contents != b'':

        # read from the stream and send send packets

        packet_buffer[sent_packets] = (mssg_contents)
        sent_packets += 1
        mssg_header = make_header(sent_packets)

        l = len(mssg_contents)
        if l < available_space:
            mssg_contents += b' ' * (available_space-l)
        mssg = mssg_header + mssg_contents

        if DEBUG:
            print(f"sender: Sending {mssg}")

        dest_socket.send(mssg)

        # check reception
        if sent_packets == CONTINOUS_PACKETS:
            if DEBUG:
                print("sender: checking acks")
            sent_packets = 0
            last_recv = recv_ack(dest_socket)
            while (last_recv != CONTINOUS_PACKETS):
                if DEBUG:
                    print(f"error last ack is {last_recv}")
                mssg_contents = packet_buffer[last_recv + 1]
                mssg_header = make_header(last_recv, 1)
                mssg = mssg_header + mssg_contents
                dest_socket.send(mssg)

                last_recv = recv_ack(dest_socket)

        # continue
        mssg_contents = bytes_stream.read(available_space)

    # manage tail (remaning non Acked messages)
    # empty message demands ack

    mssg_header = make_header(sent_packets)
    mssg_contents = b''
    mssg = mssg_header + mssg_contents
    dest_socket.send(mssg)
    last_recv = recv_ack(dest_socket)
    while (last_recv != sent_packets):
        if DEBUG:
            print(
                f"error in tail last ack is {last_recv}, sent packets is {sent_packets}")
        mssg_contents = packet_buffer[last_recv + 1]
        mssg_header = make_header(last_recv + 1)
        mssg = mssg_header + mssg_contents
        dest_socket.send(mssg)

        last_recv = recv_ack(dest_socket)

    mssg_header = make_header(0, 1)
    dest_socket.send(mssg_header + END_OF_DATA)


# --------------------------------------------------------------------------------------------
# sending tcp requests -receiving files
""" opens a tcp connection and requests is a list of commands"""


def get_file(filename: str, source_sock: socket.socket):

    if DEBUG:
        print(f"getting file {filename}")
    request_body = FILE_REQUEST + SEP + filename.encode(FORMAT)
    packet = make_packet(body=request_body)
    source_sock.send(packet)

    if DEBUG:
        print("checking file exists")
    result = get_message(source_sock).split(SEP)[0]
    if result == SUCCESS:
        if DEBUG:
            print(" file found !")

        new_file = open(filename, "wb")
        get_stream(new_file, source_sock)
        new_file.close()
    else:
        print("ERROR:" + result.decode(FORMAT))


def open_connection(adress, requests=[]):

    if DEBUG:
        print(f"attempting to connect to {adress}")
    dest_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Handshake
    dest_sock.connect(adress)
    # checking answer
    answer_packet = dest_sock.recv(BUFFER_SIZE)
    while answer_packet == b'':  # must get a valid answer
        answer_packet = dest_sock.recv(BUFFER_SIZE)
    answer_packet_contents = get_body(answer_packet)
    result = answer_packet_contents.split(SEP)[0]

    # connection accepted !
    print("receiver : connection  ")
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

        dest_sock.send(make_packet(body=DISCONNECT_MESSAGE))
        dest_sock.close()


def send_ack(n, dest_socket: socket.socket):
    mssg_header = make_header(0)
    mssg = mssg_header + ACK(n)
    dest_socket.send(mssg)


def get_message(source_socket):
    mssg_stream = io.BytesIO(b"")
    get_stream(mssg_stream, source_socket)
    mssg = mssg_stream.getvalue()
    mssg_stream.close()
    return mssg


def get_stream(write_stream, source_socket: socket.socket):

    next_missing = 1
    remaining_data = True
    packet_buffer = [None] * CONTINOUS_PACKETS
    while remaining_data:

        if DEBUG:
            print("receiver :receiving packet")

        try:

            data = recv_timeout(source_socket, 100)
            if DEBUG:
                print(f"receiver : {data}")

            # check if packet is next in order
            packets_for_ack, seq_index, contents = get_contents(data)

            if contents == b'':
                if DEBUG:
                    print("sending ack for tail")
                send_ack(next_missing-1, source_socket)

            elif contents == END_OF_DATA:
                remaining_data = False
            elif seq_index != next_missing:
                if DEBUG:
                    print(
                        f"missing packet {seq_index} next_missing: {next_missing}")
                packet_buffer[seq_index] = contents
            else:
                write_stream.write(contents)
                next_missing += 1
                # refill stream
                while next_missing < CONTINOUS_PACKETS and packet_buffer[next_missing] != None:
                    if DEBUG:
                        print("time to refill")
                    write_stream.write(packet_buffer[next_missing])
                    packet_buffer[next_missing] = None
                    next_missing += 1

        except socket.timeout:
            send_ack(next_missing - 1, source_socket)

        if DEBUG:
            print("receiver : packet_received")

        if next_missing == CONTINOUS_PACKETS + 1:

            send_ack(next_missing - 1, source_socket)
            next_missing = 1
