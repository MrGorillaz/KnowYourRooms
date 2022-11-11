#include "sys/time.h"
#include "BLEDevice.h"
#include "BLEServer.h"
#include "BLEUtils.h"
#include "esp_sleep.h"
#include "DHT.h"
#include <Wire.h>    // I2C library
#include "ccs811.h"  // CCS811 library

int GPIO_DEEP_SLEEP_DURATION = 10;  // sleep 10 seconds and then wake up
//RTC_DATA_ATTR static time_t last;        // remember last boot in RTC Memory
//RTC_DATA_ATTR static uint32_t bootcount; // remember number of boots in RTC Memory
RTC_DATA_ATTR static int working_mode;
RTC_DATA_ATTR static bool initialized;
int loop_counter = 0;



#define DHTPIN 4     // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11   // DHT 11
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define PIR_PIN 33 

bool deviceConnected = false;
bool oldDeviceConnected = false;

DHT dht(DHTPIN, DHTTYPE);
CCS811 ccs811; 
BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic;
BLEService *pService;
BLEAdvertising *pAdvertising;

//Servercallback to detect if a device is connected or disconnected via BLE
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

//Callback for Service Characterictic
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      Serial.println("I am Here");

      //Get Characters which have been send via a write-command to the Service
      std::string rxValue = pCharacteristic->getValue();
      Serial.println("something has been written");

       //only if the written Data is 4 Bytes long something should happen
       if(rxValue.length() == 4){

          std::string code;
          code.append(1,rxValue[0]);
          code.append(1,rxValue[1]);
          code.append(1,rxValue[2]);
          
          //Codeword for Writing the new Working_mode to the device
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

//Sensor Methods

//get max value in an array
int get_max (int arr[], int n){

  int max = arr[0];

  for (int i = 1; i< n; i++){

    if (arr[i] > max){
      max = arr[i];
    }
  }
  return max;
  
}

//get current Air_qualitiy
int get_air_quality(){

  int air_max[5] = {0};
  bool ok= ccs811.begin();

  if( !ok ) {
    
    Serial.println("setup: CCS811 begin FAILED");
    return 0;
  }


  bool ok_start= ccs811.start(CCS811_MODE_10SEC);
  if( !ok_start ) {
    
    Serial.println("setup: CCS811 start FAILED");
    return 0;
  }

  uint16_t eco2, etvoc, errstat, raw;
  for (int i = 0; i < 5; i++)
  {
    delay(10000);
    ccs811.read(&eco2,&etvoc,&errstat,&raw);
    if( errstat==CCS811_ERRSTAT_OK ) { 
      Serial.print("CCS811: ");
      Serial.print("eco2=");  Serial.print(eco2);     Serial.print(" ppm  ");
      Serial.print("etvoc="); Serial.print(etvoc);    Serial.print(" ppb  ");
      Serial.println();
      air_max[i] = eco2;
      delay(10000);
      } 
    else if( errstat==CCS811_ERRSTAT_OK_NODATA ) {
      Serial.println("CCS811: waiting for (new) data");
      delay(10000);
      } 
    else if( errstat & CCS811_ERRSTAT_I2CFAIL ) { 
      Serial.println("CCS811: I2C error");
      return 0;
      } 
    else {
      Serial.print("CCS811: errstat="); Serial.print(errstat,HEX); 
      Serial.print("="); Serial.println( ccs811.errstat_str(errstat) );
      return 0;
      }
   }
  return get_max(air_max,5);
  
}



//get room Temperature
int get_temperature(){
  dht.begin();
  delay(250);
  int temp = dht.readTemperature();
  Serial.print("temperature: ");
  Serial.println(temp);
  return temp;
}

//get Humidity
int get_humidity (){
  delay(250);
  dht.begin();
  delay(200);
  int humidity = dht.readHumidity();
  Serial.print("Humidity: ");
  Serial.println(humidity);
  return humidity;
  
}



//Return wakeup reason
bool get_pir_status (){
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
  pinMode(PIR_PIN,INPUT);

  int pir_status = digitalRead(PIR_PIN);
  if(pir_status == HIGH){
    Serial.println("Motion Detected");
    return true;
  }
  else{
    Serial.println("No Motion here");
    return false;
  }
  
}

//pseudo battery function
int get_battery(){

  return 101; //101% = Powerplugged
  
}


  
void setBeacon() {
  
  char beacon_data[22];
  uint16_t beconUUID = 0xFEAA;
  
  BLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
  
  oAdvertisementData.setFlags(0x06); // GENERAL_DISC_MODE 0x02 | BR_EDR_NOT_SUPPORTED 0x04
  oAdvertisementData.setCompleteServices(BLEUUID(beconUUID));
  
  
  //get Sensor Data
  int temperature = get_temperature();
  bool pir_status = get_pir_status();
  bool used_status = false;
  char temp_prefix = '+';
  char sensor_type = 'R'; //ROOM
  int air_value = get_air_quality();
  int humidity = get_humidity();
  int perc_battery = get_battery();

  unsigned char bytes[2];
  unsigned int n = air_value;

  bytes[0] = (n >> 8) & 0xFF;
  bytes[1] = (n >> 0) & 0xFF;

  if (pir_status == true){
    used_status = true;
  }

  if (temperature < 0){
    temp_prefix = '-';
  }
  
  beacon_data[0] = 0x20;  // Eddystone Frame Type (Unencrypted Eddystone-TLM)
  beacon_data[1] = 0x00;  // TLM version
  beacon_data[2] = working_mode;  //
  beacon_data[3] = sensor_type;
  beacon_data[4] =  used_status;    // 
  beacon_data[5] = pir_status;
  beacon_data[6] = temp_prefix;
  beacon_data[7] = temperature;  // 
  beacon_data[8] = humidity;
  beacon_data[9] = (air_value >> 8) & 0xFF; //bigger_byte
  beacon_data[10] = (air_value >> 0) & 0xFF;; //lower_byte
  beacon_data[11] = false;
  beacon_data[12] = false;
  beacon_data[13] = perc_battery;
  
  oAdvertisementData.setServiceData(BLEUUID(beconUUID), std::string(beacon_data, 14));
  
  pAdvertising->setScanResponseData(oAdvertisementData);

}

//returns sleep duration based on working mode
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



void setup() {

    
  Serial.begin(115200);
  Wire.begin();
  
  // Enable CCS811
  ccs811.set_i2cdelay(50);

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
  BLEDevice::init("SEDUS_ROOM");
  // Create the BLE Server
  pServer = BLEDevice::createServer();
  


  // Create Service with the specific SERVICE_UUID
  pService = pServer->createService(SERVICE_UUID);

  // Create Characteristic inside the Service with the specific CHARACTERISTIC_UUID
  // The Service should be able to handle Read and Write operations via BLE 
  pCharacteristic = pService->createCharacteristic(
                                         CHARACTERISTIC_UUID,
                                         BLECharacteristic::PROPERTY_READ |
                                         BLECharacteristic::PROPERTY_WRITE
                                       );

  // Setup the Callbacks for the Server and Characteristik Callsbacks
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
