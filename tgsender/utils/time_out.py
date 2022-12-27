"""
Adapt from:
https://stackoverflow.com/a/14924210
https://stackoverflow.com/a/10415215

"""
import multiprocessing


def func_subprocess(func_, dict_params):

    func_(**dict_params)


def time_out(sec_time_out, func_, dict_params={}, restart=False):
    """Terminate the process if the runtime exceeds the defined time

    Args:
        sec_time_out (int or float): Maximum run time in seconds
        func_ (function): function to be performed
        dict_params (dict, optional): function parameters. Defaults to {}.
        restart (bool, optional): Restart the process if it is terminated by time_out. Defaults to False.

    Returns:
        type undefined: func_ return
    """

    # Starts process
    p = multiprocessing.Process(
        target=func_subprocess, args=[func_, dict_params]
    )
    p.start()

    # Wait for defined time  or until process finishes
    p.join(sec_time_out)

    # If thread is still active
    if p.is_alive():

        # Terminate - may not work if process is stuck for good
        # p.terminate()
        # OR Kill - will work for sure, no chance for process to finish nicely however
        p.kill()

        p.join()
        if restart:
            time_out(sec_time_out, func_, dict_params, restart)
        else:
            pass
