import schedule
import psutil
import database_operations as dc


def checkIfProcessRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    '''
    # Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def job():
    process_list = ["firefox", "chrome", "winword", "excel", "powerpnt"]
    for process in process_list:
        print(process.upper() + " chalu" if checkIfProcessRunning(process) else process.upper() + " bandh")
    print("=================================================================")


schedule.every(10).seconds.do(job)
while True:
    schedule.run_pending()
