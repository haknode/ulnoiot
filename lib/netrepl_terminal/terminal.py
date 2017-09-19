#!/usr/bin/env python3
#
# Terminal program to connect to encrypted netrepl
#
# Parameters: address [port] [key]
# key needs to be 256bit in either bytes or hex notation,
# if key is not given it is read as newline terminated 64 byte hex notation from stdin
#
# author: ulno
# create date: 2017-09-16
#
# based on telnet example at http://www.binarytides.com/code-telnet-client-sockets-python/

MAGIC = b"UlnoIOT-NetREPL:"

import socket, select, sys, os, time
import chacha

def main():
    if len(sys.argv) < 2:
        print('Usage : python terminal.py hostname [port] [key]')
        sys.exit(1)

    host = sys.argv[1]
    port = 23
    key = None
    if len(sys.argv) >= 2:
        if len(sys.argv[2])<10: # could be port
            port = int(sys.argv[2])
            if len(sys.argv) >= 3:
                key = sys.argv[3].encode()
        else:
            key = sys.argv[2].encode()

    if key is None:
        print('Enter key (32bytes as hex->64bytes):')
        key=sys.stdin.readline().strip().encode()
        if len(key)!=64:
            print("Key has to specified as 64 byte hex. Exiting.")
            sys.exit(1)
    if len(key)==64:
        key=bytes.fromhex(key)
    if len(key)!=32:
        print("Key doesn't resolve to 256bit (32 bytes). Exiting.")
        sys.exit(1)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    # connect to remote host
    try:
        s.connect((host, port))
    except:
        print('\nterminal: Unable to connect. Exiting.')
        sys.exit()

    print('\nterminal: Connected to remote host.')
    print('terminal: Sending initialization and session key.\n')
    cc_out = chacha.ChaCha(key,bytes(8),socket=s) # TODO: consider IV here? sync with netrepl
    key_in = os.urandom(32)
    iv_in = os.urandom(8)

    cc_out.send(MAGIC+key_in+iv_in)  # send the key

    cc_in = chacha.ChaCha(key_in, iv_in,socket=s)

    print('terminal: Waiting for connection.\n')
    time.sleep(2)
    #print('terminal: Requesting startscreen.\n')
    #cc_out.send(b"help\r\n")

    while True:
        socket_list = [sys.stdin, s]

        # Get the list sockets which are readable
        read_sockets, write_sockets, error_sockets = \
            select.select(socket_list, [], [])

        for sock in read_sockets:
            # incoming message from remote server
            if sock == s:
                (data,l) = cc_in.receive()

                # TODO: figure out how to detect conenction close
                # #print("recvd:",data)
                # if not data:
                #     print('\nterminal: Connection closed.')
                #     sys.exit()
                # else:
                if l>0:
                    # print data
                    sys.stdout.write(bytes(data[0:l]).decode())
                    #print("data:", str(data[0:l]))
                    sys.stdout.flush()

            # user entered a message
            else:
                msg = (sys.stdin.readline().strip()+'\r\n').encode()
                cc_out.send(msg)

# main function
if __name__ == "__main__":
    main()
