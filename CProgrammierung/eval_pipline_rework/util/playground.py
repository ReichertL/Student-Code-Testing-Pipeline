class Playground:
    name: str

    def __init__(self):
        self.name = "Playground"

    @staticmethod
    def functionality():
        print("Debug env to test new functionality which can be implemented, called or composed here")

    def run(self):
        self.functionality()
