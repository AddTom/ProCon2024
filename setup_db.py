# setup_db.py

import sqlite3  # SQLiteデータベース用のモジュールをインポート
import logging   # ロギング用のモジュールをインポート

DATABASE = 'garbage.db'  # 使用するデータベースファイルの名前を定義

def create_tables():
    """
    データベースにテーブルを作成する関数。

    概要:
        bins、garbage、capacitiesの3つのテーブルを作成する。
        すでに存在する場合は新しく作成しない。

    変数:
        conn (sqlite3.Connection): データベース接続オブジェクト
    引数:
        なし
    戻り値:
        なし
    """
    conn = None  # データベース接続を初期化
    try:
        # データベースに接続
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()  # カーソルオブジェクトを取得
        
        # bins テーブルの作成
        c.execute(''' 
            CREATE TABLE IF NOT EXISTS bins (
                id TEXT PRIMARY KEY,  # ゴミ箱のID
                location TEXT NOT NULL  # ゴミ箱の場所
            )
        ''')

        # garbage テーブルの作成
        c.execute(''' 
            CREATE TABLE IF NOT EXISTS garbage (
                bin_id TEXT,  # ゴミ箱のID
                type TEXT,    # ゴミの種類
                count INTEGER,  # ゴミの数
                PRIMARY KEY (bin_id, type),  # bin_idとtypeの組み合わせを主キーに設定
                FOREIGN KEY (bin_id) REFERENCES bins (id)  # binsテーブルとの外部キー制約
            )
        ''')

        # capacities テーブルの作成
        c.execute(''' 
            CREATE TABLE IF NOT EXISTS capacities (
                bin_id TEXT,  # ゴミ箱のID
                type TEXT,    # ゴミの種類
                capacity INTEGER,  # ゴミ箱の容量
                PRIMARY KEY (bin_id, type),  # bin_idとtypeの組み合わせを主キーに設定
                FOREIGN KEY (bin_id) REFERENCES bins (id)  # binsテーブルとの外部キー制約
            )
        ''')

        conn.commit()  # 変更をデータベースにコミット
        logging.info("テーブルの作成に成功しました。")  # 成功メッセージをログに記録

    except sqlite3.OperationalError as oe:
        logging.error(f"操作エラー: {oe}")  # 操作エラーが発生した場合、ログに記録
    except sqlite3.IntegrityError as ie:
        logging.error(f"整合性エラー: {ie}")  # 整合性エラーが発生した場合、ログに記録
    except sqlite3.Error as e:
        logging.error(f"SQLiteエラー: {e}")  # その他のSQLiteエラーが発生した場合、ログに記録
    except Exception as ex:
        logging.error(f"予期しないエラー: {ex}")  # その他の予期しないエラーが発生した場合、ログに記録
    finally:
        if conn:  # 接続がある場合
            conn.close()  # データベース接続を閉じる

if __name__ == '__main__':
    create_tables()  # スクリプトが直接実行された場合、テーブル作成関数を実行
