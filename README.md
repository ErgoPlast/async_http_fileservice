Тестирование http сервера:

Для тестирования в коде описаны файлы file1, file2

Чтение блока:
curl -X GET http://127.0.0.1:8080/file1.txt
Вставка данных:
curl -X POST -d "new data" http://127.0.0.1:8080/file1.txt
Перезапись данных:
curl -X PUT -d "overwrite" http://127.0.0.1:8080/file1.txt
Удаление блока:
curl -X DELETE http://127.0.0.1:8080/file1.txt
