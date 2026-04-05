import socket
import base64
import ssl
import sys


class SMTPClient:
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.sock = None
    
    def _recv(self, expected_code=None):
        response = self.sock.recv(1024).decode()
        print(f"<<< {response.strip()}")
        if expected_code and not response.startswith(str(expected_code)):
            raise Exception(f"Expected {expected_code}, got {response[:50]}")
        return response
    
    def _send(self, command, expected_code=None):
        print(f">>> {command}")
        self.sock.send((command + "\r\n").encode())
        return self._recv(expected_code)
    
    def connect(self):
        context = ssl.create_default_context()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server, self.port))
        self.sock = context.wrap_socket(self.sock, server_hostname=self.server)
        self._recv(220)
        # EHLO обязателен!
        self._send("EHLO localhost", 250)
    
    def login(self, email, password):
        self._send("AUTH LOGIN", 334)
        self._send(base64.b64encode(email.encode()).decode(), 334)
        self._send(base64.b64encode(password.encode()).decode(), 235)
    
    def send_mail(self, from_addr, to_addr, message):
        self._send(f"MAIL FROM:<{from_addr}>", 250)
        self._send(f"RCPT TO:<{to_addr}>", 250)
        self._send("DATA", 354)
        self._send(f"{message}\r\n.", 250)
    
    def quit(self):
        self._send("QUIT", 221)
        self.sock.close()
    
    def run(self, from_addr, to_addr, message, password):
        self.connect()
        self.login(from_addr, password)
        self.send_mail(from_addr, to_addr, message)
        self.quit()


def main():
    if len(sys.argv) != 4:
        print("Usage: python smtp_client.py <from> <to> <message>")
        
        sys.exit(1)
    

    from_addr = sys.argv[1]
    to_addr = sys.argv[2]
    message = sys.argv[3]
    
    password = input("email_password:")
    
    client = SMTPClient("smtp.gmail.com", 465)
    client.run(from_addr, to_addr, message, password)
    
    print("\nEmail sent!")


if __name__ == "__main__":
    main()


