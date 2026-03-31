import socket
import sys
import threading
from datetime import datetime


LOG_FILE = "proxy.log"
BLACKLIST_FILE = "blacklist.txt"


def load_blacklist():
    """Загружает черный список из файла"""
    try:
        with open(BLACKLIST_FILE, "r") as f:
            return [line.strip().lower() for line in f if line.strip()]
    except FileNotFoundError:
        return []


def is_blocked(host, blacklist):
    """Проверяет, заблокирован ли хост"""
    host = host.lower()
    for blocked in blacklist:
        if host == blocked or host.endswith("." + blocked):
            return True
    return False


def handle_client(client_socket, blacklist):
    try:
        request = client_socket.recv(4096)
        

        first_line = request.split(b'\n')[0].decode()
        method, path, _ = first_line.split()
        
       
        if path.startswith('/'):
            path = path[1:]
        
        host = path.split('/')[0]
        file_path = '/' + '/'.join(path.split('/')[1:]) if '/' in path else '/'
        
              
        if is_blocked(host, blacklist):
            print(f"Blocked: {host}")
            blocked_body = f"""<html><body>
<h1>403 Forbidden</h1>
<p>Access to {host} is blocked by proxy.</p>
</body></html>"""
            
            blocked_response = (
                f"HTTP/1.1 403 Forbidden\r\n"
                f"Content-Length: {len(blocked_body)}\r\n"
                f"Content-Type: text/html; charset=utf-8\r\n"
                f"Connection: close\r\n"
                f"\r\n"
                f"{blocked_body}"
            ).encode()
            
            client_socket.send(blocked_response)
            with open(LOG_FILE, "a") as f:
                f.write(f"{datetime.now()} - {host}{file_path} - BLOCKED\n")
            client_socket.close()
            return
        
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
    if len(sys.argv) != 2:
        print("Usage: python proxy.py <port>")
        sys.exit(1)
    
    port = int(sys.argv[1])
    
 
    blacklist = load_blacklist()
    print(f"Loaded {len(blacklist)} blocked domains")
    print("Blacklist:", blacklist)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', port))
    server.listen(5)
    
    print(f"Proxy on http://localhost:{port}")
    
    while True:
        client, _ = server.accept()
        threading.Thread(target=handle_client, args=(client, blacklist)).start()


if __name__ == "__main__":
    main()