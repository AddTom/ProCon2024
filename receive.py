# receive.py

import sqlite3
import socket
import logging

GARBAGE_TYPES = ['ペットボトル', 'スチール缶', 'アルミ缶', 'スプレー缶', '中身有容器']

# サーバーの設定
SERVER_IP = '10.30.6.80'
PORT = 5000

DATABASE = 'garbage.db'

class LANServer:
    def __init__(self):
        # サーバーソケットの作成
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((SERVER_IP, PORT))
        self.server_socket.listen(1)
        logging.info(f"サーバーが {SERVER_IP}:{PORT} で待機しています...")

    def start(self):
        while True:
            # クライアントからの接続を待機
            conn, addr = self.server_socket.accept()
            logging.info(f"接続元: {addr} が接続しました")
            
            with conn:
                while True:
                    data = conn.recv(1024).decode()
                    if not data:
                        break
                    logging.info(f"受信データ: {data}")
                    
                    # メッセージの形式: "bin_id,garbage_type"
                    try:
                        bin_id, garbage_type = data.split(',')
                        
                        if garbage_type in GARBAGE_TYPES:
                            self.update_count(bin_id, garbage_type)
                            response = f"ゴミ箱 {bin_id} の {garbage_type} をカウントしました。"
                        else:
                            response = f"未知のゴミの種類: {garbage_type}"
                            logging.warning(response)
                        
                    except ValueError as e:
                        response = f"メッセージペイロードの解析に失敗しました: {data}, エラー: {e}"
                        logging.error(response)
                    
                    conn.send(response.encode())

    def update_count(self, bin_id, garbage_type):
        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            
            # countを加算
            c.execute('''
                INSERT INTO garbage (bin_id, type, count)
                VALUES (?, ?, 1)
                ON CONFLICT(bin_id, type) DO UPDATE SET count = count + 1
            ''', (bin_id, garbage_type))
            
            conn.commit()
            logging.info(f"ゴミ箱 {bin_id} とゴミの種類 {garbage_type} のカウントを更新しました")
        except sqlite3.Error as e:
            logging.error(f"SQLiteエラー: {e}")
        finally:
            if conn:
                conn.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    lan_server = LANServer()
    lan_server.start()