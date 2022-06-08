#!/home/admin/flask_app/bin/python3
# import main Flask class and request object
from flask import Flask, request
import time,os,re,subprocess,threading
import configparser

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



@app.route('/alerttrigger', methods=['POST'])
def alerttrigger():
    config = configparser.ConfigParser()
    config.read('test.conf')
    sections = config.sections()

    request_data = request.get_json()
    for i in range(len(request_data["alerts"])):
       a = request_data["alerts"][i]["labels"]["alertname"]
       ii = request_data["alerts"][i]["labels"]["instance"]
       desc = request_data["alerts"][i]["annotations"]["description"]
       print("alertname: ",a)
       print("hostname: ",ii)
       print("description: ", desc)
       if a == "HostOutOfDiskSpace":
           o = request_data["alerts"][i]["labels"]["mountpoint"]
           print("option: ", o)

       print("-----------------------------")
       if a == "HostOutOfDiskSpace":
           for section in sections:
               n = config[section]['node']
               if n == "ANY" or  n == ii:
                   if config[section]["alert"] == a:
                       if config[section]["action"] == "exec_remote":
                           exec_cmd = config[section]["option"]
                           print("echo  " +  section + " " + a + " " + exec_cmd + " " + o + " " +  ii)
                       if config[section]["action"] == "forward_email":
                           print("echo  formward_email" + " " + desc)

       if a == "HostHighCpuLoad":
           for section in sections:
               n = config[section]['node']
               if n == "ANY" or n == ii:
                   if config[section]["alert"] == a:
                       if config[section]["action"] == "exec_remote":
                           exec_cmd = config[section]["option"]
                           print("echo  " + section + " " + a + " " + exec_cmd + " " +  ii)
                       if config[section]["action"] == "forward_email":
                           print("echo  formward_email" + " " + desc)

       if a == "HostOutOfMemory":
           for section in sections:
               n = config[section]['node']
               if n == "ANY" or  node == ii:
                   if config[section]["alert"] == a:
                       if config[section]["action"] == "exec_remote":
                           exec_cmd = config[section]["option"]
                           print("echo  " + section + " " + a + " " + exec_cmd + " " + ii)
                       if config[section]["action"] == "forward_email":
                           print("echo  formward_email" + " " + desc)


    return ""

if __name__ == '__main__':
    # run app in debug mode on port 5000
    app.run(debug=True, port=5001)
