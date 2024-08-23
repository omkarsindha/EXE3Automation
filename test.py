import paramiko
import time

# SSH connection details
hostname = '172.16.199.39'
username = 'root'
password = 'evertz'

# Create SSH client
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # Connect to the remote server
    ssh.connect(hostname, username=username, password=password)
    channel = ssh.invoke_shell(width=1000, height=1000)
    print("Running command")
    channel.send("stress-ng --vm 8 --vm-bytes 80% -t 1m" + "\n")
    while channel.exit_status_ready() is False:
        print("not yet")
        time.sleep(0.1)
    print("Command finished")
    # Above commmand takes a random time to complete ranging from 2 to 5 minutes how to know if it as finished running or not
    channel.send("ls -s /sys/devices/system/edac/mc/mc0" + "\n")
    result = ""
    while channel.exit_status_ready() is False:
        time.sleep(0.1)
    if channel.recv_ready() is True:
        result += channel.recv(4096).decode("utf-8")
    channel.close()
    print(result)

finally:
    # Close the SSH connection
    ssh.close()