#include "sys/time.h"
#include "BLEDevice.h"
#include "BLEServer.h"
#include "BLEUtils.h"
#include "esp_sleep.h"
#include "esp_bt_device.h"

#define echoPin 22 // attach pin D2 Arduino to pin Echo of HC-SR04
#define trigPin 23 //attach pin D3 Arduino to pin Trig of HC-SR04
#define PIR_PIN 33

//BLE IDs
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

//Globals for BLE-handling
BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic;
BLEService *pService;
BLEAdvertising *pAdvertising;


//Variables which survice Deep-Sleep-Mode
RTC_DATA_ATTR static int working_mode;
RTC_DATA_ATTR static bool initialized;

//default sleep for 60 seconds
int GPIO_DEEP_SLEEP_DURATION = 60; 
int loop_counter = 0; //Counter for Loops when BLE-Device is connected
long duration; // variable for the duration of sound wave travel
int distance; // variable for the distance measurement
bool deviceConnected = false;
bool oldDeviceConnected = false;



//Callback for recognizing a Connection with the BLE-Server
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

//Callback for recieving Data over BLE
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
          
          //Authentification
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


//retrun distance to an Object by Ultrasonic
int get_distance(){

  pinMode(trigPin, OUTPUT); // Sets the trigPin as an OUTPUT
  pinMode(echoPin, INPUT); // Sets the echoPin as an INPUT
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  // Sets the trigPin HIGH (ACTIVE) for 10 microseconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  // Reads the echoPin, returns the sound wave travel time in microseconds
  duration = pulseIn(echoPin, HIGH);
  // Calculating the distance
  distance = duration * 0.034 / 2; // Speed of sound wave divided by 2 (go and back)
  // Displays the distance on the Serial Monitor
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  if (distance >70){
    distance = 0;
  }

  return distance;
}

//get status of a PIR
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

// Reason why the ESP32 woke up
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


//Dummy Function for Battery
// TO BE Implementend in the near future
int get_battery(){

  return 101; //101% = Powerplugged
  
}


//Build Eddystone Beacon
void setBeacon() {
  
  char beacon_data[22];
  uint16_t beconUUID = 0xFEAA;
  
  BLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
  
  oAdvertisementData.setFlags(0x06); // GENERAL_DISC_MODE 0x02 | BR_EDR_NOT_SUPPORTED 0x04
  oAdvertisementData.setCompleteServices(BLEUUID(beconUUID));

  
  bool trigger_status = get_trigger_status();
  bool used_status = false;
  char sensor_type = 'T'; //Table
  char temp_prefix = '+';
  bool pir_status = get_pir();
  int distance = get_distance();
  int perc_battery = get_battery();


  if ( ((distance <= 70)&& (distance > 0)) && (pir_status == true)){
    used_status = true;
  }
  
  //Set Bits for Beacon-data
  beacon_data[0] = 0x20;  // Eddystone Frame Type (Unencrypted Eddystone-TLM)
  beacon_data[1] = 0x00;  // TLM version
  beacon_data[2] = working_mode;  //
  beacon_data[3] = sensor_type; // T for Table
  beacon_data[4] =  used_status;    // 
  beacon_data[5] =  trigger_status;
  beacon_data[6] = false;
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

  Serial.printf("Initialized: %d\n",initialized);
  Serial.printf("Working_mode: %d\n",working_mode);
  
  GPIO_DEEP_SLEEP_DURATION = get_deep_sleep_duration(working_mode);
  esp_sleep_enable_ext0_wakeup(GPIO_NUM_33,1); //1 = High, 0 = Low

  
  
  // Create the BLE Device
  BLEDevice::init("SEDUS-TABLE");
  // Create the BLE Server
  pServer = BLEDevice::createServer();

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
  setBeacon();
  pService->start();
   // Start advertising
  pAdvertising->start();
  Serial.println("Advertizing started...");
  //adversiere 7.5 Sekunden
  delay(7500);
  //pAdvertising->stop();
  if (deviceConnected == false){
  Serial.printf("enter deep sleep startup\n");
  esp_deep_sleep(1000000ULL * GPIO_DEEP_SLEEP_DURATION);
  Serial.printf("in deep sleep\n");
  }
}

void loop() {

 // Loop top send ESP32 to Deep Sleep by force after a given time
 delay(2000);
 loop_counter++;

 if(!deviceConnected || loop_counter>20){
  Serial.printf("enter deep sleep loop\n");
  esp_deep_sleep(1000000ULL * GPIO_DEEP_SLEEP_DURATION);
 }
 
}
