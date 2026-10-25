// RoToRBot 
// Matches drawing ET-RRB-E01 Rev A (Round 1 submission, Figure 6). Team EigenThinker.
#pragma once

#define PIN_UART_PI_TX      17   // -> Pi GPIO15 (RXD)
#define PIN_UART_PI_RX      18   // <- Pi GPIO14 (TXD)

// BNO085 IMU (I2C, 400 kHz) 
#define PIN_IMU_SDA          8
#define PIN_IMU_SCL          9
#define PIN_IMU_INT         10
#define PIN_IMU_RST         11

//  Dual 20 A H-bridge, PWM + DIR per channel 
#define PIN_M1_PWM           4   // drive motor L
#define PIN_M1_DIR           5
#define PIN_M2_PWM           6   // drive motor R
#define PIN_M2_DIR           7

//  Quadrature encoders (3.3 V) 
#define PIN_ENC_L_A         12
#define PIN_ENC_L_B         13
#define PIN_ENC_R_A         14
#define PIN_ENC_R_B         21

//      Ballast-sled steering: TMC2209 + NEMA 17
#define PIN_SLED_STEP       39
#define PIN_SLED_DIR        40
#define PIN_SLED_EN         41
#define PIN_SLED_UART       42   // PDN_UART through 1 kOhm
#define PIN_SLED_HOME       16   // limit switch, active low, internal pull-up 

#define PIN_LEVEL_SERVO     47

// Safety and power monitoring 
#define PIN_KILL_PWM_IN     15   // kill receiver CH5 pulse width (read-only K2 is driven in hardware)
#define PIN_K2_SENSE         2   // optocoupler on the K2 output side
#define PIN_PACK_ADC         1   // ADC1_CH0, divider 100k / 10k
#define PIN_STATUS_LED      48


#define PWM_FREQ_HZ         20000
#define CONTROL_LOOP_HZ     1000
#define PI_TARGET_RATE_HZ   100
#define TARGET_TIMEOUT_MS   200    // watchdog: stop if Pi targets are older than this one ,NOTE: we will adjust it with experimentation
#define MOTOR_CURRENT_LIMIT_A 10.0f
#define PACK_DIVIDER_RATIO  (110.0f / 10.0f)
#define PACK_WARN_V         19.8f  // 3.3 V per cell
#define PACK_STOP_V         19.2f  // 3.2 V per cell, controlled stop under load
#define SLED_TRAVEL_MM      70.0f
#define PENDULUM_SWING_LIMIT_DEG 60.0f
