import subprocess
import threading
import socket


p = subprocess.Popen(["ocaml"], stderr=subprocess.PIPE,shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
exit = False

def read_stdout():
    while not exit:
        msg = p.stdout.readline()
        print("stdout: ", msg.decode())


def read_stderro():
    while not exit:
        msg = p.stderr.readline()
        print("stderr: ", msg.decode())
        exit = True

readout = threading.Thread(target=read_stdout)
readout.start()

readerr = threading.Thread(target=read_stderro)
readerr.start()


while not exit:
    res = input(">")
    p.stdin.write((res + '\n').encode())
    p.stdin.flush()

exit = True
readout.join()
readerr.join()


    # with subprocess.Popen(script, stdin=PIPE, stdout=f, stderr=f) as fproc:
    #     fproc.stdin.write(b"1+1;;\n")

    #     print(f.read())
    #     print("---------------")
    #     ##fproc.stdin.write(bytes(input("# "), 'utf-8')+b"\n")
    #     #f.seek(0)
    #     #print(f.read())
    #     #print("---------------")
    #     fproc.communicate(b"1+3;;\n")

  
