import shutil
import datetime
import schedule
import time
import os


#back up scheduler

def backup():
    #ensure the back up folder exists
    backup_folder = "backups"
    os.makedirs(backup_folder,exist_ok = True )

    #source and destination
    source = "expenses.db"
    timestamp =datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destination = f"{backup_folder}/expenses_backup_{timestamp}.db"


    #perform backup
    shutil.copy2(source, destination)
    print(f"Backup created at {destination}")

    # Schedule the backup to run weekly at a specific time
schedule.every().day.do(backup)  # Adjust time as needed (HH:MM in 24-hour format)

print("Backup scheduler is running. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute if the scheduled time has arrived
