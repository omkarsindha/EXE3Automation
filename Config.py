class Config:
    def __init__(self):
        self.CMDs = []  #
        self.load_config()  # Loads values from config.txt

    def load_config(self):
        isCmds: bool = False

        with open("config.txt", "r") as file:
            for line in file:
                l = line.strip()
                # Checking if the line is a comment or not
                if "//" in l:
                    continue

                if "END_CMDS" == l:
                    isCmds = False
                    continue

                if isCmds:
                    self.CMDs.append(line.strip())

                if "CMDS" == l:
                    isCmds = True


if __name__ == "__main__":
    config_instance = Config()
    print(config_instance.CMDs)


