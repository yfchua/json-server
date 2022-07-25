from flask import Flask, request
import time,os,re,subprocess,threading
import pandas as pd
import sqlite3

# create the Flask app
app = Flask(__name__)

def run_shell_command(commandline, h, timeout):
    """
    Run OS command with timeout and status return. Also works in Python 2.7.
    Example:
    output, task_return_code, task_timeouted = run_shell_command('shell command text', timeout)
    """
    print(h)
    output = ""
    task_timeouted = False
    task_return_code = 100
    FNULL = open(os.devnull, 'w')
    try:
        task = subprocess.Popen(commandline.split(), shell=False, stdout=subprocess.PIPE, stderr=FNULL)
    except OSError:
        task_return_code = 101
        return "", task_return_code, task_timeouted

    task_stop_time = time.time() + timeout

    def killer_for_task(task, task_stop_time):
        while task.poll() is None and time.time() < task_stop_time:
            time.sleep(0.1)
        if time.time() > task_stop_time:
            try:
                task.kill()
                try:
                    task.stdout.close()
                except (ValueError, IOError) as e:
                    pass
            except OSError:
                pass

    killer_job = threading.Thread(target=killer_for_task, args=(task, task_stop_time))
    killer_job.start()

    # Wait for subprocess complete. Timeout is controlled by thread killer_job
    try:
        output = task.communicate()[0]

    except ValueError:
        pass

    killer_job.join()
    FNULL.close()

    if time.time() >= task_stop_time:
        task_timeouted = True
    else:
        task_return_code = task.returncode

    try:
        task.stdout.close()
    except ValueError:
        pass

    return output.decode('utf-8'), task_return_code, task_timeouted

def trigger_action(alrt,inst,mntpt):
    df = pd.read_csv("alert_action")
    if mntpt == "":
        select_rows = df.loc[(df['alert'] == alrt)  & ((df['server'] == inst ) | df['server'].isnull())]
    else:
        select_rows = df.loc[(df['alert'] == alrt) & ((df['server'] == inst ) | df['server'].isnull()) & (df['mntpt'] == mntpt)]
    print(select_rows)

def insert_alertdb(alrt,inst,desc,svty,startsat):
    try:
        conn = sqlite3.connect("am_alert.db")
        cursor = conn.cursor()
        sqlite_insert_with_param = """INSERT INTO am_alerts ( name, instance, severity, description, startat) VALUES ( ?, ?, ?, ?, ?);"""
        data_tuple = (alrt, inst, svty, desc,startsat)
        cursor.execute(sqlite_insert_with_param, data_tuple)
        conn.commit()
        conn.close()
    except sqlite3.Error as error:
        print("Failed to insert data")
    finally:
        if conn:
            conn.close()
            print("db closed")

@app.route('/alerttrigger', methods=['POST'])
def alerttrigger():

    request_data = request.get_json()

    for i in range(len(request_data["alerts"])):
       alrt = request_data["alerts"][i]["labels"]["alertname"]
       inst = request_data["alerts"][i]["labels"]["instance"]
       desc = request_data["alerts"][i]["annotations"]["description"]
       svty = request_data["alerts"][i]["labels"]["severity"]
       startsat = request_data["alerts"][i]["startsAt"]
       mntpt = ""
       if alrt == "HostOutOfDiskSpace":
           mntpt = request_data["alerts"][i]["labels"]["mountpoint"]
       insert_alertdb(alrt,inst,desc,svty,startsat)
       trigger_action(alrt,inst,mntpt)


    return ""

if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, port=5001)
