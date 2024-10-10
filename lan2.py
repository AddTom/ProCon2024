import socket

# サーバーIPとポートの設定
SERVER_IP = '10.30.6.73'
PORT = 5000

# クライアントソケットの作成
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

while True:
    message = input("送信データ: ")
    if not message:
        break
    client_socket.send(message.encode())

    response = client_socket.recv(1024).decode()
    print(f"サーバー応答: {response}")

client_socket.close()