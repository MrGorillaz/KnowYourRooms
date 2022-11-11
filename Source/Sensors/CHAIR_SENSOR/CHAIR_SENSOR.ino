#include "sys/time.h"
#include "BLEDevice.h"
#include "BLEServer.h"
#include "BLEUtils.h"
#include "esp_sleep.h"

#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define SEAT_PIN 13

int GPIO_DEEP_SLEEP_DURATION = 10;  // sleep 10 seconds and then wake up
RTC_DATA_ATTR static int working_mode;
RTC_DATA_ATTR static bool initialized;
int loop_counter = 0;

bool deviceConnected = false;
bool oldDeviceConnected = false;

BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic;
BLEService *pService;
BLEAdvertising *pAdvertising;

//Erkennt ob eine Verbindung mit dem BLE-Server aufgebaut wurde.
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

/* #######################################################################
 * ##################### SENSOR METHODEN #################################
 * #######################################################################
 */

/*  method:       get_seat_status
 *  @description: Ermittelt 
 * 
 */
bool get_seat_status (){
  
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
  Serial.print("Get PIR Status: ");
  pinMode(SEAT_PIN,INPUT);

  int seat_status = analogRead(SEAT_PIN);
  if(seat_status > 0){
    Serial.println("Sitting Detected");
    return true;
  }
  else{
    Serial.println("No sitting here");
    return false;
  }
  
}

int get_battery(){

  return 101; //101% = Powerplugged
  
}

int get_seat_detail(){

  pinMode(SEAT_PIN,INPUT);

  int seat_detail = analogRead(SEAT_PIN);
  Serial.print("Seat-Resistance:");
  Serial.println(seat_detail);
  return seat_detail;
  
  
}


void setBeacon() {
  
  char beacon_data[22];
  uint16_t beconUUID = 0xFEAA;
  
  BLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
  
  oAdvertisementData.setFlags(0x06); // GENERAL_DISC_MODE 0x02 | BR_EDR_NOT_SUPPORTED 0x04
  oAdvertisementData.setCompleteServices(BLEUUID(beconUUID));
  
  
  bool used_status = get_seat_status();
  int seat_detail = get_seat_detail();
  char sensor_type = 'C'; //CHAIR
  int perc_battery = get_battery();

  unsigned char bytes[2];
  unsigned int n = seat_detail;

  bytes[0] = (n >> 8) & 0xFF;
  bytes[1] = (n >> 0) & 0xFF;
  

  beacon_data[0] = 0x20;  // Eddystone Frame Type (Unencrypted Eddystone-TLM)
  beacon_data[1] = 0x00;  // TLM version
  beacon_data[2] = working_mode;  //
  beacon_data[3] = sensor_type;
  beacon_data[4] =  used_status;    // 
  beacon_data[5] =  used_status;
  beacon_data[6] = false;  //Vorzeichen (+ oder - Grad)
  beacon_data[7] = false;  // 
  beacon_data[8] = (seat_detail >> 8) & 0xFF; //bigger_byte;
  beacon_data[9] = (seat_detail >> 0) & 0xFF; //bigger_byte;
  beacon_data[10] = false;
  beacon_data[11] = false;
  beacon_data[12] = false;
  beacon_data[13] = perc_battery;
  
  oAdvertisementData.setServiceData(BLEUUID(beconUUID), std::string(beacon_data, 14));
  
  pAdvertising->setScanResponseData(oAdvertisementData);

}

/*Method:        get_deep_sleep_duration
//@description:  Gibt die Deepsleep-dauer in Sekunden abhänging vom Workingmode zurück
//@param wm:     Integerwert für Workingmode
*/
int get_deep_sleep_duration(int wm){

  //Working_mode 1: 
  if (wm == 1){
      Serial.println("Set Sleep for 300 Seconds (5 Minutes)");
      return 300;
  }
  //Working_Mode 2:
  if (wm == 2){
      Serial.println("Set Sleep for 60 Seconds (1 Minute)");
    return 60;
    
  }
  //Sonstiges
  Serial.println("Set Sleep for 3600 Seconds (1 Hour)"); 
  return 3600;
}

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
  esp_sleep_enable_ext0_wakeup(GPIO_NUM_13,1); //1 = High, 0 = Low

  
  
  // Create the BLE Device
  BLEDevice::init("SEDUS_SEAT");
  // Create the BLE Server
  pServer = BLEDevice::createServer();
  
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
  delay(10000);
  //pAdvertising->stop();
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
