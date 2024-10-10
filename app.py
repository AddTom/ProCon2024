# app.py

from flask import Flask, render_template, request, redirect, url_for, g, flash
import sqlite3 
import logging
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # 16バイトのランダムな16進数の秘密鍵を生成

DATABASE = 'garbage.db'

GARBAGE_TYPES = ['ペットボトル', 'スチール缶', 'アルミ缶', 'スプレー缶', '中身有容器']

def get_db():
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(DATABASE)
        except sqlite3.Error as e:
            logging.error(f"データベース接続エラー: {e}")
            raise
    return g.db

def percentage(garbage_data, capacity_data):
    capacities = {row[0]: row[1] for row in capacity_data}
    percentages = []

    for garbage_type, count in garbage_data:
        capacity = capacities.get(garbage_type, 1)  # 0除算対策でデフォルト値を1に設定
        percentage = (count / capacity) * 100
        percentages.append((garbage_type, count, capacity, percentage))
    
    return percentages

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    try:
        conn = get_db()
        cursor = conn.cursor()

        # ゴミ箱データを取得
        cursor.execute("SELECT * FROM bins")
        bins = cursor.fetchall()

        notifications = []

        for bin in bins:
            # ゴミの種類と数量を取得
            cursor.execute("SELECT type, count FROM garbage WHERE bin_id = ?", (bin[0],))
            garbage_data = cursor.fetchall()

            # 容量データを取得
            cursor.execute("SELECT type, capacity FROM capacities WHERE bin_id = ?", (bin[0],))
            capacity_data = cursor.fetchall()

            # パーセンテージ計算
            percentages = percentage(garbage_data, capacity_data)

            # 80%以上のゴミタイプをメッセージリストに追加
            message = [
                f"{garbage_type}が{percentage:.1f}%に達しています"
                for garbage_type, _, _, percentage in percentages if percentage >= 80
            ]

            # ゴミ箱とメッセージリストを追加
            notifications.append((bin, message))

    except sqlite3.Error as e:
        logging.error(f"ゴミ箱 取得エラー: {e}")
        notifications = []

    return render_template('index.html', bins=notifications)

@app.route('/bin/<string:bin_id>')
def bin_details(bin_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bins WHERE id = ?", (bin_id,))
        bin_data = cursor.fetchone()
        if bin_data is None:
            logging.error(f"ゴミ箱データが存在しません。")
        
        # ゴミの種類と数量を取得
        cursor.execute("SELECT type, count FROM garbage WHERE bin_id = ?", (bin_id,))
        garbage_data = cursor.fetchall()
        
        # 容量データを取得
        cursor.execute("SELECT type, capacity FROM capacities WHERE bin_id = ?", (bin_id,))
        capacity_data = cursor.fetchall()
        
        # パーセンテージ計算
        garbage_percentages = percentage(garbage_data, capacity_data)

    except sqlite3.Error as e:
        logging.error(f"ゴミ箱の詳細データ 取得エラー: {e}")
        garbage_percentages = []

    return render_template('bin_details.html', bin=bin_data, results=garbage_percentages)

@app.route('/new_bin', methods=['GET', 'POST'])
def new_bin():
    error_message = None 
    if request.method == 'POST':
        bin_id = request.form['bin_id']
        location = request.form['location']

        try:
            conn = get_db()
            c = conn.cursor()

            # 既にIDが存在するかをチェック
            c.execute('SELECT id FROM bins WHERE id = ?', (bin_id,))
            existing_bin = c.fetchone()

            if existing_bin:
                error_message = f"ゴミ箱ID {bin_id} は既に存在しています。"
            else:
                # ゴミ箱を新規登録
                c.execute('INSERT INTO bins (id, location) VALUES (?, ?)', (bin_id, location))

                for garbage_type in GARBAGE_TYPES:
                    c.execute('INSERT INTO garbage (bin_id, type, count) VALUES (?, ?, ?)', (bin_id, garbage_type, 0))
                    c.execute('INSERT INTO capacities (bin_id, type, capacity) VALUES (?, ?, ?)', (bin_id, garbage_type, 10))

                conn.commit()
                logging.info(f"ゴミ箱 {bin_id} が新規登録されました。")
                return redirect(url_for('index'))

        except sqlite3.Error as e:
            logging.error(f"SQLiteエラー: {e}")

        finally:
            if conn:
                conn.close()

    return render_template('new_bin.html', error_message=error_message)

@app.route('/search_bin', methods=['GET', 'POST'])
def search_bin():
    conn = get_db()
    c = conn.cursor()
    bin_data = None
    error_message = None

    if request.method == 'POST':
        bin_id = request.form.get('searched_bin_id', '')

        if not bin_id:
            return "ゴミ箱IDが必要です", 400

        c.execute('SELECT id, location FROM bins WHERE id = ?', (bin_id,))
        bin_data = c.fetchone()

        if bin_data:
            return redirect(url_for('bin_details', bin_id=bin_id))
        else:
            error_message = f"ゴミ箱ID {bin_id} は存在しません。"

    return render_template('search_bin.html', error_message=error_message)

@app.route('/reset_garbage', methods=['GET', 'POST'])
def reset_garbage():
    if request.method == 'POST':
        bin_id = request.form.get('bin_id')
        garbage_types = request.form.getlist('garbage_types')

        # ゴミの種類が選択されていない場合
        if not garbage_types:
            flash('ゴミの種類が選択されていません。', 'warning')
            return redirect(url_for('reset_garbage'))

        try:
            conn = get_db()
            c = conn.cursor()
            
            for garbage_type in garbage_types:
                c.execute('''
                    UPDATE garbage
                    SET count = 0
                    WHERE bin_id = ? AND type = ?
                ''', (bin_id, garbage_type))

            conn.commit()
            flash('ゴミの量がリセットされました。', 'success')
        except sqlite3.Error as e:
            flash(f'エラーが発生しました: {e}', 'error')
        finally:
            if conn:
                conn.close()

        return redirect(url_for('reset_garbage'))

    return render_template('reset_garbage.html', garbage_types=GARBAGE_TYPES)

@app.route('/edit_bin', methods=['GET', 'POST'])
def edit_bin():
    conn = get_db()
    c = conn.cursor()
    selected_bin_id = None
    bin_data = None
    capacity_data = None

    if request.method == 'POST':
        selected_bin_id = request.form.get('selected_bin_id', None)
        new_bin_id = request.form.get('new_bin_id', None)
        new_capacity = request.form.get('new_capacity', None)
        new_location = request.form.get('new_location', None)  # 新しい設置場所
        action = request.form['action']

        if action == 'select_bin' and selected_bin_id:
            # ゴミ箱のIDと設置場所を取得
            c.execute('SELECT id, location FROM bins WHERE id = ?', (selected_bin_id,))
            bin_data = c.fetchone()

            c.execute('SELECT capacity FROM capacities WHERE bin_id = ?', (selected_bin_id,))
            capacity_data = c.fetchone()

            if not bin_data:
                flash(f"ゴミ箱ID {selected_bin_id} は存在しません。", 'danger')
                return render_template('edit_bin.html', selected_bin_id=selected_bin_id, bin_data=bin_data, capacity=capacity_data)

        elif action == 'update_id' and selected_bin_id and new_bin_id:
            c.execute('SELECT id FROM bins WHERE id = ?', (new_bin_id,))
            if c.fetchone():
                flash(f"新しいゴミ箱ID {new_bin_id} は既に存在します。", 'danger')
                return render_template('edit_bin.html', selected_bin_id=selected_bin_id, bin_data=bin_data, capacity=capacity_data)

            c.execute('UPDATE bins SET id = ? WHERE id = ?', (new_bin_id, selected_bin_id))
            c.execute('UPDATE garbage SET bin_id = ? WHERE bin_id = ?', (new_bin_id, selected_bin_id))
            c.execute('UPDATE capacities SET bin_id = ? WHERE bin_id = ?', (new_bin_id, selected_bin_id))

            conn.commit()
            flash('ゴミ箱IDが更新されました。', 'success')

        elif action == 'update_location' and selected_bin_id and new_location:
            c.execute('UPDATE bins SET location = ? WHERE id = ?', (new_location, selected_bin_id))
            conn.commit()
            flash('ゴミ箱の設置場所が更新されました。', 'success')

        elif action == 'update_capacity' and selected_bin_id and new_capacity:
            c.execute('UPDATE capacities SET capacity = ? WHERE bin_id = ?', (new_capacity, selected_bin_id))
            conn.commit()
            flash('ゴミ箱の容量が更新されました。', 'success')

        elif action == 'delete' and selected_bin_id:
            try:
                c.execute('DELETE FROM garbage WHERE bin_id = ?', (selected_bin_id,))
                c.execute('DELETE FROM capacities WHERE bin_id = ?', (selected_bin_id,))
                c.execute('DELETE FROM bins WHERE id = ?', (selected_bin_id,))
                conn.commit()
                flash(f'ゴミ箱 {selected_bin_id} が削除されました。', 'success')
            except sqlite3.Error as e:
                flash(f'削除中にエラーが発生しました: {e}', 'danger')
            finally:
                selected_bin_id = None
                bin_data = None
                capacity_data = None

    if selected_bin_id:
        c.execute('SELECT id, location FROM bins WHERE id = ?', (selected_bin_id,))
        bin_data = c.fetchone()

        c.execute('SELECT capacity FROM capacities WHERE bin_id = ?', (selected_bin_id,))
        capacity_data = c.fetchone()

    return render_template('edit_bin.html', selected_bin_id=selected_bin_id, bin_data=bin_data, capacity=capacity_data)

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/memory_game')
def memory_game():
    return render_template('memory_game.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)