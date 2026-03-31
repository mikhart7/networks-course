import socket
import sys
import threading
from datetime import datetime


LOG_FILE = "proxy.log"


def handle_client(client_socket):
    try:
        request = client_socket.recv(4096)
        
        
        first_line = request.split(b'\n')[0].decode()
        method, path, _ = first_line.split()
        
       
        if path.startswith('/'):
            path = path[1:]
        
        host = path.split('/')[0]
        file_path = '/' + '/'.join(path.split('/')[1:]) if '/' in path else '/'
        
        
        body = b""
        if method == "POST" and b"\r\n\r\n" in request:
            body = request.split(b"\r\n\r\n", 1)[1]
        
     
        target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target.connect((host, 80))
        
        
        req = f"{method} {file_path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n"
        if method == "POST" and body:
            req += f"Content-Length: {len(body)}\r\n"
        req += "\r\n"
        
        target.send(req.encode() + body)
        
      
        response = b""
        while True:
            data = target.recv(4096)
            if not data:
                break
            response += data
        
        
        try:
            status = response.split(b'\n')[0].split(b' ')[1]
        except:
            status = b"500"
        
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now()} - {host}{file_path} - {status.decode()}\n")
    
        client_socket.send(response)
        target.close()
        
    except Exception:
        client_socket.send(b"HTTP/1.1 502 Bad Gateway\r\n\r\nError")
    finally:
        client_socket.close()


def main():
    port = int(sys.argv[1])
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', port))
    server.listen(5)
    
    print(f"Proxy on http://localhost:{port}")
    
    while True:
        client, _ = server.accept()
        threading.Thread(target=handle_client, args=(client,)).start()


if __name__ == "__main__":
    main()