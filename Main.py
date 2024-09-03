import os
import sys
import threading
import wx
import wx.adv
from Panel import Panel


class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)
        menubar = wx.MenuBar()
        helpMenu = wx.Menu()
        saveMenu = wx.Menu()
        editMenu = wx.Menu()
        helpMenu.Append(wx.ID_ABOUT, "&About")
        menubar.Append(helpMenu, "&Help")
        editMenu.Append(wx.ID_FILE1, "Edit Config")
        menubar.Append(editMenu, "&Edit")
        saveMenu.Append(wx.ID_FILE2, "Save")
        menubar.Append(saveMenu, "&Save")

        self.Bind(wx.EVT_MENU, self.on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_edit_config, id=wx.ID_FILE1)
        self.Bind(wx.EVT_MENU, self.save_as_text, id=wx.ID_FILE2)
        self.SetMenuBar(menubar)

        self.CreateStatusBar(number=2, style=wx.STB_DEFAULT_STYLE)
        self.SetStatusWidths([-1, 100])
        self.SetStatusText("Setup the test", 0)

        self.wxconfig = wx.Config("exe")
        self.output = []
        self.panel = Panel(self, wxconfig=self.wxconfig)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.SetTitle("EXE 3 Sign Off Automation")
        self.SetSize((500, 500))
        self.Centre()

    def OnClose(self, event: wx.CloseEvent):
        """User wants to close the application. Forward to app_panel."""
        # Skip event by default, so it propagates the closing the application.
        event.Skip()
        self.panel.inProgress = False
        self.panel.HandleClose()

    def on_about(self, event):
        info = wx.adv.AboutDialogInfo()
        info.SetName('EXE SSH Automation')
        info.SetDescription(
            "Python version %s.%s.%s (%s %s)\n" % tuple(sys.version_info) +
            "Powered by wxPython %s\n" % (wx.version()) +
            "Running on %s\n\n" % (wx.GetOsDescription()) +
            "Process ID = %s\n" % (os.getpid()))
        info.SetWebSite("www.evertz.com", "Evertz")
        info.AddDeveloper("Omkarsinh Sindha")
        wx.adv.AboutBox(info)

    def on_edit_config(self, event):
        """Opens notepad to edit the configuration file"""
        file_path = "config.txt"
        text_editor_command = "notepad"

        def run_code():
            os.system(f"{text_editor_command} {file_path}")

        edit_thread = threading.Thread(target=run_code)
        edit_thread.start()

    def save_as_text(self, event):
        open_path = os.getcwd()
        WILDCARDS = "Text files (*.txt)|*.txt"
        fileDialog = wx.FileDialog(self,
                                   message="Save as Text File",
                                   wildcard=WILDCARDS,
                                   defaultDir=open_path,
                                   style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if fileDialog.ShowModal() == wx.ID_CANCEL:
            return
        save_filename = fileDialog.GetPath()
        fileDialog.Destroy()
        try:
            with open(save_filename, 'w') as file:
                for line in self.output:
                    file.write(line)
        except IOError as e:
            print(f"Error saving lines to file: {e}")


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None)
        frame.Show(True)
        return True


if __name__ == "__main__":
    app = MyApp()
    app.MainLoop()
