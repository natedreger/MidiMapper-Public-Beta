# mp1.py

from multiprocessing import Process,Pipe

def f(child_conn):
    msg = input("Enter username:")
    child_conn.send(msg)
    child_conn.close()
