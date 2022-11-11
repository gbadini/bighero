import psutil

for proc in psutil.process_iter():
    #print(proc.name())
    if any(procstr in proc.name() for procstr in\
                ['chromedriver']):
                print(f'Killing {proc.name()}')
                proc.kill()

