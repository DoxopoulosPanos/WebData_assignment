"""
This script uses subprocess Popen in order to reserve again nodes (by using the reserve_nodes_again.sh)
"""
import os
import subprocess


def run():
    path = os.path.dirname(os.path.abspath(__file__))

    command = "{} {}/{}".format("bash", path, "reserve_nodes_again.sh")
    result = subprocess.check_output(command.split())
    ES_DOMAIN, KB_DOMAIN = result.split()

    return ES_DOMAIN, KB_DOMAIN

