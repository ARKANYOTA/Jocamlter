# launch 3 threads
import logging
import subprocess

import ray as ray

ray.init()

# Logging
logging.basicConfig(filename='../debug.log', encoding='utf-8', level=logging.DEBUG)

# Keyboard Only


@ray.remote
def ocaml_out():
    # msg = p.stdout.readline()
    print("oo")

@ray.remote
def ocaml_err():
    # msg = p.stderr.readline()
    print("bb")


if __name__ == '__main__':
    p = subprocess.Popen(["ocaml"], stderr=subprocess.PIPE, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    ray.get([ocaml_out.remote(), ocaml_err.remote()])

