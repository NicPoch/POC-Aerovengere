import os
from multiprocessing import Process

def startUpdate():
    os.system('python3 updateDataTask.py')
def startStreamlit():
    os.system('streamlit run stEE.py')

if __name__=="__main__":
    p=Process(target=startUpdate)
    p.start()
    startStreamlit()
    p.join()