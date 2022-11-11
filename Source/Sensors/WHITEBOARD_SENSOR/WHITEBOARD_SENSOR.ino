#include "sys/time.h"
#include "BLEDevice.h"
#include "BLEServer.h"
#include "BLEUtils.h"
#include "esp_sleep.h"
#include <Adafruit_MPU6050.h>
//#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;
using namespace std;
int gyro_counter = 0;
int max_gyro_x = 0;
int max_gyro_y = 0;
int max_gyro_z = 0;
int gyro_temp = 0;

//default sleep for 60 seconds
int GPIO_DEEP_SLEEP_DURATION = 60;

RTC_DATA_ATTR static int working_mode;
RTC_DATA_ATTR static bool initialized;
int loop_counter = 0;


#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

//Wakeup Trigger Pin
#define VIBRATION_PIN 13

bool deviceConnected = false;
bool oldDeviceConnected = false;

//Globals für BLE-Handling
BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic;
BLEService *pService;
BLEAdvertising *pAdvertising;

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


//Get the maximum value out of an array
int get_max (int arr[], int n){

  int max = arr[0];

  for (int i = 1; i< n; i++){

    if (arr[i] > max){
      max = arr[i];
    }
  }
  return max;
  
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

//Get Vibration from S801
int get_vibration(){

  int vib_array[10] = {0};
  for (int i = 0; i< 10; i++){
  int value = pulseIn(VIBRATION_PIN, HIGH);
  //Reduce the Sensorvalue to fit into a byte
  vib_array[i] = value/100;
  delay(100);
  Serial.printf("Read Value %d\n",vib_array[i]);
  }
  int max_vibration_value = get_max(vib_array,10);

  
  Serial.printf("Max Value is: %d\n",max_vibration_value);
  return max_vibration_value;
  
}


//Get the Values out of Gyro Sensor
bool get_gyro_usage(){

  delay(10); // will pause Zero, Leonardo, etc until serial console opens

  Serial.println("Adafruit MPU6050 test!");

  // Try to initialize!
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");

  //Setup the MPU6050
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_250_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);

  sensors_event_t a, g, temp;
  mpu.getEvent(&a ,&g, &temp);
  float gyro_first[3] ={g.gyro.x,g.gyro.y,g.gyro.z};
  int gyro_x[500] = {0};
  int gyro_y[500] = {0};
  int gyro_z[500] = {0};

  for (int i = 0; i<500; i++){
      mpu.getEvent(&a ,&g, &temp);

      // set to 0.03 by a few try and errors
      // but it works quite good
      float diff = 0.03;

      //abs gives the differnce between two values
      if (abs(gyro_first[0]-g.gyro.x) > diff || abs(gyro_first[1]-g.gyro.y) > diff || abs(gyro_first[2]-g.gyro.z) > diff){

        
        // to get a measureble difference we multiply by 100
        gyro_x[gyro_counter] = abs(gyro_first[0]-g.gyro.x)*100;
        gyro_y[gyro_counter] = abs(gyro_first[1]-g.gyro.y)*100;
        gyro_z[gyro_counter] = abs(gyro_first[2]-g.gyro.z)*100;
        
        Serial.printf("USED %d x:%d\ty:%d\tz:%d\n",gyro_counter,gyro_x[gyro_counter],gyro_y[gyro_counter],gyro_z[gyro_counter]);
        //count the number of valid Measurements
        gyro_counter++;
      }
    
  }

  //get the biggest values out of the given axis.
  max_gyro_x = get_max(gyro_x,500);
  max_gyro_y = get_max(gyro_y,500);
  max_gyro_z = get_max(gyro_z,500);

// Cut of to get into 1-Byte
 if (max_gyro_x >255){
  max_gyro_x = 255;
 }
  if (max_gyro_y >255){
  max_gyro_y = 255;
 }
  if (max_gyro_y >255){
  max_gyro_y = 255;
 }

  //Get the Temperature out of MPU6050
  gyro_temp = temp.temperature;

  Serial.printf("Maximum:\tX: %d\tY: %d\tZ: %d\n",max_gyro_x,max_gyro_y,max_gyro_z);
  
  Serial.printf("Temperature: %d °C\n",gyro_temp);

  // if there are more the 100 valid measurements then a usage is given
  if (gyro_counter > 100){
    return true;
  }else{
    return false;
  }
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

  get_gyro_usage();
  
  bool trigger_status = get_trigger_status();
  bool used_status = false;
  int vibration_detail = get_vibration();
  int gyro_x = max_gyro_x;
  int gyro_y = max_gyro_y;
  int gyro_z = max_gyro_z;
  char sensor_type = 'W'; //CHAIR
  char temp_prefix = '+';
  int temperature = gyro_temp;
  int perc_battery = get_battery();


  //if ((vibration_detail || gyro_counter) != 0){
  if ((vibration_detail != 0 ) && (gyro_counter != 0)){

      used_status = true;
      
  }

  if ( temperature < 0){
  
    temp_prefix = '-';
  }

  beacon_data[0] = 0x20;  // Eddystone Frame Type (Unencrypted Eddystone-TLM)
  beacon_data[1] = 0x00;  // TLM version
  beacon_data[2] = working_mode;  //
  beacon_data[3] = sensor_type; // 'W' for Whiteboard
  beacon_data[4] =  used_status;    // 
  beacon_data[5] =  trigger_status;
  beacon_data[6] = temp_prefix; 
  beacon_data[7] = temperature;  // 
  beacon_data[8] = (vibration_detail >> 8) & 0xFF; //bigger_byte;
  beacon_data[9] = (vibration_detail >> 0) & 0xFF; //lower_byte;
  beacon_data[10] = gyro_x;
  beacon_data[11] = gyro_y;
  beacon_data[12] = gyro_z;
  beacon_data[13] = perc_battery;
  
  oAdvertisementData.setServiceData(BLEUUID(beconUUID), std::string(beacon_data, 14));
  
  pAdvertising->setScanResponseData(oAdvertisementData);

}

//Set Sleep duration based on Working Mode
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
  BLEDevice::init("SEDUS-WHITEBOARD");
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

 // Loop top send ESP32 to Deep Sleep by force after a given time
 delay(2000);
 loop_counter++;

 if(!deviceConnected || loop_counter>20){
  Serial.printf("enter deep sleep loop\n");
  esp_deep_sleep(1000000ULL * GPIO_DEEP_SLEEP_DURATION);
 }
 
}
