import os
from datetime import datetime, date

directory_name = "json_files/world_leaders/"
prev_date = '2021-12-15'  # str(datetime.date.today() - datetime.timedelta(days=1))
today_date = str(date.today()) # + datetime.timedelta(days=1))

for filename in os.listdir(directory_name):
    f = os.path.join(directory_name, filename)
    print(f)
    print("creation time: " + str(datetime.fromtimestamp(os.path.getctime(f))))
    print("modification time: " + str(datetime.fromtimestamp(os.path.getmtime(f))))
    print("---------------------------------------------")
    if os.path.isfile(f):
        if prev_date in f:
            os.replace(f, f.replace(prev_date, today_date))
