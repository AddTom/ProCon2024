import sys
import csv
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv1D, MaxPooling1D, Flatten, Dense,Dropout
#import tensorflow.keras.utils as pad_sequences
from tensorflow.keras.preprocessing.sequence import pad_sequences  # ここを修正
from tensorflow.keras import regularizers
import librosa
from pydub import AudioSegment
import io
import numpy as np
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def add_white_noise(signal, noise_factor=0.005):
    """音声信号にホワイトノイズを追加する関数"""
    noise = np.random.randn(len(signal))  # ホワイトノイズを生成
    augmented_signal = signal + noise_factor * noise  # 音声信号にノイズを追加
    return augmented_signal

def extract_features(file_path):
    """音声ファイルの読み込みとMFCC特徴量の抽出"""
    try:
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_frame_rate(44100).set_channels(1)
        raw_data = io.BytesIO()
        audio.export(raw_data, format="wav")
        raw_data.seek(0)
        y, sr = librosa.load(raw_data, sr=44100)
        
        # 元のデータのMFCCを抽出
        mfccs_original = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # ホワイトノイズを追加
        y_noisy = add_white_noise(y, noise_factor=0.005)
        
        # ホワイトノイズを追加したデータのMFCCを抽出
        mfccs_noisy = librosa.feature.mfcc(y=y_noisy, sr=sr, n_mfcc=13)

        return mfccs_original.T, mfccs_noisy.T  # 元のMFCCとノイズを追加したMFCCを返す
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, None

# CSVファイルのパス
csv_file = 'Training1.csv'

# データを格納するリストを初期化
data = []

# CSVファイルを読み取り、データをリストに追加する
with open(csv_file, 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        data.append({'path': row['path'], 'label': row['label']})

# LabelEncoderのインスタンスを作成
label_encoder = LabelEncoder()

# ラベルを数値にエンコードする
labels = [item['label'] for item in data]
encoded_labels = label_encoder.fit_transform(labels)

# エンコードされたラベルをデータに追加する
for i, item in enumerate(data):
    item['encoded_label'] = encoded_labels[i]

# 有効な特徴量を抽出する
valid_data = []
for item in data:
    features = extract_features(item['path'])
    if features is not None:
        valid_data.append((features, item['encoded_label']))

# 特徴量とラベルをそれぞれのリストに分割する
X_raw = [item[0] for item in valid_data]
y = np.array([item[1] for item in valid_data])

# 最大の長さを取得
max_len = max(len(x) for x in X_raw)

# データの形状を揃えるためにパディングを行う
X = pad_sequences(X_raw, maxlen=max_len, padding='post', dtype='float32')

# データの分割
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 損失関数の選択
if len(label_encoder.classes_) == 2:
    loss_function = 'binary_crossentropy'
    y_train = y_train.reshape(-1, 1)
    y_test = y_test.reshape(-1, 1)
    output_units = 1
    activation = 'sigmoid'
else:
    loss_function = 'sparse_categorical_crossentropy'
    output_units = len(label_encoder.classes_)
    activation = 'softmax'

# モデルの定義
model = Sequential([
      Conv1D(32, 3, activation='relu', input_shape=(X.shape[1], X.shape[2])),  # 1層目: 畳み込み層
    MaxPooling1D(2),  # 2層目: プーリング層
    Dropout(0.2),  # 3層目: ドロップアウト層（20%のユニットを無効化）
    Conv1D(64, 3, activation='relu'),  # 4層目: 畳み込み層
    MaxPooling1D(2),  # 5層目: プーリング層
    Dropout(0.2),  # 6層目: ドロップアウト層（20%のユニットを無効化）
    Conv1D(128, 3, activation='relu'),  # 7層目: 畳み込み層
    MaxPooling1D(2),  # 8層目: プーリング層
    Dropout(0.2),  # 9層目: ドロップアウト層（20%のユニットを無効化）
    Flatten(),  # フラット化層
    Dense(64, activation='relu'),  # 全結合層
    Dropout(0.5),  # 11層目: ドロップアウト層（50%のユニットを無効化）
    Dense(32, activation='relu'),  # 全結合層
    Dense(output_units, activation=activation)  # 出力層
])

# モデルのコンパイル
model.compile(optimizer='adam',
              loss=loss_function,
              metrics=['accuracy'])

# モデルの学習
history = model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test))

# モデルの評価
loss, accuracy = model.evaluate(X_test, y_test)
print(f'Test loss: {loss:.4f}')
print(f'Test accuracy: {accuracy:.4f}')

# テストデータの読み込みと評価
def evaluate_single_file(file_path):
    features = extract_features(file_path)
    if features is not None:
        features_padded = pad_sequences([features], maxlen=max_len, padding='post', dtype='float32')
        prediction = model.predict(features_padded)
        if len(label_encoder.classes_) == 2:
            predicted_label = label_encoder.inverse_transform([int(prediction[0][0] > 0.5)])[0]
        else:
            predicted_label = label_encoder.inverse_transform(np.argmax(prediction, axis=1))[0]
        return predicted_label
    else:
        return None

metrics = ['loss', 'accuracy']  # 使用する評価関数を指定

plt.figure(figsize=(10, 5))  # グラフを表示するスペースを用意

for i in range(len(metrics)):
    metric = metrics[i]
    plt.subplot(1, 2, i+1)  # figureを1×2のスペースに分け、i+1番目のスペースを使う
    plt.title(metric)  # グラフのタイトルを表示
    
    plt_train = history.history[metric]  # historyから訓練データの評価を取り出す
    plt_test = history.history['val_' + metric]  # historyからテストデータの評価を取り出す
    
    plt.plot(plt_train, label='training')  # 訓練データの評価をグラフにプロット
    plt.plot(plt_test, label='test')  # テストデータの評価をグラフにプロット
    plt.legend()  # ラベルの表示
    
plt.show()  # グラフの表示
model.save('model1.h5')


# テスト用の音声ファイルパス
