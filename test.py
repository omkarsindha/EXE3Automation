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

    # Create an interactive shell session
    channel = ssh.invoke_shell()

    # Enter screen session
    channel.send('x fu' + '\n')
    time.sleep(2)  # Wait for screen session to start

    # Run command inside screen session
    channel.send('show port all' + '\n')
    output = ""
    time.sleep(4)
    output += channel.recv(4096).decode("utf-8")
    print(output)

    # Exit screen session (Ctrl+A, then D)
    channel.send('\x01')  # Ctrl+A
    channel.send('d')     # D
    time.sleep(1)

    # Run netstat
    channel.send('forallx uptime')
    output = ""
    time.sleep(1)
    output += channel.recv(4096).decode("utf-8")
    print('\n\n\n'+output)

finally:
    # Close the SSH connection
    ssh.close()