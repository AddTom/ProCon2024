# send.py

import sqlite3
import socket
import logging

# サーバーIPとポートの設定
SERVER_IP = '10.30.6.80'
PORT = 5000

GARBAGE_TYPES = ['ペットボトル', 'スチール缶', 'アルミ缶', 'スプレー缶', '中身有容器']

def get_ids():
    try:
        conn = sqlite3.connect('garbage.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM bins")
        ids = [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"SQLiteエラー: {e}")
        ids = []
    finally:
        if conn:
            conn.close()
    return ids

# クライアントソケットの作成
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

ids = get_ids()

# データ送信
try:
    while True:
        print("既存のbin_idを選んでください:", ids)
        bin_id = input("bin_id: ")
        if bin_id not in ids:
            print("無効なbin_idです。もう一度入力してください。")
            continue

        print("ゴミの種類を選んでください:", GARBAGE_TYPES)
        garbage_type = input("garbage_type: ")
        if garbage_type not in GARBAGE_TYPES:
            print("無効なゴミの種類です。もう一度入力してください。")
            continue

        message = f"{bin_id},{garbage_type}"
        client_socket.send(message.encode())

        response = client_socket.recv(1024).decode()
        print(f"サーバー応答: {response}")

        if input("続けますか？ (y/n): ").lower() != 'y':
            break

finally:
    client_socket.close()