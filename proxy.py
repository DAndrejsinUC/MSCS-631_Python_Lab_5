from socket import *
import sys
import os

if len(sys.argv) <= 1:
    print('Usage : "python ProxyServer.py server_ip"\n[server_ip : It is the IP Address Of Proxy Server')
    sys.exit(2)

# Create a server socket, bind it to a port and start listening
tcpSerSock = socket(AF_INET, SOCK_STREAM)
tcpSerSock.bind((sys.argv[1], 8888))
tcpSerSock.listen(5)

while 1:
    # Strat receiving data from the client
    print('Ready to serve...')
    tcpCliSock, addr = tcpSerSock.accept()
    print('Received a connection from:', addr)

    message = tcpCliSock.recv(4096).decode()
    print(message)

    parts = message.split()
    if len(parts) < 2:
        tcpCliSock.close()
        continue

    # Extract the filename from the given message
    print(parts[1])
    url = parts[1]

    if url.startswith("/"):
        url = url[1:]

    if url.startswith("http://"):
        url = url[len("http://"):]

    filename = url
    print(filename)

    fileExist = "false"
    filetouse = "/" + filename
    print(filetouse)

    url_parts = filename.split("/", 1)
    hostn = url_parts[0]
    path = "/"
    if len(url_parts) > 1:
        path = "/" + url_parts[1]

    cache_path = "./" + filename
    cache_dir = os.path.dirname(cache_path)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)

    try:
        # Check wether the file exist in the cache
        f = open(cache_path, "rb")
        outputdata = f.read()
        fileExist = "true"

        # ProxyServer finds a cache hit and generates a response message
        tcpCliSock.sendall(outputdata)

        print('Read from cache')
        f.close()

    # Error handling for file not found in cache
    except IOError:
        if fileExist == "false":
            # Create a socket on the proxyserver
            c = socket(AF_INET, SOCK_STREAM)
            print(hostn)

            try:
                # Connect to the socket to port 80
                c.connect((hostn, 80))

                # Create a temporary file on this socket and ask port 80
                # for the file requested by the client
                request = (
                    f"GET {path} HTTP/1.0\r\n"
                    f"Host: {hostn}\r\n"
                    f"Connection: close\r\n\r\n"
                )
                c.sendall(request.encode())

                # Read the response into buffer
                buffer = b""
                while True:
                    data = c.recv(4096)
                    if not data:
                        break
                    buffer += data

                # Create a new file in the cache for the requested file.
                # Also send the response in the buffer to client socket
                # and the corresponding file in the cache
                tmpFile = open(cache_path, "wb")
                tmpFile.write(buffer)
                tmpFile.close()
                tcpCliSock.sendall(buffer)
                c.close()

            except Exception as e:
                print("Illegal request")
                print(e)
                tcpCliSock.sendall(b"HTTP/1.0 400 Bad Request\r\nContent-Type:text/html\r\n\r\n")
                tcpCliSock.sendall(b"<html><body><h1>400 Bad Request</h1></body></html>")

        else:
            # HTTP response message for file not found
            tcpCliSock.sendall(b"HTTP/1.0 404 Not Found\r\nContent-Type:text/html\r\n\r\n")
            tcpCliSock.sendall(b"<html><body><h1>404 Not Found</h1></body></html>")

    # Close the client and the server sockets
    tcpCliSock.close()

tcpSerSock.close()