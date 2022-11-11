import requests


working_mode={
                "operation":"modify",
                "mode": 0,
                "initiator": "pir_sensor",
            }

url = 'https://localhost:8443/setWorkingMode'

result =  requests.post(url,verify=False,json=working_mode)
print(result.content)
settings = requests.get('https://localhost:8443/getWorkingMode',verify=False)
print(settings.content)