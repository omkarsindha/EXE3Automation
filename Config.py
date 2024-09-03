class Config:
    def __init__(self):
        self.CMDs = []      # List to store the data from file
        self.load_config()  # Loads values from config.txt

    def load_config(self):
        """Method to read the config from the file and store it into a list for the program"""
        with open("config.txt", "r") as file:
            for line in file:
                line = line.strip()

                if "//" in line:  # Checking if the line is a comment or not
                    continue

                if line != "":   # Checking if the line is blank or not
                    self.CMDs.append(line)


if __name__ == "__main__":
    config_instance = Config()
    print(config_instance.CMDs)
