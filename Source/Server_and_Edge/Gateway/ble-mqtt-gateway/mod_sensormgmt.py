import pexpect
from time import sleep

#create a BLE connection with GATTOOL and pexpect
#Write the working mode byte to a given ble_address
def set_sensor_working_mode(ble_address,mode):
    try:
               gatt_device = pexpect.spawn("gatttool -I")
               gatt_device.sendline("connect {}".format(ble_address))
               sleep(0.5)
               #SENDS W(0x57),R(0x52),T(0x54) and WORKINGMODe{0,1,2}
               gatt_device.sendline("char-write-req 0x002a 5752540{}".format(mode))
               sleep(0.5)
               gatt_device.sendline("disconnect")
               sleep(0.5)
               gatt_device.sendline("exit")
               gatt_device.kill(0)
    except:
            print("error writing on {}".format(ble_address))
            pass