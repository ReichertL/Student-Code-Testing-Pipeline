import os
import shutil
import subprocess

class Playground:
    name: str
      

    def __init__(self):
        self.name = "Playground"
        self.dirname="/tmp/similarity"


    def functionality(self,):
        print("Debug env to test new functionality which can be implemented, called or composed here")

        try:
            shutil.rmtree(self.dirname)
        except:
            pass
        ok.mkdir(self.dirname)
        students=stud.get_students_passed()
        for student in students:
            submissions=sub.get_passed_for_name(student.name)
            last=submissions[0]
            src=last.submission_path
            dest=f"{self.dirname}/{(student.name).replace(" ","_")}"
            shutil.copy(src,dest)
            command=f"cd ..& java -jar jplag-2.12.1-SNAPSHOT-jar-with-dependencies.jar -l c/c++ -vd  -s {self.dirname}"
            subprocess.run(command,shell=True)
            logging.info(f"Results written to {os.getcwd()}/../results")

                


    def run(self,):
        self.functionality()

        


















