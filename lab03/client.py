import socket
import sys


def create_request(filename: str) -> bytes:
    """Создает HTTP GET запрос"""
    request = (
        f"GET /{filename} HTTP/1.1\r\n"
        f"Host: localhost\r\n"
        "User-Agent: PythonClient/1.0\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    return request.encode()


def parse_response(response: bytes) -> None:
    """Разбирает и выводит HTTP ответ"""
    try:
        header_part, body_part = response.split(b"\r\n\r\n", 1)
        headers = header_part.decode("utf-8", errors="ignore")
        
        status_line = headers.split("\r\n")[0]
        
        print("=" * 50)
        print("HTTP RESPONSE")
        print("=" * 50)
        print(f"Status: {status_line}")
        print("-" * 50)
        print("Headers:")
        print(headers)
        print("-" * 50)
        print("Body:")
        
        try:
            body_text = body_part.decode("utf-8")
            print(body_text)
        except UnicodeDecodeError:
            print(f"(binary data, {len(body_part)} bytes)")
            
    except Exception as e:
        print(f"Error parsing response: {e}")
        print(response[:500])


def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: python client.py <server_host> <server_port> <filename>")
        print("Example: python client.py localhost 8080 index.html")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        try:
            print(f"Connecting to {host}:{port}...")
            client.connect((host, port))
            
        
            request = create_request(filename)
            print(f"Requesting: /{filename}")
            client.sendall(request)
            
            response_data = b""
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response_data += chunk
            
            
            parse_response(response_data)
            
        except ConnectionRefusedError:
            print(f"Error: Cannot connect to {host}:{port}. Server is not running.")
            sys.exit(1)
        except socket.timeout:
            print("Error: Connection timeout")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()