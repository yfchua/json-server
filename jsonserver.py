# import main Flask class and request object
from flask import Flask, request
import time,os,re,subprocess,threading

# create the Flask app
app = Flask(__name__)

def run_shell_command(commandline, timeout):
    """
    Run OS command with timeout and status return. Also works in Python 2.7.
    Example:
    output, task_return_code, task_timeouted = run_shell_command('shell command text', timeout)
    """
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



@app.route('/alerttrigger', methods=['POST'])
def alerttrigger():
    request_data = request.get_json()
    for i in range(len(request_data["alerts"])):
       a = request_data["alerts"][i]["labels"]["alertname"]
       ii = request_data["alerts"][i]["labels"]["instance"]
       print("alertname: ",a)
       print("hostname: ",ii)
       if a == "HostOutOfDiskSpace":
           o = request_data["alerts"][i]["labels"]["mountpoint"]
           print("option: ", o)

       print("-----------------------------")
       if a == "HostOutOfDiskSpace":
           r = run_shell_command("/opt/alertmon/python/bin/flask/bin/alert_trigger.sh " + a + " disk " + o , 60)
       if a == "HighCPU":
           r = run_shell_command("/opt/alertmon/python/bin/flask/bin/alert_trigger.sh " + a + " cpu" , 60)
       if a == "HighMEM":
           r = run_shell_command("/opt/alertmon/python/bin/flask/bin/alert_trigger.sh " + a + " mem" , 60)

    return ""

if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, port=5000)
