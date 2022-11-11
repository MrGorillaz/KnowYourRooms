#include "sys/time.h"
#include "BLEDevice.h"
#include "BLEServer.h"
#include "BLEUtils.h"
#include "esp_sleep.h"
#include "esp_bt_device.h"
#include "Adafruit_VL53L0X.h"

int GPIO_DEEP_SLEEP_DURATION = 10;  // sleep 10 seconds and then wake up
RTC_DATA_ATTR static int working_mode;
RTC_DATA_ATTR static bool initialized;
int loop_counter = 0;
long duration; // variable for the duration of sound wave travel
int distance; // variable for the distance measurement

//BLE SETTINGS
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define PIR_PIN 33

Adafruit_VL53L0X lox = Adafruit_VL53L0X();

bool deviceConnected = false;
bool oldDeviceConnected = false;

BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic;
BLEService *pService;
BLEAdvertising *pAdvertising;

//Get if a Device is connected via BLE
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      Serial.println("Connected");
      deviceConnected = true;
    };

    void onDisconnect(BLEServer* pServer) {
      Serial.println("Disconnected");
      deviceConnected = false;
    }
};

//Service Characteric for Writing Data
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      Serial.println("I am Here");
      std::string rxValue = pCharacteristic->getValue();
      Serial.println("something has been written");

       if(rxValue.length() == 4){

          std::string code;
          code.append(1,rxValue[0]);
          code.append(1,rxValue[1]);
          code.append(1,rxValue[2]);
          
          //Pseudo Pasword for Writing
          if (code == "WRT"){

            Serial.println("AUTH SUCCESSFULL");
            working_mode = rxValue[3];
            
          }
       }
      
      if (rxValue.length() > 0) {
        Serial.println("*********");
        Serial.print("Received Value: ");
        for (int i = 0; i < rxValue.length(); i++)
          Serial.print(rxValue[i]);

        Serial.println();
        Serial.println("*********");
      }
    }
};



//####################################################################################################################################
//Sensor Methods
//####################################################################################################################################
int get_distance(){

  VL53L0X_RangingMeasurementData_t measure;
    
  Serial.print("Reading a measurement... ");
  lox.rangingTest(&measure, false); // pass in 'true' to get debug data printout!

  if (measure.RangeStatus != 4) {  // phase failures have incorrect data
    Serial.print("Distance (mm): "); Serial.println(measure.RangeMilliMeter);
    distance = measure.RangeMilliMeter / 10;
    if (distance > 70){
      distance = 0;
    }
  } else {
    Serial.println(" out of range ");
    distance = 0;
  }

  return distance;
}


bool get_pir(){

  Serial.print("Get PIR Status: ");
  pinMode(PIR_PIN,INPUT);
  int pir_status = 0;

  
  for (int i=0; i<10;i++){
    pir_status = digitalRead(PIR_PIN);
    delay(200);
    if (pir_status == HIGH){
      break;
    }
  }
  
  if(pir_status == HIGH){
    Serial.println("Motion Detected");
    return true;
  }
  else{
    Serial.println("No Motion here");
    return false;
  }

}


bool get_trigger_status (){
  esp_sleep_wakeup_cause_t wakeup_reason;

  wakeup_reason = esp_sleep_get_wakeup_cause();

  switch(wakeup_reason)
  {
    case ESP_SLEEP_WAKEUP_EXT0 : Serial.println("Wakeup caused by external signal using RTC_IO"); return true; break;
    case ESP_SLEEP_WAKEUP_EXT1 : Serial.println("Wakeup caused by external signal using RTC_CNTL"); break;
    case ESP_SLEEP_WAKEUP_TIMER : Serial.println("Wakeup caused by timer"); break;
    case ESP_SLEEP_WAKEUP_TOUCHPAD : Serial.println("Wakeup caused by touchpad"); break;
    case ESP_SLEEP_WAKEUP_ULP : Serial.println("Wakeup caused by ULP program"); break;
    default : Serial.printf("Wakeup was not caused by deep sleep: %d\n",wakeup_reason); break;
  }
  return false;
}



int get_battery(){

  return 101; //101% = Powerplugged
  
}


void setBeacon() {
  
  char beacon_data[22];
  uint16_t beconUUID = 0xFEAA;
  
  BLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
  
  oAdvertisementData.setFlags(0x06); // GENERAL_DISC_MODE 0x02 | BR_EDR_NOT_SUPPORTED 0x04
  oAdvertisementData.setCompleteServices(BLEUUID(beconUUID));

  //Get Sensor-Data
  bool trigger_status = get_trigger_status();
  bool used_status = false;
  char sensor_type = 'T'; //TABLE
  char temp_prefix = '+';
  bool pir_status = get_pir();
  int distance = get_distance();
  int perc_battery = get_battery();

  if ( ((distance <= 70)&&(distance>0) ) && (pir_status == true)){
    used_status = true;
  }
  
  //Set Eddystone Beacon
  beacon_data[0] = 0x20;  // Eddystone Frame Type (Unencrypted Eddystone-TLM)
  beacon_data[1] = 0x00;  // TLM version
  beacon_data[2] = working_mode;  //
  beacon_data[3] = sensor_type; // 'T' for Table
  beacon_data[4] =  used_status;    // 
  beacon_data[5] =  trigger_status;
  beacon_data[6] = false;  //
  beacon_data[7] = false;  // 
  beacon_data[8] = distance;
  beacon_data[9] = false;
  beacon_data[10] = false;
  beacon_data[11] = false;
  beacon_data[12] = false;
  beacon_data[13] = perc_battery;
  
  oAdvertisementData.setServiceData(BLEUUID(beconUUID), std::string(beacon_data, 14));
  
  pAdvertising->setScanResponseData(oAdvertisementData);

}

//Get Working Mode and set duration for Deep Sleep
int get_deep_sleep_duration(int wm){

  if (wm == 1){
      Serial.println("Set Sleep for 300 Seconds (5 Minutes)");
      return 300;
  }
  if (wm == 2){
      Serial.println("Set Sleep for 60 Seconds (1 Minute)");
    return 60;
    
  }
  Serial.println("Set Sleep for 3600 Seconds (1 Hour)"); 
  return 3600;
}






//##########################


void printBLEAdress() {
 
  const uint8_t* point = esp_bt_dev_get_address();
 
  for (int i = 0; i < 6; i++) {
 
    char str[3];
 
    sprintf(str, "%02X", (int)point[i]);
    Serial.print(str);
 
    if (i < 5){
      Serial.print(":");
    }
 
  }

  Serial.println();
}


//#############################

void setup() {

    
  Serial.begin(115200);
 

  if (!initialized){
    Serial.printf("Initialized: %d\n",initialized);
    initialized = true;
    working_mode = 1;
  }

   if (!lox.begin()) {
    Serial.println(F("Failed to boot VL53L0X"));
   }
   else{
    lox.configSensor(Adafruit_VL53L0X::VL53L0X_SENSE_HIGH_SPEED);
   }

  Serial.printf("Initialized: %d\n",initialized);
  Serial.printf("Working_mode: %d\n",working_mode);
  
  GPIO_DEEP_SLEEP_DURATION = get_deep_sleep_duration(working_mode);
  esp_sleep_enable_ext0_wakeup(GPIO_NUM_33,1); //1 = High, 0 = Low

  
  
  // Create the BLE Device
  BLEDevice::init("SEDUS-TABLE");
  // Create the BLE Server
  pServer = BLEDevice::createServer();

  //for Serial-Log and identification of ESP-Board over BLE
  Serial.print("MY BLE-ADRESS IS: ");
  printBLEAdress();

  pService = pServer->createService(SERVICE_UUID);
  
  pCharacteristic = pService->createCharacteristic(
                                         CHARACTERISTIC_UUID,
                                         BLECharacteristic::PROPERTY_READ |
                                         BLECharacteristic::PROPERTY_WRITE
                                       );

   pServer->setCallbacks(new MyServerCallbacks());
   pCharacteristic->setCallbacks(new MyCallbacks());

  pCharacteristic->setValue("Start");
  
  pAdvertising = pServer->getAdvertising();

  //Get Sensordata and set it in Eddystone Beacon
  setBeacon();

  //start BLE-Services
  pService->start();
   // Start advertising
  pAdvertising->start();
  Serial.println("Advertizing started...");
  //advertise for  7.5 Seconds
  delay(7500);

  //check if edge-device is connected
  if (deviceConnected == false){
  Serial.printf("enter deep sleep startup\n");
  esp_deep_sleep(1000000ULL * GPIO_DEEP_SLEEP_DURATION);
  Serial.printf("in deep sleep\n");
  }
}

void loop() {

 delay(2000);
 loop_counter++;

 if(!deviceConnected || loop_counter>20){
  Serial.printf("enter deep sleep loop\n");
  esp_deep_sleep(1000000ULL * GPIO_DEEP_SLEEP_DURATION);
 }
 
}
