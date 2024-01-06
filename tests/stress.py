import unittest
from unittest import TestCase
from unittest.mock import patch

from chat.client.peer_main import PeerMain
from chat.server.server_context import ServerContext

import sys
from io import StringIO

import threading

import numpy as np

def smooth_curve(x, y, degree=50, num_points=500):
    coefficients = np.polyfit(x, y, degree)

    polynomial = np.poly1d(coefficients)

    x_smooth = np.linspace(np.min(x), np.max(x), num_points)

    y_smooth = polynomial(x_smooth)

    return x_smooth, y_smooth

def remove_outliers(data):
    data_sorted = sorted(data)
    n = len(data_sorted)
    Q1 = data_sorted[n // 4] if n % 4 != 0 else (data_sorted[n // 4 - 1] + data_sorted[n // 4]) / 2
    Q3 = data_sorted[3 * n // 4] if n % 4 != 0 else (data_sorted[3 * n // 4 - 1] + data_sorted[3 * n // 4]) / 2
    
    IQR = Q3 - Q1

    lower_bound = Q1 - IQR
    upper_bound = Q3 + IQR
    filtered_data = [x for x in data if lower_bound <= x <= upper_bound]

    return filtered_data

class StressTest(TestCase):
    @patch('chat.client.peer_main.inputRegAddress')
    @patch('chat.client.peer_main.inputPassword')
    @patch('builtins.input')
    def test_all(self, mock_input, mock_inputPassword, mock_inputRegAddress):
        testing = {'log': ""}
        registry = ServerContext()
        threading.Thread(target=registry.mainLoop, args=(testing,)).start()
        side_effect = []
        pass_side_effect = []
        regAddress_side_effect = []
        TIMES = 100
        while testing.get('host', '') == "": pass
        for i in range(TIMES):
            regAddress_side_effect.append((testing['host'], testing['tcp_port']))
            regAddress_side_effect.append((testing['host'], testing['udp_port']))
            side_effect.append('1')
            side_effect.append('user'+str(i))
            pass_side_effect.append('password'+str(i))
            side_effect.append('2')
            side_effect.append('user'+str(i))
            pass_side_effect.append('password'+str(i))
            side_effect.append('CANCEL')
        mock_input.side_effect = side_effect
        mock_inputPassword.side_effect = pass_side_effect
        mock_inputRegAddress.side_effect = regAddress_side_effect
        import time
        time.sleep(3)
        conn_times = []
        total_times = []
        for i in range(TIMES):
            self.held, sys.stdout = sys.stdout, StringIO()
            start_time = time.time()
            peerMain = PeerMain()
            while testing.get('log', '') == "": pass
            connection_end_time = time.time()
            del testing['log']
            thread = threading.Thread(target=peerMain.mainLoop)
            thread.start()
            thread.join()
            end_time = time.time()
            conn_times.append(connection_end_time - start_time)
            total_times.append(end_time - start_time)
            sys.stdout = self.held
            if i > 0:
                print("\033[F\033[K", end='')
            print(f"Process {i+1}/{TIMES} finished.")
        newLen = TIMES - (TIMES//10)
        y1 = remove_outliers(conn_times[TIMES//10:])
        y2 = remove_outliers(total_times[TIMES//10:])
        _, y1 = smooth_curve(range(newLen), conn_times[TIMES//10:], num_points=newLen)
        _, y2 = smooth_curve(range(newLen), total_times[TIMES//10:], num_points=newLen)
        try:
            import matplotlib.pyplot as plt
            plt.plot(y1, label="Connection time")
            plt.plot(y2, label="Total time")
            plt.legend()
            plt.figure()

            plt.plot(y1, label="Connection time")
            plt.title('Connection time (without database access)')
            plt.figure()

            plt.plot(y2, label="Total time", color='orange')
            plt.title("Total time (with database access read/write)")
            plt.show()
        except:
            pass

        try:
            import psutil
            p = psutil.Process(testing['registryPID'])
            p.terminate()
        except:
            import os
            os.kill(os.getpid(), 9)
            
if __name__ == "__main__":
    unittest.main()    
