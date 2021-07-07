import os
from multiprocessing import Process

def startUpdate():
    os.system('python3 updateDataTask.py')
def startAPI():
    os.system('python3 restAPI.py')

if __name__=="__main__":
    p=Process(target=startUpdate)
    p.start()
    startAPI()
    p.join()