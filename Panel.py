import time
import paramiko
import threading
import wx
from Config import Config


class Panel(wx.Panel):
    def __init__(self, parent, wxconfig):
        wx.Panel.__init__(self, parent)
        self.wxconfig = wxconfig
        self.config = Config()

        self.parent = parent

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        self.inProgress = False
        self.top_ssh = None
        self.bottom_ssh = None

        self.animation_counter: int = 0

        top_box = wx.StaticBox(self, label='Test Configuration')
        top_box.SetFont(wx.Font(wx.FontInfo(12).Bold()))
        top_box_sizer = wx.StaticBoxSizer(top_box)

        ip1_box = wx.StaticBox(self, label="Top FC IP")
        ip1_box_sizer = wx.StaticBoxSizer(ip1_box)
        self.ip1 = wx.TextCtrl(self, value=self.wxconfig.Read('/exeIP1', defaultVal=""))
        ip1_box_sizer.Add(self.ip1, 0, wx.EXPAND | wx.ALL, 5)

        ip2_box = wx.StaticBox(self, label="Bottom FC IP")
        ip2_box_sizer = wx.StaticBoxSizer(ip2_box)
        self.ip2 = wx.TextCtrl(self, value=self.wxconfig.Read('/exeIP2', defaultVal=""))
        ip2_box_sizer.Add(self.ip2, 0, wx.EXPAND | wx.ALL, 5)

        port_box = wx.StaticBox(self, label="Port")
        port_box_sizer = wx.StaticBoxSizer(port_box)
        self.port = wx.TextCtrl(self, size=(60, -1), value=self.wxconfig.Read('/exePort', defaultVal=""))
        port_box_sizer.Add(self.port, 0, wx.EXPAND | wx.ALL, 5)

        delay_box = wx.StaticBox(self, label="Delay")
        delay_box_sizer = wx.StaticBoxSizer(delay_box)
        self.delay = wx.TextCtrl(self, size=(30, -1), value=self.wxconfig.Read('/exeDelay', defaultVal=""))
        delay_box_sizer.Add(self.delay, 0, wx.EXPAND | wx.ALL, 5)
        delay_box_sizer.Add(wx.StaticText(self, label="Seconds"), 0, wx.EXPAND | wx.ALL, 5)

        self.start = wx.Button(self, label="Start")
        self.start.Bind(wx.EVT_BUTTON, self.on_start)

        self.stop = wx.Button(self, label="Stop")
        self.stop.Disable()
        self.stop.Bind(wx.EVT_BUTTON, self.on_stop)

        grid = wx.GridBagSizer()
        grid.Add(ip1_box_sizer, pos=(0, 0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        grid.Add(ip2_box_sizer, pos=(0, 1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        grid.Add(port_box_sizer, pos=(1, 0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        grid.Add(delay_box_sizer, pos=(1, 1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        grid.Add(self.start, pos=(0, 2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        grid.Add(self.stop, pos=(1, 2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)

        top_box_sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 5)

        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.VSCROLL | wx.EXPAND)
        # Populating the text box with the commands from file
        self.text.WriteText("Commands\n\n")
        for cmd in self.config.CMDs:
            self.text.WriteText(cmd + "\n\n")

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(top_box_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        box.Add(self.text, 1, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(box)

    def on_start(self, event):
        try:
            delay = float(self.delay.GetValue())
        except Exception as e:
            wx.MessageBox("Delay should be a number", 'Error', wx.OK | wx.ICON_ERROR)
            return
        self.timer.Start(200)

        self.stop.Enable()
        self.start.Disable()
        self.inProgress = True
        self.parent.output = []
        ip1 = self.ip1.GetValue()
        ip2 = self.ip2.GetValue()
        port = self.port.GetValue()
        thread = threading.Thread(target=self.execute_ssh_cmds, args=(ip1, ip2, port, delay))
        thread.start()

        self.wxconfig.Write("/exeIP1", ip1)
        self.wxconfig.Write("/exeIP2", ip2)
        self.wxconfig.Write("/exePort", port)
        self.wxconfig.Write("/exeDelay", str(delay))

    def on_stop(self, event=None):
        self.start.Enable()
        self.stop.Disable()
        self.inProgress = False

        if self.timer.IsRunning():
            self.timer.Stop()
        self.parent.SetStatusText("Complete :-)")

    def execute_ssh_cmds(self, ip1, ip2, port, delay):
        self.top_ssh = paramiko.SSHClient()
        self.top_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.bottom_ssh = paramiko.SSHClient()
        self.bottom_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.top_ssh.connect(ip1, port=port, username="root", password="evertz", timeout=3)
            self.bottom_ssh.connect(ip2, port=port, username="root", password="evertz", timeout=3)
        except (paramiko.SSHException, IOError) as err:
            wx.MessageBox("Unable to SSH %s" % (str(err)), 'Error', wx.OK | wx.ICON_ERROR)
            self.on_stop()
            return

        commands = []  # List of [[FC,[CMD1, CMD2]], [FC, [CMD1, CMD2, CMD3]]] where FC denotes where to run the command

        for c in self.config.CMDs:
            parts = c.strip().split('-->')
            if len(parts) > 1:
                fc = parts[0].strip()
                cmds = []
                for cmd in parts[1:]:
                    if cmd.strip() == "<BLANK>":  # If its <BLANK> simulate pressing enter without any input
                        cmds.append("")
                    else:
                        cmds.append(cmd.strip())
                commands.append([fc, cmds])

        for c in commands:
            if not self.inProgress:
                self.HandleClose()
                return
            if c[0] == "TOP-FC":    # Checking the FC where the command needs to be executed on
                result = self.run_commands(self.top_ssh, c[1])
                self.print_filter_result(c[0], result, c[1])
            elif c[0] == "BOTTOM-FC":
                result = self.run_commands(self.bottom_ssh, c[1])
                self.print_filter_result(c[0], result, c[1])
            time.sleep(delay)

        if not self.inProgress:
            self.HandleClose()
            return

        # Running stress test separately as the above loop cannot tell when the command has finished execution
        print("Running Stress test on TOP FC please wait 2 minutes")
        self.execute_command(self.top_ssh, "stress-ng --vm 8 --vm-bytes 80% -t 2m")
        result = self.execute_command(self.top_ssh, "ls -s /sys/devices/system/edac/mc/mc0")
        self.print_filter_result("TOP-FC", result, "Stress Command")
        time.sleep(delay)

        if not self.inProgress:
            self.HandleClose()
            return

        print("Running Stress test on Bottom FC please wait 2 minutes")
        self.execute_command(self.bottom_ssh, "stress-ng --vm 8 --vm-bytes 80% -t 2m")
        result = self.execute_command(self.bottom_ssh, "ls -s /sys/devices/system/edac/mc/mc0")
        self.print_filter_result("Bottom-FC", result, "Stress Command")
        time.sleep(delay)

        self.on_stop()

    def run_commands(self, ssh, commands):
        """Method used to execute a chain of commands (Cannot tell when the command has finished execution)"""
        chan = ssh.invoke_shell(width=1000, height=1000)      # Interactive shell same as putty
        for index, cmd in enumerate(commands):
            chan.send(cmd + "\n")       # \n to denote pressing of enter
            time.sleep(0.5)
            if index != len(commands) - 1:
                while chan.recv_ready():
                    chan.recv(1000)
        timeout = 3
        start_time = time.time()
        result = ""
        # Loop takes output from terminal until it has passed a certain time without any output
        while True:
            if chan.recv_ready():
                result += chan.recv(1000).decode("utf-8")
                start_time = time.time()
            else:
                time.sleep(0.1)
                if time.time() - start_time > timeout:
                    break
        chan.close()
        return result

    def execute_command(self, ssh, cmd):
        """Method used to execute standalone commands (Can tell when the command has finished execution)"""
        chan = ssh.get_transport().open_session()
        chan.get_pty()
        chan.exec_command(cmd)
        result = ""
        while chan.exit_status_ready() is False:
            time.sleep(0.1)
        if chan.recv_ready() is True:
            result += chan.recv(4096).decode("utf-8")
        chan.close()
        return result

    def print_filter_result(self, fc: str, result: str, cmd):
        """Filters the result of the command and prints it in a nice human-readable format.
        It also stores it in the output list to later save it as a text file"""
        lines = result.split('\r\n')
        filtered_lines = [line for line in lines if line.strip() and '\r\r' not in line]
        filtered_result = '\n'.join(filtered_lines)
        self.parent.output.append(f"{cmd}'s output (Ran on {fc})\n\n{filtered_result}\n\n\n")
        print(f"{cmd}'s output (Ran on {fc})\n" + filtered_result)
        print("-----------------------------------------------------------------------\n\n")

    def OnTimer(self, event):
        """Called periodically while the flooder threads are running."""
        self.animation_counter += 1
        self.parent.SetStatusText(f"In progress{'.' * (self.animation_counter % 10)}")

    def HandleClose(self):
        """Closes the SSH Objects"""
        if self.top_ssh:
            self.top_ssh.close()
            self.top_ssh = None
        if self.bottom_ssh:
            self.bottom_ssh.close()
            self.bottom_ssh = None
