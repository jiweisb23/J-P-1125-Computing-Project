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

datefmt = '%Y-%m-%d %H:%M'
t = '2021-11-21 09:00:58.593595'
t_ = t.split(":")[0] + ':' + t.split(":")[1]
v = datetime.strptime(t_, datefmt )
print(v)





if __name__ == "__optimizer__":

    print("Optimizing2!")



