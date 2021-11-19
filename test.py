from datetime import datetime
from datetime import timedelta
import pytz

#$x = timezone(timedelta(hours=-5))
pytz.utc.localize( datetime.utcnow() )  
print(str(datetime.now()-timedelta(hours=5)))
#print(str(timezone.now()))