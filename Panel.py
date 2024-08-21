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
        top_ssh = paramiko.SSHClient()
        top_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        bottom_ssh = paramiko.SSHClient()
        bottom_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            top_ssh.connect(ip1, port=port, username="root", password="evertz", timeout=3)
            bottom_ssh.connect(ip2, port=port, username="root", password="evertz", timeout=3)
        except (paramiko.SSHException, IOError) as err:
            wx.MessageBox("Unable to SSH %s" % (str(err)), 'Error', wx.OK | wx.ICON_ERROR)
            self.on_stop()
            return

        # Testing EXE
        for c in self.config.CMDs:
            if not self.inProgress:
                top_ssh.close()
                bottom_ssh.close()
                return
            parts = c.split()
            cmd = ' '.join(parts[1:])
            if parts[0] == "TOP-FC":
                if cmd.split()[0] == "SCREEN-CMD":
                    cm = ' '.join(cmd.split()[1:])
                    result = self.execute_screen_command(top_ssh, cm)
                else:
                    result = self.execute_command(top_ssh, cmd)
            elif parts[0] == "BOTTOM-FC":
                if cmd.split()[0] == "SCREEN-CMD":
                    cm = ' '.join(cmd.split()[1:])
                    result = self.execute_screen_command(top_ssh, cm)
                else:
                    result = self.execute_command(bottom_ssh, cmd)

            self.print_filter_result(parts[0], result, cmd)
            time.sleep(delay)

        result = self.run_commands(top_ssh, ["screen -x sc", "z", "99", "6", "1", "", ""])
        self.print_filter_result("TOP-FC", result, "x sc")
        time.sleep(delay)
        result = self.run_commands(top_ssh, ["screen -x sc", "z", "99", "6", "5", ""])
        self.print_filter_result("TOP-FC", result, "x sc")
        time.sleep(delay)
        result = self.run_commands(top_ssh, ["screen -x sc", "z", "99", "6", "6", ""])
        self.print_filter_result("TOP-FC", result, "x sc")
        time.sleep(delay)
        result = self.run_commands(top_ssh, ["screen -x sc", "z", "99", "6", "8", ""])
        self.print_filter_result("TOP-FC", result, "x sc")
        time.sleep(delay)
        result = self.run_commands(top_ssh, ["screen -x sc", "z", "99", "9", "2", ""])
        self.print_filter_result("TOP-FC", result, "x sc")
        top_ssh.close()
        bottom_ssh.close()
        self.on_stop()

    def run_commands(self, ssh, commands):
        chan = ssh.invoke_shell(width=1000, height=1000)
        for cmd in commands:
            chan.send(cmd + "\n")
            time.sleep(0.5)
            if cmd != "":
                while chan.recv_ready():
                    chan.recv(1000)
        time.sleep(2)
        timeout = 5  # Timeout in seconds
        start_time = time.time()
        result = ""
        print("hi")
        while True:
            if chan.recv_ready():
                result += chan.recv(1000).decode("utf-8")
                start_time = time.time()
            else:
                time.sleep(0.1)
                if time.time() - start_time > timeout:
                    break
        print("bye")
        chan.close()
        return result

    def execute_command(self, ssh, cmd):
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

    def execute_screen_command(self, ssh, cmd):
        split_cmd = cmd.split("$")
        parts = [p.strip() for p in split_cmd]
        screen = parts[0]
        chan = ssh.invoke_shell()
        result = ""
        chan.send(screen + '\n')
        time.sleep(1)
        for item in parts[1:]:
            chan.send(item + '\n')
            time.sleep(2)
            result += chan.recv(4096).decode("utf-8")
            result += '\n'
        chan.send('\x01')  # Ctrl+A
        chan.send('d')
        chan.close()
        return result

    def print_filter_result(self, fc: str, result: str, cmd):
        lines = result.split('\r\n')
        filtered_lines = [line for line in lines if line.strip() and '\r\r' not in line]
        filtered_result = '\n'.join(filtered_lines)
        self.parent.output.append(f"{cmd}'s output {fc}\n\n{filtered_result}\n\n\n")
        print(f"{cmd}'s output {fc}\n" + filtered_result)
        print("-----------------------------------------------------------------------\n\n")

    def OnTimer(self, event):
        """Called periodically while the flooder threads are running."""
        self.animation_counter += 1
        self.parent.SetStatusText(f"In progress{'.' * (self.animation_counter % 10)}")
