/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : main.c
 * @brief          : ToF keypad + OLED + password(1370) + buzzer + servo
 ******************************************************************************
 */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "vl53l5cx_api.h"
#include <string.h>
#include <stdio.h>
#include <stdint.h>
/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
/* USER CODE END Includes */
/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
/* USER CODE END PTD */
/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */
/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */
/* USER CODE END PM */
/* Private variables ---------------------------------------------------------*/
COM_InitTypeDef BspCOMInit;
I2C_HandleTypeDef hi2c1;
UART_HandleTypeDef hlpuart1;
TIM_HandleTypeDef htim1;
/* USER CODE BEGIN PV */
static VL53L5CX_Configuration Dev;
static VL53L5CX_ResultsData Results;
static uint8_t is_alive = 0;
static uint8_t data_ready = 0;
static uint8_t status = 0;
#define DETECT_THRESHOLD_MM   450
#define STABLE_COUNT_REQ      2
#define CONFIRM_HOLD_MS       900
#define NO_DATA_RESET_REQ     5
#define OLED_I2C_ADDR         (0x3C << 1)
#define OLED_WIDTH            128
#define OLED_HEIGHT           32
#define OLED_PAGES            (OLED_HEIGHT / 8)
/* 부저 / 서보 */
#define BUZZER_GPIO_Port      GPIOA
#define BUZZER_Pin            GPIO_PIN_5
#define SERVO_TIMER           htim1
#define SERVO_CHANNEL         TIM_CHANNEL_1
#define SERVO_LOCK_PULSE      1000   /* 1.0ms */
#define SERVO_OPEN_PULSE      2000   /* 2.0ms */
static const int8_t password[4] = {1, 3, 7, 0};
static uint8_t oled_buffer[OLED_WIDTH * OLED_PAGES];
static int8_t input_buffer[4] = {-1, -1, -1, -1};
static uint8_t input_count = 0;
static uint8_t esp_rx;
static char esp_msg[16];
static uint8_t esp_idx = 0;
static uint8_t auth_wait = 0;
/* USER CODE END PV */
/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
void PeriphCommonClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_I2C1_Init(void);
static void MX_TIM1_Init(void);
static void MX_LPUART1_UART_Init(void);
/* USER CODE BEGIN PFP */
static void UI_SendHighlight(int8_t key);
static void UI_SendMessage(const char *msg);
static void Input_ClearAll(void);
static void OLED_ShowMainScreen(int8_t current_key);
static void OLED_ShowMessage(const char *msg, uint32_t hold_ms);
static void Buzzer_Beep(uint16_t on_ms);
static void Buzzer_Beep_Count(uint8_t count, uint16_t on_ms, uint16_t off_ms);
static void Servo_OpenSequence(void);
/* USER CODE END PFP */
/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
static void ESP_SendPW(void)
{
 char msg[16];
 snprintf(msg, sizeof(msg), "PW:%d%d%d%d\r\n",
          input_buffer[0],
          input_buffer[1],
          input_buffer[2],
          input_buffer[3]);
 HAL_UART_Transmit(&hlpuart1, (uint8_t*)msg, strlen(msg), 100);
}
static void ESP_HandleMessage(const char *msg)
{
	printf("ESP_REPLY:%s\r\n", msg);
	UI_SendMessage(msg);
 if (strcmp(msg, "OK") == 0)
 {
   OLED_ShowMessage("OK", 700);
   Buzzer_Beep(150);
   Servo_OpenSequence();
   Input_ClearAll();
   UI_SendMessage("OK");
   UI_SendHighlight(-1);
   OLED_ShowMainScreen(-1);
   auth_wait = 0;
 }
 else if (strcmp(msg, "FAIL") == 0)
 {
   OLED_ShowMessage("WRONG", 800);
   Buzzer_Beep_Count(2, 120, 120);
   Input_ClearAll();
   UI_SendMessage("WRONG");
   UI_SendHighlight(-1);
   OLED_ShowMainScreen(-1);
   auth_wait = 0;
 }
}
static void ESP_PollRx(void)
{
 while (HAL_UART_Receive(&hlpuart1, &esp_rx, 1, 10) == HAL_OK)
 {
   printf("RXCHAR:%c\r\n", esp_rx);
   if (esp_rx == 'O')
   {
     ESP_HandleMessage("OK");
     esp_idx = 0;
   }
   else if (esp_rx == 'F')
   {
     ESP_HandleMessage("FAIL");
     esp_idx = 0;
   }
   else if (esp_rx == '\n')
   {
     esp_msg[esp_idx] = '\0';
     if (esp_idx > 0)
     {
       if (esp_msg[esp_idx - 1] == '\r')
         esp_msg[esp_idx - 1] = '\0';
       printf("ESP_REPLY:%s\r\n", esp_msg);
       ESP_HandleMessage(esp_msg);
     }
     esp_idx = 0;
   }
   else
   {
     if (esp_idx < sizeof(esp_msg) - 1)
     {
       esp_msg[esp_idx++] = esp_rx;
     }
   }
 }
}
static const char* UI_KeyLabel(int8_t key)
{
 switch (key)
 {
   case 0:  return "0";
   case 1:  return "1";
   case 2:  return "2";
   case 3:  return "3";
   case 4:  return "4";
   case 5:  return "5";
   case 6:  return "6";
   case 7:  return "7";
   case 8:  return "8";
   case 9:  return "9";
   case 10: return "CANCEL";
   case 11: return "OK";
   default: return "NONE";
 }
}
static void UI_SendHighlight(int8_t key)
{
 printf("HIGHLIGHT:%s\r\n", UI_KeyLabel(key));
}
static void UI_SendConfirm(int8_t key)
{
 printf("CONFIRM:%s\r\n", UI_KeyLabel(key));
}
static void UI_SendMessage(const char *msg)
{
 printf("MSG:%s\r\n", msg);
}
/* ===== 5x7 ASCII font ===== */
static const uint8_t font5x7[][5] = {
 {0x00,0x00,0x00,0x00,0x00}, {0x00,0x00,0x5F,0x00,0x00},
 {0x00,0x07,0x00,0x07,0x00}, {0x14,0x7F,0x14,0x7F,0x14},
 {0x24,0x2A,0x7F,0x2A,0x12}, {0x23,0x13,0x08,0x64,0x62},
 {0x36,0x49,0x55,0x22,0x50}, {0x00,0x05,0x03,0x00,0x00},
 {0x00,0x1C,0x22,0x41,0x00}, {0x00,0x41,0x22,0x1C,0x00},
 {0x14,0x08,0x3E,0x08,0x14}, {0x08,0x08,0x3E,0x08,0x08},
 {0x00,0x50,0x30,0x00,0x00}, {0x08,0x08,0x08,0x08,0x08},
 {0x00,0x60,0x60,0x00,0x00}, {0x20,0x10,0x08,0x04,0x02},
 {0x3E,0x51,0x49,0x45,0x3E}, {0x00,0x42,0x7F,0x40,0x00},
 {0x42,0x61,0x51,0x49,0x46}, {0x21,0x41,0x45,0x4B,0x31},
 {0x18,0x14,0x12,0x7F,0x10}, {0x27,0x45,0x45,0x45,0x39},
 {0x3C,0x4A,0x49,0x49,0x30}, {0x01,0x71,0x09,0x05,0x03},
 {0x36,0x49,0x49,0x49,0x36}, {0x06,0x49,0x49,0x29,0x1E},
 {0x00,0x36,0x36,0x00,0x00}, {0x00,0x56,0x36,0x00,0x00},
 {0x08,0x14,0x22,0x41,0x00}, {0x14,0x14,0x14,0x14,0x14},
 {0x00,0x41,0x22,0x14,0x08}, {0x02,0x01,0x51,0x09,0x06},
 {0x32,0x49,0x79,0x41,0x3E}, {0x7E,0x11,0x11,0x11,0x7E},
 {0x7F,0x49,0x49,0x49,0x36}, {0x3E,0x41,0x41,0x41,0x22},
 {0x7F,0x41,0x41,0x22,0x1C}, {0x7F,0x49,0x49,0x49,0x41},
 {0x7F,0x09,0x09,0x09,0x01}, {0x3E,0x41,0x49,0x49,0x7A},
 {0x7F,0x08,0x08,0x08,0x7F}, {0x00,0x41,0x7F,0x41,0x00},
 {0x20,0x40,0x41,0x3F,0x01}, {0x7F,0x08,0x14,0x22,0x41},
 {0x7F,0x40,0x40,0x40,0x40}, {0x7F,0x02,0x0C,0x02,0x7F},
 {0x7F,0x04,0x08,0x10,0x7F}, {0x3E,0x41,0x41,0x41,0x3E},
 {0x7F,0x09,0x09,0x09,0x06}, {0x3E,0x41,0x51,0x21,0x5E},
 {0x7F,0x09,0x19,0x29,0x46}, {0x46,0x49,0x49,0x49,0x31},
 {0x01,0x01,0x7F,0x01,0x01}, {0x3F,0x40,0x40,0x40,0x3F},
 {0x1F,0x20,0x40,0x20,0x1F}, {0x3F,0x40,0x38,0x40,0x3F},
 {0x63,0x14,0x08,0x14,0x63}, {0x07,0x08,0x70,0x08,0x07},
 {0x61,0x51,0x49,0x45,0x43}, {0x00,0x7F,0x41,0x41,0x00},
 {0x02,0x04,0x08,0x10,0x20}, {0x00,0x41,0x41,0x7F,0x00},
 {0x04,0x02,0x01,0x02,0x04}, {0x40,0x40,0x40,0x40,0x40},
 {0x00,0x01,0x02,0x04,0x00}, {0x20,0x54,0x54,0x54,0x78},
 {0x7F,0x48,0x44,0x44,0x38}, {0x38,0x44,0x44,0x44,0x20},
 {0x38,0x44,0x44,0x48,0x7F}, {0x38,0x54,0x54,0x54,0x18},
 {0x08,0x7E,0x09,0x01,0x02}, {0x08,0x14,0x54,0x54,0x3C},
 {0x7F,0x08,0x04,0x04,0x78}, {0x00,0x44,0x7D,0x40,0x00},
 {0x20,0x40,0x44,0x3D,0x00}, {0x7F,0x10,0x28,0x44,0x00},
 {0x00,0x41,0x7F,0x40,0x00}, {0x7C,0x04,0x18,0x04,0x78},
 {0x7C,0x08,0x04,0x04,0x78}, {0x38,0x44,0x44,0x44,0x38},
 {0x7C,0x14,0x14,0x14,0x08}, {0x08,0x14,0x14,0x18,0x7C},
 {0x7C,0x08,0x04,0x04,0x08}, {0x48,0x54,0x54,0x54,0x20},
 {0x04,0x3F,0x44,0x40,0x20}, {0x3C,0x40,0x40,0x20,0x7C},
 {0x1C,0x20,0x40,0x20,0x1C}, {0x3C,0x40,0x30,0x40,0x3C},
 {0x44,0x28,0x10,0x28,0x44}, {0x0C,0x50,0x50,0x50,0x3C},
 {0x44,0x64,0x54,0x4C,0x44}, {0x00,0x08,0x36,0x41,0x00},
 {0x00,0x00,0x7F,0x00,0x00}, {0x00,0x41,0x36,0x08,0x00},
 {0x08,0x04,0x08,0x10,0x08}
};
static void OLED_WriteCommand(uint8_t cmd)
{
 uint8_t data[2];
 data[0] = 0x00;
 data[1] = cmd;
 HAL_I2C_Master_Transmit(&hi2c1, OLED_I2C_ADDR, data, 2, 100);
}
static void OLED_WriteData(uint8_t *data, uint16_t size)
{
 uint8_t buf[129];
 if (size > 128) return;
 buf[0] = 0x40;
 memcpy(&buf[1], data, size);
 HAL_I2C_Master_Transmit(&hi2c1, OLED_I2C_ADDR, buf, size + 1, 200);
}
static void OLED_Init(void)
{
 HAL_Delay(100);
 OLED_WriteCommand(0xAE);
 OLED_WriteCommand(0xD5); OLED_WriteCommand(0x80);
 OLED_WriteCommand(0xA8); OLED_WriteCommand(0x1F);
 OLED_WriteCommand(0xD3); OLED_WriteCommand(0x00);
 OLED_WriteCommand(0x40);
 OLED_WriteCommand(0x8D); OLED_WriteCommand(0x14);
 OLED_WriteCommand(0x20); OLED_WriteCommand(0x00);
 OLED_WriteCommand(0xA1);
 OLED_WriteCommand(0xC8);
 OLED_WriteCommand(0xDA); OLED_WriteCommand(0x02);
 OLED_WriteCommand(0x81); OLED_WriteCommand(0x8F);
 OLED_WriteCommand(0xD9); OLED_WriteCommand(0xF1);
 OLED_WriteCommand(0xDB); OLED_WriteCommand(0x40);
 OLED_WriteCommand(0xA4);
 OLED_WriteCommand(0xA6);
 OLED_WriteCommand(0xAF);
}
static void OLED_UpdateScreen(void)
{
 for (uint8_t page = 0; page < OLED_PAGES; page++)
 {
   OLED_WriteCommand(0xB0 + page);
   OLED_WriteCommand(0x00);
   OLED_WriteCommand(0x10);
   OLED_WriteData(&oled_buffer[OLED_WIDTH * page], OLED_WIDTH);
 }
}
static void OLED_Clear(void)
{
 memset(oled_buffer, 0x00, sizeof(oled_buffer));
}
static void OLED_DrawPixel(uint8_t x, uint8_t y, uint8_t color)
{
 if (x >= OLED_WIDTH || y >= OLED_HEIGHT) return;
 if (color)
   oled_buffer[x + (y / 8) * OLED_WIDTH] |= (1 << (y % 8));
 else
   oled_buffer[x + (y / 8) * OLED_WIDTH] &= ~(1 << (y % 8));
}
static void OLED_DrawChar(uint8_t x, uint8_t y, char ch)
{
 if (ch < 32 || ch > 126) ch = '?';
 for (uint8_t i = 0; i < 5; i++)
 {
   uint8_t line = font5x7[ch - 32][i];
   for (uint8_t j = 0; j < 7; j++)
   {
     OLED_DrawPixel(x + i, y + j, (line & (1 << j)) ? 1 : 0);
   }
 }
 for (uint8_t j = 0; j < 7; j++)
 {
   OLED_DrawPixel(x + 5, y + j, 0);
 }
}
static void OLED_DrawString(uint8_t x, uint8_t y, const char *str)
{
 while (*str)
 {
   OLED_DrawChar(x, y, *str++);
   x += 6;
   if (x > OLED_WIDTH - 6) break;
 }
}
static void Input_ClearAll(void)
{
 for (uint8_t i = 0; i < 4; i++)
   input_buffer[i] = -1;
 input_count = 0;
}
static char Key_To_Char(int8_t key)
{
 if (key >= 0 && key <= 9) return (char)('0' + key);
 return '_';
}
static void OLED_ShowMainScreen(int8_t current_key)
{
 char line1[24];
 char line2[32];
 OLED_Clear();
 if (current_key >= 1 && current_key <= 9)
   snprintf(line1, sizeof(line1), "CURRENT:%d", current_key);
 else if (current_key == 10)
   snprintf(line1, sizeof(line1), "CURRENT:CANCEL");
 else if (current_key == 0)
   snprintf(line1, sizeof(line1), "CURRENT:0");
 else if (current_key == 11)
   snprintf(line1, sizeof(line1), "CURRENT:OK");
 else
   snprintf(line1, sizeof(line1), "CURRENT:NONE");
 snprintf(line2, sizeof(line2), "INPUT: %c %c %c %c",
          Key_To_Char(input_buffer[0]),
          Key_To_Char(input_buffer[1]),
          Key_To_Char(input_buffer[2]),
          Key_To_Char(input_buffer[3]));
 OLED_DrawString(0, 0, line1);
 OLED_DrawString(0, 16, line2);
 OLED_UpdateScreen();
}
static void OLED_ShowMessage(const char *msg, uint32_t hold_ms)
{
 OLED_Clear();
 OLED_DrawString(0, 0, msg);
 OLED_UpdateScreen();
 HAL_Delay(hold_ms);
}
static uint8_t I2C_Ping7(uint8_t addr7)
{
 return (HAL_I2C_IsDeviceReady(&hi2c1, (uint16_t)(addr7 << 1), 2, 100) == HAL_OK);
}
static void Fatal_Blink_Code(uint8_t code)
{
 BSP_LED_Off(LED_RED);
 BSP_LED_Off(LED_GREEN);
 BSP_LED_Off(LED_BLUE);
 while (1)
 {
   switch (code)
   {
     case 1: BSP_LED_Toggle(LED_RED);   HAL_Delay(120); break;
     case 2: BSP_LED_Toggle(LED_RED);   HAL_Delay(500); break;
     case 3:
       BSP_LED_On(LED_RED); BSP_LED_Off(LED_BLUE); HAL_Delay(150);
       BSP_LED_Off(LED_RED); BSP_LED_On(LED_BLUE); HAL_Delay(150);
       break;
     case 4: BSP_LED_Toggle(LED_BLUE);  HAL_Delay(120); break;
     case 5: BSP_LED_Toggle(LED_BLUE);  HAL_Delay(500); break;
     case 6: BSP_LED_Toggle(LED_GREEN); HAL_Delay(120); break;
     case 7: BSP_LED_Toggle(LED_GREEN); HAL_Delay(500); break;
     default: BSP_LED_Toggle(LED_RED);  HAL_Delay(100); break;
   }
 }
}
/* 부저: 안 울리면 이 둘 반대로 바꿔서 테스트 */
static void Buzzer_On(void)
{
 HAL_GPIO_WritePin(BUZZER_GPIO_Port, BUZZER_Pin, GPIO_PIN_SET);
}
static void Buzzer_Off(void)
{
 HAL_GPIO_WritePin(BUZZER_GPIO_Port, BUZZER_Pin, GPIO_PIN_RESET);
}
static void Buzzer_Beep(uint16_t on_ms)
{
 Buzzer_On();
 HAL_Delay(on_ms);
 Buzzer_Off();
}
static void Buzzer_Beep_Count(uint8_t count, uint16_t on_ms, uint16_t off_ms)
{
 for (uint8_t i = 0; i < count; i++)
 {
   Buzzer_On();
   HAL_Delay(on_ms);
   Buzzer_Off();
   if (i < (count - 1))
   {
     HAL_Delay(off_ms);
   }
 }
}
static void Servo_SetPulse(uint16_t pulse_us)
{
 __HAL_TIM_SET_COMPARE(&SERVO_TIMER, SERVO_CHANNEL, pulse_us);
}
static void Servo_Lock(void)
{
 Servo_SetPulse(SERVO_LOCK_PULSE);
}
static void Servo_Open(void)
{
 Servo_SetPulse(SERVO_OPEN_PULSE);
}
static void Servo_OpenSequence(void)
{
 Servo_Open();
 HAL_Delay(1000);
 Servo_Lock();
}
static uint8_t Password_Match(void)
{
 if (input_count != 4) return 0;
 for (uint8_t i = 0; i < 4; i++)
 {
   if (input_buffer[i] != password[i])
     return 0;
 }
 return 1;
}
static uint8_t Find_Closest_Zone(VL53L5CX_ResultsData *res,
                                uint8_t *best_row,
                                uint8_t *best_col,
                                int16_t *best_dist)
{
 int16_t min_dist = 32767;
 uint8_t found = 0;
 for (uint8_t row = 0; row < 8; row++)
 {
   for (uint8_t col = 0; col < 8; col++)
   {
     uint8_t idx = row * 8 + col;
     uint8_t ts = res->target_status[idx];
     int16_t d = res->distance_mm[idx];
     if ((ts == 5) || (ts == 9))
     {
       if ((d > 0) && (d < DETECT_THRESHOLD_MM) && (d < min_dist))
       {
         min_dist = d;
         *best_row = row;
         *best_col = col;
         found = 1;
       }
     }
   }
 }
 if (found)
 {
   *best_dist = min_dist;
   return 1;
 }
 return 0;
}
static uint8_t Map_Row_8x8_To_4(uint8_t row)
{
 if (row <= 1) return 0;
 if (row <= 3) return 1;
 if (row <= 5) return 2;
 return 3;
}
static uint8_t Map_Col_8x8_To_3(uint8_t col)
{
 if (col <= 1) return 2;
 if (col <= 4) return 1;
 return 0;
}
static int8_t Map_Keypad_Value(uint8_t row4, uint8_t col3)
{
 static const int8_t keypad[4][3] =
 {
   { 1, 2, 3 },
   { 4, 5, 6 },
   { 7, 8, 9 },
   {10, 0, 11}
 };
 return keypad[row4][col3];
}
static void Show_Selected_Key_LED(int8_t key)
{
 BSP_LED_Off(LED_RED);
 BSP_LED_Off(LED_GREEN);
 BSP_LED_Off(LED_BLUE);
 if (key >= 1 && key <= 9)
 {
   BSP_LED_On(LED_RED);
 }
 else if (key == 10)
 {
   BSP_LED_On(LED_BLUE);
 }
 else if (key == 0)
 {
   BSP_LED_On(LED_GREEN);
 }
 else if (key == 11)
 {
   BSP_LED_On(LED_RED);
   BSP_LED_On(LED_GREEN);
 }
}
static void Handle_Confirmed_Key(int8_t key)
{
 if (key >= 0 && key <= 9)
 {
   if (input_count < 4)
   {
     input_buffer[input_count] = key;
     input_count++;
     Buzzer_Beep(50);
     UI_SendConfirm(key);
     UI_SendMessage("INPUT");
   }
 }
 else if (key == 10)  /* CANCEL */
 {
   Buzzer_Beep_Count(2, 40, 40);
   Input_ClearAll();
   OLED_ShowMessage("CLEARED", 500);
   UI_SendConfirm(key);
   UI_SendMessage("CLEARED");
 }
 else if (key == 11)  /* OK */
 {
   UI_SendConfirm(key);
   if (input_count == 4)
   {
     UI_SendMessage("CHECKING...");
     OLED_ShowMessage("CHECKING...", 300);
     auth_wait = 1;
     ESP_SendPW();
   }
   else
   {
     Buzzer_Beep_Count(2, 40, 40);
     OLED_ShowMessage("NEED 4 DIGITS", 700);
     UI_SendMessage("NEED 4 DIGITS");
   }
 }
}
/* USER CODE END 0 */
/**
 * @brief  The application entry point.
 * @retval int
 */
int main(void)
{
 /* USER CODE BEGIN 1 */
 /* USER CODE END 1 */
 /* MCU Configuration--------------------------------------------------------*/
 /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
 HAL_Init();
 /* USER CODE BEGIN Init */
 /* USER CODE END Init */
 /* Configure the system clock */
 SystemClock_Config();
 /* Configure the peripherals common clocks */
 PeriphCommonClock_Config();
 /* USER CODE BEGIN SysInit */
 /* USER CODE END SysInit */
 /* Initialize all configured peripherals */
 MX_GPIO_Init();
 MX_I2C1_Init();
 MX_TIM1_Init();
 MX_LPUART1_UART_Init();
 /* USER CODE BEGIN 2 */
 BSP_LED_Init(LED_BLUE);
 BSP_LED_Init(LED_GREEN);
 BSP_LED_Init(LED_RED);
 Input_ClearAll();
 OLED_Init();
 OLED_ShowMainScreen(-1);
 if (HAL_TIM_PWM_Start(&SERVO_TIMER, SERVO_CHANNEL) != HAL_OK)
 {
   Error_Handler();
 }
 Servo_Lock();
 Buzzer_Off();
 BSP_LED_On(LED_BLUE);
 HAL_Delay(150);
 BSP_LED_Off(LED_BLUE);
 if (!I2C_Ping7(0x29))
 {
   Fatal_Blink_Code(1);
 }
 BSP_LED_On(LED_GREEN);
 HAL_Delay(150);
 BSP_LED_Off(LED_GREEN);
 Dev.platform.address = 0x29;
 status = vl53l5cx_is_alive(&Dev, &is_alive);
 if ((status != VL53L5CX_STATUS_OK) || (is_alive == 0))
 {
   Fatal_Blink_Code(2);
 }
 BSP_LED_On(LED_RED);
 HAL_Delay(150);
 BSP_LED_Off(LED_RED);
 status = vl53l5cx_init(&Dev);
 if (status != VL53L5CX_STATUS_OK)
 {
   Fatal_Blink_Code(3);
 }
 status = vl53l5cx_set_resolution(&Dev, VL53L5CX_RESOLUTION_8X8);
 if (status != VL53L5CX_STATUS_OK)
 {
   Fatal_Blink_Code(4);
 }
 status = vl53l5cx_set_ranging_frequency_hz(&Dev, 10);
 if (status != VL53L5CX_STATUS_OK)
 {
   Fatal_Blink_Code(5);
 }
 status = vl53l5cx_set_target_order(&Dev, VL53L5CX_TARGET_ORDER_CLOSEST);
 if (status != VL53L5CX_STATUS_OK)
 {
   Fatal_Blink_Code(6);
 }
 status = vl53l5cx_start_ranging(&Dev);
 if (status != VL53L5CX_STATUS_OK)
 {
   Fatal_Blink_Code(7);
 }
 /* USER CODE END 2 */
 /* Initialize leds */
 BSP_LED_Init(LED_BLUE);
 BSP_LED_Init(LED_GREEN);
 BSP_LED_Init(LED_RED);
 /* Initialize USER push-button, will be used to trigger an interrupt each time it's pressed.*/
 BSP_PB_Init(BUTTON_SW1, BUTTON_MODE_EXTI);
 BSP_PB_Init(BUTTON_SW2, BUTTON_MODE_EXTI);
 BSP_PB_Init(BUTTON_SW3, BUTTON_MODE_EXTI);
 /* Initialize COM1 port (115200, 8 bits (7-bit data + 1 stop bit), no parity */
 BspCOMInit.BaudRate   = 115200;
 BspCOMInit.WordLength = COM_WORDLENGTH_8B;
 BspCOMInit.StopBits   = COM_STOPBITS_1;
 BspCOMInit.Parity     = COM_PARITY_NONE;
 BspCOMInit.HwFlowCtl  = COM_HWCONTROL_NONE;
 if (BSP_COM_Init(COM1, &BspCOMInit) != BSP_ERROR_NONE)
 {
   Error_Handler();
 }
 /* Infinite loop */
 /* USER CODE BEGIN WHILE */
 int8_t raw_key = -1;
 int8_t prev_raw_key = -1;
 int8_t stable_key = -1;
 int8_t last_oled_key = -99;
 int8_t last_confirmed_key = -1;
 uint8_t same_count = 0;
 uint8_t no_data_count = 0;
 int8_t hold_key = -1;
 uint32_t hold_start_ms = 0;
 uint8_t wait_release = 0;
 while (1)
 {
	  ESP_PollRx();
   uint8_t best_row = 0, best_col = 0;
   uint8_t row4 = 0, col3 = 0;
   int16_t best_dist = 0;
   status = vl53l5cx_check_data_ready(&Dev, &data_ready);
   if (status != VL53L5CX_STATUS_OK)
   {
     data_ready = 0;
     if (no_data_count < 255) no_data_count++;
     HAL_Delay(30);
     continue;
   }
   if (data_ready)
   {
   	status = vl53l5cx_get_ranging_data(&Dev, &Results);
   	if (status != VL53L5CX_STATUS_OK)
   	{
   	  if (no_data_count < 255) no_data_count++;
   	  HAL_Delay(30);
   	  continue;
   	}
     if (Find_Closest_Zone(&Results, &best_row, &best_col, &best_dist))
     {
   	no_data_count = 0;
       row4 = Map_Row_8x8_To_4(best_row);
       col3 = Map_Col_8x8_To_3(best_col);
       raw_key = Map_Keypad_Value(row4, col3);
       if (raw_key == prev_raw_key)
       {
         if (same_count < 255) same_count++;
       }
       else
       {
         prev_raw_key = raw_key;
         same_count = 1;
       }
       if (same_count >= STABLE_COUNT_REQ)
       {
         stable_key = raw_key;
         Show_Selected_Key_LED(stable_key);
         if (stable_key != last_oled_key)
         {
           OLED_ShowMainScreen(stable_key);
           last_oled_key = stable_key;
           UI_SendHighlight(stable_key);
         }
         if (wait_release && (stable_key != last_confirmed_key))
         {
           wait_release = 0;
           hold_key = stable_key;
           hold_start_ms = HAL_GetTick();
         }
         if (!wait_release)
         {
           if (stable_key != hold_key)
           {
             hold_key = stable_key;
             hold_start_ms = HAL_GetTick();
           }
           else
           {
             if ((HAL_GetTick() - hold_start_ms) >= CONFIRM_HOLD_MS)
             {
               Handle_Confirmed_Key(stable_key);
               OLED_ShowMainScreen(stable_key);
               last_confirmed_key = stable_key;
               wait_release = 1;
             }
           }
         }
       }
     }
     else
     {
       if (no_data_count < 255) no_data_count++;
       if (no_data_count >= NO_DATA_RESET_REQ)
       {
         raw_key = -1;
         prev_raw_key = -1;
         stable_key = -1;
         same_count = 0;
         hold_key = -1;
         hold_start_ms = 0;
         BSP_LED_Off(LED_RED);
         BSP_LED_Off(LED_GREEN);
         BSP_LED_Off(LED_BLUE);
         wait_release = 0;
         last_confirmed_key = -1;
         if (last_oled_key != -1)
         {
           OLED_ShowMainScreen(-1);
           last_oled_key = -1;
           UI_SendHighlight(-1);
         }
       }
     }
   }
   if (!data_ready)
   {
     if (no_data_count < 255) no_data_count++;
     if (no_data_count >= NO_DATA_RESET_REQ)
     {
       raw_key = -1;
       prev_raw_key = -1;
       stable_key = -1;
       same_count = 0;
       hold_key = -1;
       hold_start_ms = 0;
       BSP_LED_Off(LED_RED);
       BSP_LED_Off(LED_GREEN);
       BSP_LED_Off(LED_BLUE);
       wait_release = 0;
       last_confirmed_key = -1;
       if (last_oled_key != -1)
       {
         OLED_ShowMainScreen(-1);
         last_oled_key = -1;
         UI_SendHighlight(-1);
       }
     }
   }
   HAL_Delay(30);
   /* USER CODE END WHILE */
   /* USER CODE BEGIN 3 */
 }
 /* USER CODE END 3 */
}
/**
 * @brief System Clock Configuration
 * @retval None
 */
void SystemClock_Config(void)
{
 RCC_OscInitTypeDef RCC_OscInitStruct = {0};
 RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
 /** Configure the main internal regulator output voltage
 */
 __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);
 /** Initializes the RCC Oscillators according to the specified parameters
 * in the RCC_OscInitTypeDef structure.
 */
 RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI|RCC_OSCILLATORTYPE_MSI;
 RCC_OscInitStruct.HSIState = RCC_HSI_ON;
 RCC_OscInitStruct.MSIState = RCC_MSI_ON;
 RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
 RCC_OscInitStruct.MSICalibrationValue = RCC_MSICALIBRATION_DEFAULT;
 RCC_OscInitStruct.MSIClockRange = RCC_MSIRANGE_10;
 RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
 if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
 {
   Error_Handler();
 }
 /** Configure the SYSCLKSource, HCLK, PCLK1 and PCLK2 clocks dividers
 */
 RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK4|RCC_CLOCKTYPE_HCLK2
                             |RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                             |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
 RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_MSI;
 RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
 RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
 RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;
 RCC_ClkInitStruct.AHBCLK2Divider = RCC_SYSCLK_DIV1;
 RCC_ClkInitStruct.AHBCLK4Divider = RCC_SYSCLK_DIV1;
 if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_1) != HAL_OK)
 {
   Error_Handler();
 }
}
/**
 * @brief Peripherals Common Clock Configuration
 * @retval None
 */
void PeriphCommonClock_Config(void)
{
 RCC_PeriphCLKInitTypeDef PeriphClkInitStruct = {0};
 /** Initializes the peripherals clock
 */
 PeriphClkInitStruct.PeriphClockSelection = RCC_PERIPHCLK_SMPS;
 PeriphClkInitStruct.SmpsClockSelection = RCC_SMPSCLKSOURCE_HSI;
 PeriphClkInitStruct.SmpsDivSelection = RCC_SMPSCLKDIV_RANGE0;
 if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInitStruct) != HAL_OK)
 {
   Error_Handler();
 }
 /* USER CODE BEGIN Smps */
 /* USER CODE END Smps */
}
/**
 * @brief I2C1 Initialization Function
 * @param None
 * @retval None
 */
static void MX_I2C1_Init(void)
{
 /* USER CODE BEGIN I2C1_Init 0 */
 /* USER CODE END I2C1_Init 0 */
 /* USER CODE BEGIN I2C1_Init 1 */
 /* USER CODE END I2C1_Init 1 */
 hi2c1.Instance = I2C1;
 hi2c1.Init.Timing = 0x00B07CB4;
 hi2c1.Init.OwnAddress1 = 0;
 hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
 hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
 hi2c1.Init.OwnAddress2 = 0;
 hi2c1.Init.OwnAddress2Masks = I2C_OA2_NOMASK;
 hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
 hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
 if (HAL_I2C_Init(&hi2c1) != HAL_OK)
 {
   Error_Handler();
 }
 /** Configure Analogue filter
 */
 if (HAL_I2CEx_ConfigAnalogFilter(&hi2c1, I2C_ANALOGFILTER_ENABLE) != HAL_OK)
 {
   Error_Handler();
 }
 /** Configure Digital filter
 */
 if (HAL_I2CEx_ConfigDigitalFilter(&hi2c1, 0) != HAL_OK)
 {
   Error_Handler();
 }
 /* USER CODE BEGIN I2C1_Init 2 */
 /* USER CODE END I2C1_Init 2 */
}
/**
 * @brief LPUART1 Initialization Function
 * @param None
 * @retval None
 */
static void MX_LPUART1_UART_Init(void)
{
 /* USER CODE BEGIN LPUART1_Init 0 */
 /* USER CODE END LPUART1_Init 0 */
 /* USER CODE BEGIN LPUART1_Init 1 */
 /* USER CODE END LPUART1_Init 1 */
 hlpuart1.Instance = LPUART1;
 hlpuart1.Init.BaudRate = 115200;
 hlpuart1.Init.WordLength = UART_WORDLENGTH_8B;
 hlpuart1.Init.StopBits = UART_STOPBITS_1;
 hlpuart1.Init.Parity = UART_PARITY_NONE;
 hlpuart1.Init.Mode = UART_MODE_TX_RX;
 hlpuart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
 hlpuart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
 hlpuart1.Init.ClockPrescaler = UART_PRESCALER_DIV1;
 hlpuart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;
 hlpuart1.FifoMode = UART_FIFOMODE_DISABLE;
 if (HAL_UART_Init(&hlpuart1) != HAL_OK)
 {
   Error_Handler();
 }
 if (HAL_UARTEx_SetTxFifoThreshold(&hlpuart1, UART_TXFIFO_THRESHOLD_1_8) != HAL_OK)
 {
   Error_Handler();
 }
 if (HAL_UARTEx_SetRxFifoThreshold(&hlpuart1, UART_RXFIFO_THRESHOLD_1_8) != HAL_OK)
 {
   Error_Handler();
 }
 if (HAL_UARTEx_DisableFifoMode(&hlpuart1) != HAL_OK)
 {
   Error_Handler();
 }
 /* USER CODE BEGIN LPUART1_Init 2 */
 /* USER CODE END LPUART1_Init 2 */
}
/**
 * @brief TIM1 Initialization Function
 * @param None
 * @retval None
 */
static void MX_TIM1_Init(void)
{
 /* USER CODE BEGIN TIM1_Init 0 */
 /* USER CODE END TIM1_Init 0 */
 TIM_ClockConfigTypeDef sClockSourceConfig = {0};
 TIM_MasterConfigTypeDef sMasterConfig = {0};
 TIM_OC_InitTypeDef sConfigOC = {0};
 TIM_BreakDeadTimeConfigTypeDef sBreakDeadTimeConfig = {0};
 /* USER CODE BEGIN TIM1_Init 1 */
 /* USER CODE END TIM1_Init 1 */
 htim1.Instance = TIM1;
 htim1.Init.Prescaler = 31;
 htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
 htim1.Init.Period = 19999;
 htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
 htim1.Init.RepetitionCounter = 0;
 htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
 if (HAL_TIM_Base_Init(&htim1) != HAL_OK)
 {
   Error_Handler();
 }
 sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
 if (HAL_TIM_ConfigClockSource(&htim1, &sClockSourceConfig) != HAL_OK)
 {
   Error_Handler();
 }
 if (HAL_TIM_PWM_Init(&htim1) != HAL_OK)
 {
   Error_Handler();
 }
 sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
 sMasterConfig.MasterOutputTrigger2 = TIM_TRGO2_RESET;
 sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
 if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig) != HAL_OK)
 {
   Error_Handler();
 }
 sConfigOC.OCMode = TIM_OCMODE_PWM1;
 sConfigOC.Pulse = 0;
 sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
 sConfigOC.OCNPolarity = TIM_OCNPOLARITY_HIGH;
 sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
 sConfigOC.OCIdleState = TIM_OCIDLESTATE_RESET;
 sConfigOC.OCNIdleState = TIM_OCNIDLESTATE_RESET;
 if (HAL_TIM_PWM_ConfigChannel(&htim1, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
 {
   Error_Handler();
 }
 sBreakDeadTimeConfig.OffStateRunMode = TIM_OSSR_DISABLE;
 sBreakDeadTimeConfig.OffStateIDLEMode = TIM_OSSI_DISABLE;
 sBreakDeadTimeConfig.LockLevel = TIM_LOCKLEVEL_OFF;
 sBreakDeadTimeConfig.DeadTime = 0;
 sBreakDeadTimeConfig.BreakState = TIM_BREAK_DISABLE;
 sBreakDeadTimeConfig.BreakPolarity = TIM_BREAKPOLARITY_HIGH;
 sBreakDeadTimeConfig.BreakFilter = 0;
 sBreakDeadTimeConfig.BreakAFMode = TIM_BREAK_AFMODE_INPUT;
 sBreakDeadTimeConfig.Break2State = TIM_BREAK2_DISABLE;
 sBreakDeadTimeConfig.Break2Polarity = TIM_BREAK2POLARITY_HIGH;
 sBreakDeadTimeConfig.Break2Filter = 0;
 sBreakDeadTimeConfig.Break2AFMode = TIM_BREAK_AFMODE_INPUT;
 sBreakDeadTimeConfig.AutomaticOutput = TIM_AUTOMATICOUTPUT_DISABLE;
 if (HAL_TIMEx_ConfigBreakDeadTime(&htim1, &sBreakDeadTimeConfig) != HAL_OK)
 {
   Error_Handler();
 }
 /* USER CODE BEGIN TIM1_Init 2 */
 /* USER CODE END TIM1_Init 2 */
 HAL_TIM_MspPostInit(&htim1);
}
/**
 * @brief GPIO Initialization Function
 * @param None
 * @retval None
 */
static void MX_GPIO_Init(void)
{
 GPIO_InitTypeDef GPIO_InitStruct = {0};
 /* USER CODE BEGIN MX_GPIO_Init_1 */
 /* USER CODE END MX_GPIO_Init_1 */
 /* GPIO Ports Clock Enable */
 __HAL_RCC_GPIOC_CLK_ENABLE();
 __HAL_RCC_GPIOB_CLK_ENABLE();
 __HAL_RCC_GPIOA_CLK_ENABLE();
 GPIO_InitStruct.Pin = GPIO_PIN_5;
 GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
 GPIO_InitStruct.Pull = GPIO_NOPULL;
 GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
 HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
 /*Configure GPIO pins : PC0 PC1 */
 GPIO_InitStruct.Pin = GPIO_PIN_0|GPIO_PIN_1;
 GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
 GPIO_InitStruct.Pull = GPIO_NOPULL;
 GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
 GPIO_InitStruct.Alternate = GPIO_AF8_LPUART1;
 HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);
 /*Configure GPIO pins : USB_DM_Pin USB_DP_Pin */
 GPIO_InitStruct.Pin = USB_DM_Pin|USB_DP_Pin;
 GPIO_InitStruct.Mode = GPIO_MODE_AF_PP;
 GPIO_InitStruct.Pull = GPIO_NOPULL;
 GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
 GPIO_InitStruct.Alternate = GPIO_AF10_USB;
 HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
 /* USER CODE BEGIN MX_GPIO_Init_2 */
 /* USER CODE END MX_GPIO_Init_2 */
}
/* USER CODE BEGIN 4 */
/* USER CODE END 4 */
/**
 * @brief  This function is executed in case of error occurrence.
 * @retval None
 */
void Error_Handler(void)
{
 /* USER CODE BEGIN Error_Handler_Debug */
 /* User can add his own implementation to report the HAL error return state */
 __disable_irq();
 while (1)
 {
 }
 /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
 * @brief  Reports the name of the source file and the source line number
 *         where the assert_param error has occurred.
 * @param  file: pointer to the source file name
 * @param  line: assert_param error line source number
 * @retval None
 */
void assert_failed(uint8_t *file, uint32_t line)
{
 /* USER CODE BEGIN 6 */
 /* User can add his own implementation to report the file name and line number,
    ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
 /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
