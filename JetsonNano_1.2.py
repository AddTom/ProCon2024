#!/usr/bin/python
# -*- coding: utf-8 -*-

# Simple demo of of the PCA9685 PWM servo/LED controller library.
# This will move channel 0 from min to max position repeatedly.
# Author: Tony DiCola
# License: Public Domain

from __future__ import division
import Jetson.GPIO as GPIO
import pyaudio
import wave
import time
import subprocess
import threading
import Adafruit_PCA9685
import subprocess #ライブラリを追加
import sys
import io
import serial
import os
import numpy as np
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences  # ここを修正
import librosa
from pydub import AudioSegment

# モデルの読み込み
model = load_model('model.h5')

# ピンの設定
PIR_PIN = 17  # HC-SR501の接続ピン
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)


# デフォルトのアドレス（0x40）を使用してPCA9685を初期化する
pwm = Adafruit_PCA9685.PCA9685()
#サーボの最小及び最大パルス長を設定
servo_min = 150  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096

# 録音パラメータ
FORMAT = pyaudio.paInt16  # 16ビット整数形式
CHANNELS = 1  # モノラル
RATE = 44100  # サンプリングレート（Hz）
RECORD_SECONDS = 2  # 録音時間（秒）
WAV_FILENAME = "output.wav"  # 一時WAVファイル名
MP3_FILENAME = "output.mp3"  # 出力MP3ファイル名

# PyAudioインスタンスの作成
p = pyaudio.PyAudio()

# サーボのパルス幅設定をかんたんにするためのヘルパー関数
def set_servo_pulse(channel, pulse):
    pulse_length = 1000000    # 1,000,000 us per second
    pulse_length //= 60       # 60 Hz
    print('{0}us per period'.format(pulse_length))
    pulse_length //= 4096     # 12 bits of resolution
    print('{0}us per bit'.format(pulse_length))
    pulse *= 1000
    pulse //= pulse_length
    pwm.set_pwm(channel, 7, pulse)

#サーボのパルス幅を設定するのを簡単にするためのヘルパー関数
pwm.set_pwm_freq(60)

def record_audio():
    time.sleep(13)
    print("録音を開始します...")

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=1024)
    
    frames = []

    for _ in range(0, int(RATE / 1024 * RECORD_SECONDS)):
        data = stream.read(1024)
        frames.append(data)

    print("録音を終了します。")

    stream.stop_stream()
    stream.close()

    # 音声データの保存 (WAV形式)
    wf = wave.open(WAV_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # ffmpegを使ってWAVファイルをMP3に変換
    command = [
        'ffmpeg', '-y', '-i', WAV_FILENAME,
        '-codec:a', 'libmp3lame', '-b:a', '192k',
        MP3_FILENAME
    ]
    subprocess.run(command)

    print(f"録音データを{MP3_FILENAME}に保存しました。")

def move_servos():
    print("物体を検知！！")
    for i in range(8):
        pwm.set_pwm(i, 0, servo_min)
        time.sleep(0.8)  # 短縮
        pwm.set_pwm(i, 0, servo_max)
        time.sleep(1)  # 短縮

#mp3の読み込み
def extract_features(file_path):
    try:
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_frame_rate(44100).set_channels(1)
        raw_data = io.BytesIO()
        audio.export(raw_data, format="wav")
        raw_data.seek(0)
        y, sr = librosa.load(raw_data, sr=44100)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        return mfccs.T
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None
    
    # LabelEncoderのインスタンスを作成
label_encoder = LabelEncoder()

# ここで、すでにラベルが与えられている場合は、fitメソッドを使用してクラスを学習させる
label_encoder.fit(['Empty', 'Spray','Pet','Bottle'])  # 実際のクラス名を入力

def evaluate_single_file_with_loaded_model(file_path):
    # 音声ファイルから特徴量を抽出
    features = extract_features(file_path)
    if features is not None:
        # 特徴量のパディング
        features_padded = pad_sequences([features], maxlen=1553, padding='post', dtype='float32')

        # 入力データの形状を確認
        print(f"Input shape before prediction: {features_padded.shape}")
        
        # Conv1Dの入力に対応するように、次元を拡張
        features_padded = np.expand_dims(features_padded, axis=0)  # (1, 1553, 13)

        # 余分な次元を削除
        features_padded = np.squeeze(features_padded, axis=1)  # (1, 1553, 13)

        # モデルを使って予測を行う
        prediction = model.predict(features_padded)
        
        # ラベルの逆変換（数値をクラス名に変換）
        if len(label_encoder.classes_) == 2:
            predicted_label = label_encoder.inverse_transform([int(prediction[0][0] > 0.5)])[0]
        else:
            predicted_label = label_encoder.inverse_transform(np.argmax(prediction, axis=1))[0]

        # 確率を表示
        predicted_probabilities = prediction[0]  # 各クラスの確率
        predicted_label_index = np.argmax(predicted_probabilities)  # 最大の確率を持つクラスのインデックス
        predicted_label = label_encoder.inverse_transform([predicted_label_index])[0]

        # 確率を画面上に表示
        print(f'Predicted label: {predicted_label}, Probabilities: {predicted_probabilities}')

        
        return predicted_label
    else:
        return None
    
#実行
try:

    print("システム起動。PIRセンサーを待っています...")
    while True:
        if GPIO.input(PIR_PIN):  #赤外線センサー感知
            servo_thread = threading.Thread(target=move_servos)
            servo_thread.start()
            record_audio()  # 音声の録音をメインスレッドで行う
            servo_thread.join()  # サーボ動作が完了するのを待つ
            result=evaluate_single_file_with_loaded_model(MP3_FILENAME)

            print(result)
            ser=serial.Serial("/dev/ttyACM0",9600,timeout=None)
            if (result=="Enpty"):
                ser.write(b'1')
            if (result=="Spray"):
                ser.write(b'2')
            if (result=="Pet"):
                ser.write(b'3')
            if (result=="Bottle"):
                ser.write(b'4')

           

            #for i in range(8):   #サーボモーター動作
                #pwm.set_pwm(i, 0, servo_min)
                #time.sleep(0.8)
                #pwm.set_pwm(i, 0, servo_max)
                #time.sleep(1)

            time.sleep(2)  # 次の検知を防ぐために少し待機
            if ser.in_waiting > 0:
                ser.write(b'0')

except serial.SerialException as e:
        print("シリアル通信エラー:{e}")

except KeyboardInterrupt:
    print("プログラム終了。GPIOをクリーンアップします...")

finally:
    ser.close()
    GPIO.cleanup()
    p.terminate()

