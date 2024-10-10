import socket

# サーバーIPとポートの設定
SERVER_IP = '10.30.6.73'
PORT = 5000

# サーバーソケットの作成
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, PORT))
server_socket.listen(1)

print(f"サーバーが {SERVER_IP}:{PORT} で待機しています...")

# クライアントの接続を待機
conn, addr = server_socket.accept()
print(f"接続元: {addr} が接続しました")

while True:
    data = conn.recv(1024).decode()
    if not data:
        break
    print(f"受信データ: {data}")

    response = f"受信したデータ: {data}"
    conn.send(response.encode())

conn.close()
server_socket.close()