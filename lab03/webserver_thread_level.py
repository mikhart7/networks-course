import socket
import sys
import threading
from pathlib import Path


ROOT = Path(__file__).with_name("static")
semaphore = None


def response(status: str, body: bytes) -> bytes:
    headers = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Connection: close\r\n\r\n"
    )
    return headers.encode() + body


def handle(client: socket.socket) -> None:
    try:
        request = client.recv(4096).decode("utf-8", errors="ignore")
        try:
            method, path, _ = request.splitlines()[0].split()
        except (IndexError, ValueError):
            client.sendall(response("400 Bad Request", b"400 Bad Request"))
            return

        if method != "GET":
            client.sendall(response("405 Method Not Allowed", b"405 Method Not Allowed"))
            return

        name = path.lstrip("/") or "index.html"
        
        if ".." in name:
            client.sendall(response("403 Forbidden", b"403 Forbidden"))
            return

        try:
            body = (ROOT / name).read_bytes()
            client.sendall(response("200 OK", body))
        except FileNotFoundError:
            not_found_body = b"<h1>404 Not Found</h1><p>File not found</p>"
            client.sendall(response("404 Not Found", not_found_body))
    finally:
        client.close()
        semaphore.release()  # Освобождаем слот


def main() -> None:
    global semaphore
    
    if len(sys.argv) != 3:
        print("Usage: python server.py <port> <concurrency_level>")
        print("Example: python server.py 8080 5")
        sys.exit(1)

    port = int(sys.argv[1])
    concurrency_level = int(sys.argv[2])
    
    # Создаем семафор для ограничения потоков
    semaphore = threading.Semaphore(concurrency_level)
    
    ROOT.mkdir(exist_ok=True)
    
    index_file = ROOT / "index.html"
    if not index_file.exists():
        index_file.write_text("<h1>Welcome!</h1><p>Server is running</p>", encoding="utf-8")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", port))
        server.listen()
        print(f"Server running at http://127.0.0.1:{port}")
        print(f"Max concurrent threads: {concurrency_level}")
        print("Press Ctrl+C to stop")

        try:
            while True:
                client, addr = server.accept()
                print(f"Connection from {addr}")
                
                # Блокируется, если достигнут лимит потоков
                semaphore.acquire()
                
                thread = threading.Thread(target=handle, args=(client,))
                thread.start()
        except KeyboardInterrupt:
            print("\nServer stopped")


if __name__ == "__main__":
    main()