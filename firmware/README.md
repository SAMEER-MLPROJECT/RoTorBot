# Firmware

Status for Round 1: the ESP32-S3 pin map is frozen (`esp32s3/include/pins.h`, matching drawing ET-RRB-E01).
Control firmware (1 kHz loops, torque-vector mixer, kill latch) and the Raspberry Pi 5 vision code are next, after parts arrive.

| Target | Role |
| --- | --- |
| ESP32-S3 DevKitC-1 | 1 kHz speed PI, pendulum PD, roll loop to the ballast sled, axle levelling, watchdog, kill latch |
| Raspberry Pi 5 | Twin-Eye vision, lane Kalman filter, Gate-and-Cue state machine, pendulum timing |
