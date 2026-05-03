import socket
import select
import random
import struct
import zlib
import sys
import os

LOSS_PROB = 0.3 
TIMEOUT = 1.0 
CHUNK_SIZE = 1000


TYPE_DATA = 0
TYPE_ACK = 1 
TYPE_FIN = 2

def calc_crc32(data):
    return zlib.crc32(data)

def make_pkt(pkt_type, seq, data=b''):
    data_len = len(data)
    header = struct.pack('!BBH', pkt_type, seq, data_len)
    chk = calc_crc32(header + data)
    return struct.pack('!BBHI', pkt_type, seq, data_len, chk) + data

def unpack_pkt(pkt):
    if len(pkt) < 8:
        return None
    pkt_type, seq, data_len, chk = struct.unpack('!BBHI', pkt[:8])
    if len(pkt) != 8 + data_len:
        return None
    data = pkt[8:]
    computed_chk = calc_crc32(struct.pack('!BBH', pkt_type, seq, data_len) + data)
    if computed_chk != chk:
        return None  # Поврежден
    return pkt_type, seq, data

def udt_send(sock, pkt, addr, loss_prob=LOSS_PROB):
    if random.random() < loss_prob:
        print("Simulated packet loss")
        return
    sock.sendto(pkt, addr)

def client(host, port, input_filename):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        addr = (host, port)

        if not os.path.exists(input_filename):
            print(f"Error: File {input_filename} not found")
            return

        with open(input_filename, 'rb') as f:
            file_data = f.read()

        chunks = [file_data[i:i + CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]

        seq = 0
        for chunk in chunks:
            pkt = make_pkt(TYPE_DATA, seq, chunk)
            while True:
                udt_send(sock, pkt, addr)
                ready = select.select([sock], [], [], TIMEOUT)
                if ready[0]:
                    try:
                        rcv_pkt, _ = sock.recvfrom(1024 + 100)
                        res = unpack_pkt(rcv_pkt)
                        if res:
                            r_type, r_seq, r_data = res
                            if r_type == TYPE_ACK and r_seq == seq:
                                print(f"ACK {seq} received for data packet")
                                break
                    except Exception as e:
                        print(f"Error receiving: {e}")
                else:
                    print(f"Timeout for seq {seq}, resending")
            seq = 1 - seq

        # Отправка FIN с ожиданием ACK
        fin_seq = seq
        fin_pkt = make_pkt(TYPE_FIN, fin_seq)
        while True:
            udt_send(sock, fin_pkt, addr)
            ready = select.select([sock], [], [], TIMEOUT)
            if ready[0]:
                try:
                    rcv_pkt, _ = sock.recvfrom(1024 + 100)
                    res = unpack_pkt(rcv_pkt)
                    if res:
                        r_type, r_seq, r_data = res
                        if r_type == TYPE_ACK and r_seq == fin_seq:
                            print(f"ACK {fin_seq} received for FIN")
                            break
                except Exception as e:
                    print(f"Error receiving: {e}")
            else:
                print(f"Timeout for FIN, resending")

        sock.close()
        print("File transfer completed")
    except Exception as e:
        print(f"Client error: {e}")

def server(port, output_filename):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))

        expected_seq = 0
        received_chunks = []
        done = False
        post_fin_timeout = 5.0

        while True:
            # Ожидание пакета с таймаутом (после FIN - ограниченный)
            timeout = post_fin_timeout if done else None
            ready = select.select([sock], [], [], timeout)
            if not ready[0]:
                if done:
                    print("No more packets after FIN, shutting down server")
                    break
                continue

            try:
                rcv_pkt, addr = sock.recvfrom(1024 + 100)
                res = unpack_pkt(rcv_pkt)
                if not res:
                    print("Corrupt or invalid packet received, ignoring")
                    continue

                r_type, r_seq, r_data = res

                if done:
                    # Обработка дубликатов FIN после завершения
                    if r_type == TYPE_FIN and r_seq != expected_seq:
                        print(f"Duplicate FIN {r_seq} received after completion, sending ACK")
                        ack_pkt = make_pkt(TYPE_ACK, r_seq)
                        udt_send(sock, ack_pkt, addr)
                    else:
                        print("Unexpected packet after FIN, ignoring")
                    continue

                if r_type == TYPE_DATA or r_type == TYPE_FIN:
                    if r_seq == expected_seq:
                        if r_type == TYPE_DATA:
                            if len(r_data) > 0:
                                received_chunks.append(r_data)
                                print(f"Data packet {r_seq} received and accepted")
                            expected_seq = 1 - expected_seq
                        elif r_type == TYPE_FIN:
                            print(f"FIN packet {r_seq} received, ending transfer")
                            done = True
                            expected_seq = 1 - expected_seq
                    else:
                        print(f"Unexpected seq {r_seq} (expected {expected_seq}), treating as duplicate")

                    # Отправка ACK
                    ack_pkt = make_pkt(TYPE_ACK, r_seq)
                    udt_send(sock, ack_pkt, addr)
                else:
                    print("Unknown packet type, ignoring")
            except Exception as e:
                print(f"Server receive error: {e}")

        if done:
            with open(output_filename, 'wb') as f:
                f.write(b''.join(received_chunks))
            print("File received and saved")
        else:
            print("Transfer not completed, no file saved")

        sock.close()
    except Exception as e:
        print(f"Server error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        server(12345, "output.txt")
    else:
        client("localhost", 12345, "alice.txt")
