from datetime import datetime
from datetime import timedelta
import pytz


'''

#$x = timezone(timedelta(hours=-5))
pytz.utc.localize( datetime.utcnow() )  
print(str(datetime.now()-timedelta(hours=5)))

#print(str(timezone.now()))





for i in range(10):

	print(i)


x = sum(sum(i for i in range(1,10)) for j in range(1,10))
print(x)

'''



test_dict = {'2': {'last': datetime(2021, 11, 21, 9, 0), 'currentCharge': 15, 'desiredCharge': 90, 'departureTime': datetime(2021, 11, 21, 18, 31), 'newStatus': 'Arrived', 'lastChargingStatus': None, 'recommendedChargeTime': None}, '1': {'last': datetime(2021, 11, 21, 9, 1), 'currentCharge': 10, 'desiredCharge': 90, 'departureTime': datetime(2021, 11, 21, 17, 31), 'newStatus': 'Charging', 'lastChargingStatus': None, 'recommendedChargeTime': None}}
for v in test_dict:
	print(v)


s = ''
for i in range(1,10):
	s+='i'

print(s)

print(0 + True & True)

if __name__ == "__optimizer__":

    print("Optimizing2!")



