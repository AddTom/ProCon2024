#include <Wire.h>  // I2C通信ライブラリのインクルード
#include <Adafruit_PWMServoDriver.h>  // PWM制御ライブラリのインクルード

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);  // PCA9685のインスタンスを作成（I2Cアドレス0x40）
#define SERVOMIN 500  // サーボの最小パルス幅（μs）
#define SERVOMAX 2400  // サーボの最大パルス幅（μs）
#define INITIAL_ANGLE 100  // サーボの初期角度
#define CHANGE_ANGLE 48  // 角度変更分

int angle = INITIAL_ANGLE - CHANGE_ANGLE;  // 実際の角度設定
int rightUp = 0;  // 右上モーターのピン番号
int rightDown = 3;  // 右下モーターのピン番号
int leftUp = 6;  // 左上モーターのピン番号
int leftDown = 9;  // 左下モーターのピン番号
int floorMotor = 12;  // フロアモーターのピン番号

void setup() {
  pwm.begin();  // PWMの初期化
  pwm.setPWMFreq(50);  // PWM周波数を50Hzに設定（サーボの制御に最適な周波数）
  Serial.begin(9600);  // シリアル通信を9600bpsで開始

  motor(floorMotor, 180);  // フロアモーターを停止（90度で停止）
  delay(500);  // 500ms待機
  
  // 各モーターを初期角度に設定
  motor(rightUp, INITIAL_ANGLE);
  delay(500);
  motor(rightDown, INITIAL_ANGLE);
  delay(500);
  motor(leftUp, INITIAL_ANGLE);
  delay(500);
  motor(leftDown, INITIAL_ANGLE);
  delay(500);
}

void loop() {
  if (Serial.available() > 0) {  // シリアル入力をチェック
    char key = Serial.read();  // 入力されたキーを読み取る
    if (key == '1') {
      // 右上モーターを動かす操作
      motor(rightUp, angle);
      delay(500);
      motor(floorMotor, 85);  // フロアモーターを動かす
      delay(2000);
      motor(rightUp, INITIAL_ANGLE);  // 右上モーターを元に戻す
      delay(500);
      motor(floorMotor, 180);  // フロアモーターを停止
    } else if (key == '2') {
      // 右下モーターを動かす操作
      motor(rightDown, angle);
      delay(500);
      motor(floorMotor, 85);  // フロアモーターを動かす
      delay(2000);
      motor(rightDown, INITIAL_ANGLE);  // 右上モーターを元に戻す
      delay(500);
      motor(floorMotor, 180);  // フロアモーターを停止
    } else if (key == '3') {
      // 左上モーターを動かす操作
      motor(leftUp, angle);
      delay(500);
      motor(floorMotor, 85);  // フロアモーターを動かす
      delay(2000);
      motor(leftUp, INITIAL_ANGLE);  // 右上モーターを元に戻す
      delay(500);
      motor(floorMotor, 180);  // フロアモーターを停止
    } else if (key == '4') {
      // 左下モーターを動かす操作
      motor(leftDown, angle);
      delay(500);
      motor(floorMotor, 85);  // フロアモーターを動かす
      delay(2000);
      motor(leftDown, INITIAL_ANGLE);  // 右上モーターを元に戻す
      delay(500);
      motor(floorMotor, 180);  // フロアモーターを停止
    }
    Serial.println(key);  // 入力されたキーをシリアルモニタに出力
  }
}

// モーター制御関数
void motor(int pin, int angle) {
  angle = map(angle, 0, 180, SERVOMIN, SERVOMAX);  // 角度をパルス幅にマッピング
  pwm.writeMicroseconds(pin, angle);  // 指定したピンにパルス幅を送信
}
