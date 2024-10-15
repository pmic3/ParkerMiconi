import subprocess

#Run the program
def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

#Create arguments for run_command
run = "sss_run"
run_returncode, run_stdout, run_stderr = run_command(run)

#Print output
if run_returncode == 0:
    print("Command executed successfully")
    print(run_stdout.decode())
else:
    print("Failed to execute command")
    print(run_stderr.decode())