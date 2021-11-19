from datetime import datetime
import pytz

#$x = timezone(timedelta(hours=-5))
pytz.utc.localize( datetime.utcnow() )  
print(str(datetime.now()))
#print(str(timezone.now()))