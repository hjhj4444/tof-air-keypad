#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>


const char* ssid = "wifi";
const char* pw = "wifi_password";


const char* url = "https://vywibxwwge.execute-api.ap-northeast-2.amazonaws.com/prod/get-password";


String rx_msg = "";


void checkPassword(String input_pw) {
  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");


  String body = "{\"device_id\":\"main\"}";
  int httpCode = http.POST(body);


  Serial.print("HTTP code: ");
  Serial.println(httpCode);


  if (httpCode > 0) {
    String response = http.getString();
    Serial.println("Raw response:");
    Serial.println(response);


    DynamicJsonDocument doc(512);
    DeserializationError error = deserializeJson(doc, response);


    if (error) {
      Serial.print("JSON parse failed: ");
      Serial.println(error.c_str());
      Serial2.println("FAIL");
      Serial.println("sent to STM32: FAIL");
    } else {
      String server_pw = doc["password"].as<String>();


      Serial.print("input pw: ");
      Serial.println(input_pw);


      Serial.print("server pw: ");
      Serial.println(server_pw);


      if (input_pw == server_pw) {
        Serial.println("OK");
        Serial2.println("OK");
        Serial.println("sent to STM32: OK");
      } else {
        Serial.println("FAIL");
        Serial2.println("FAIL");
        Serial.println("sent to STM32: FAIL");
      }
    }


  } else {
    Serial.println("Request failed");
    Serial2.println("FAIL");
    Serial.println("sent to STM32: FAIL");
  }


  http.end();
}


void setup() {
  Serial.begin(115200);
  Serial2.begin(115200, SERIAL_8N1, 16, 17);   // <- 여기 핀번호 실제 배선대로 수정
  delay(1000);


  Serial.println("WiFi connecting...");
  WiFi.begin(ssid, pw);


  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }


  Serial.println();
  Serial.println("WiFi connected");
  Serial.println("Waiting STM32...");
}


void loop() {
  while (Serial2.available()) {
    char c = Serial2.read();


    if (c == '\n') {
      rx_msg.trim();


      Serial.print("rx msg: ");
      Serial.println(rx_msg);


      if (rx_msg.startsWith("PW:")) {
        String input_pw = rx_msg.substring(3);
        Serial.print("parsed input pw: ");
        Serial.println(input_pw);


        checkPassword(input_pw);
      } else {
        Serial.println("FORMAT ERROR");
      }


      rx_msg = "";
    }
    else if (c != '\r') {
      rx_msg += c;
    }
