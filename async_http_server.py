import asyncio
import os

class FileHandler:
    def __init__(self, filename, block_size):
        self.filename = filename
        self.block_size = block_size
        self.position = 0  # Текущая позиция

    async def get_block(self):
        """Чтение текущего блока файла."""
        try:
            with open(self.filename, 'rb') as f:
                f.seek(self.position)
                data = f.read(self.block_size)
                self.position += len(data)
            return data
        except FileNotFoundError:
            return b"File not found."

    async def insert_data(self, data):
        """Вставка данных в текущую позицию."""
        try:
            with open(self.filename, 'r+b') as f:
                f.seek(self.position)
                remaining_data = f.read()
                f.seek(self.position)
                f.write(data + remaining_data)
                self.position += len(data)
        except FileNotFoundError:
            return b"File not found."

    async def overwrite_data(self, data):
        """Перезапись данных в текущей позиции."""
        try:
            with open(self.filename, 'r+b') as f:
                f.seek(self.position)
                f.write(data)
                self.position += len(data)
        except FileNotFoundError:
            return b"File not found."

    async def delete_block(self):
        try:
            with open(self.filename, 'r+b') as f:
                f.seek(self.position)
                print(self.position)
                remaining_data = f.read()  # Читаем всё после текущей позиции
                f.seek(self.position)  # Возвращаемся к началу блока
                f.truncate()  # Обрезаем файл
                if len(remaining_data) > self.block_size:
                    f.write(remaining_data[self.block_size:])  # Пишем данные без блока
            return b"Block deleted successfully."
        except FileNotFoundError:
            return b"File not found."
        except Exception as e:
            return f"Error deleting block: {e}".encode()

class AsyncHTTPServer:
    def __init__(self, host, port, file_configs):
        self.host = host
        self.port = port
        self.handlers = {
            config[0]: FileHandler(config[0], config[1]) for config in file_configs
        }

    async def handle_client(self, reader, writer):
        request = await reader.read(1024)  # Читаем запрос
        response = await self.route_request(request)
        writer.write(response)  # Пишем ответ
        await writer.drain()
        writer.close()

    async def route_request(self, request):
        """Маршрутизация запросов."""
        try:
            request_line = request.split(b'\r\n')[0].decode()
            method, path, _ = request_line.split()
            filename = path.lstrip("/")
            if filename not in self.handlers:
                return self.http_response(404, b"File not registered")

            handler = self.handlers[filename]
            if method == "GET":
                data = await handler.get_block()
                return self.http_response(200, data)
            elif method == "POST":
                body = request.split(b'\r\n\r\n', 1)[1]
                await handler.insert_data(body)
                return self.http_response(200, b"Data inserted")
            elif method == "PUT":
                body = request.split(b'\r\n\r\n', 1)[1]
                await handler.overwrite_data(body)
                return self.http_response(200, b"Data overwritten")
            elif method == "DELETE":
                await handler.delete_block()
                return self.http_response(200, b"Block deleted")
            else:
                return self.http_response(405, b"Method not allowed")
        except Exception as e:
            return self.http_response(500, f"Server error: {e}".encode())

    def http_response(self, status_code, body):
        """Создание HTTP-ответа."""
        status_messages = {
            200: "OK",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error",
        }
        status_message = status_messages.get(status_code, "Unknown Status")
        response = (
            f"HTTP/1.1 {status_code} {status_message}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Content-Type: text/plain\r\n"
            f"\r\n"
        ).encode() + body
        return response

    async def run(self):
        """Запуск сервера."""
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        async with server:
            print(f"Server running on {self.host}:{self.port}")
            await server.serve_forever()


if __name__ == "__main__":
    # Настройка файлов и запуск сервера
    file_configs = [
        ("file1.txt", 512),  # файл и размер блока
        ("file2.txt", 1024),
    ]

    # Создаём тестовые файлы
    for filename, _ in file_configs:
        with open(filename, "wb") as f:
            f.write(b"Test content for " + filename.encode())

    server = AsyncHTTPServer('127.0.0.1', 8080, file_configs)
    asyncio.run(server.run())
