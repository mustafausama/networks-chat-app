import socket
import re
import sys


def is_port_available(hostname, port, udp=False):
    try:
        # Attempt to create a socket and bind to the specified port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) if not udp else socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((hostname, port))
            return True  # Port is available
    except:
        return False  # Port is not available


def find_available_port(hostname, start_port = 0, end_port = 65535, udp=False):
    for port in range(start_port, end_port):
        if is_port_available(hostname, port, udp):
            return port


def sendTCPMessage(tcpClientSocket, message):
    tcpClientSocket.send(message.encode())


def receiveTCPMessage(tcpClientSocket):
    message = tcpClientSocket.recv(1024).decode()
    return message



def get_hostname():
    hostname=socket.gethostname()
    try:
        res = socket.gethostbyname(hostname)
    except socket.gaierror:
        raise ValueError("Hostname %s could not be resolved" % hostname)
    return res


def generate_random_secret():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

class FORMAT:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GREY = '\033[90m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ITALIC = '\033[3m'
    STRIKETHROUGH = '\033[9m'
    END = '\033[0m'
    LIGHT_RED = '\033[91m'

def _frmt(c, text):
    if c == '*':
        return FORMAT.BOLD + text + FORMAT.END
    elif c == '`':
        return FORMAT.ITALIC + text + FORMAT.END
    elif c == '~':
        return FORMAT.STRIKETHROUGH + text + FORMAT.END
    elif c == '_':
        return FORMAT.UNDERLINE + text + FORMAT.END
    else:
        return text

def format_link(text):
    pattern = r'\[([^\]]*)\]\((https?://\S+|www\.\S+)\)'

    def print_clickable_link(url, text):
        if not text:
            text = url
        return FORMAT.BLUE + (f'\033]8;;{url}\033\\{text}\033]8;;\033\\') + FORMAT.END
    replaced_text = re.sub(pattern, lambda match: print_clickable_link(match.group(2), match.group(1)), text)

    return replaced_text


def format_text(text) -> str:
    text = format_link(text)
    stack = []
    specifiers = ['*', '`', '~', '_']
    for i in range(len(text)):
        if text[i] in specifiers:
            if len(stack) == 0 or stack[-1][0] != text[i]:
                stack.append([text[i], ''])
            else:
                stack[-1] = ['', _frmt(text[i], stack[-1][1])]
                while len(stack) > 1 and stack[-1][0] == '':
                    last = stack.pop()
                    stack[-1][1] += last[1]
        else:
            if len(stack) > 0:
                stack[-1][1] += text[i]
            else:
                stack.append(['', text[i]])
    res = ''
    for i in range(len(stack)):
        res += stack[i][0] + stack[i][1]
    return res

def print_colored_text(text, color: str = '', end='\n'):
    if color == 'red':
        print(FORMAT.RED + text + FORMAT.END, end=end)
    elif color == 'green':
        print(FORMAT.GREEN + text + FORMAT.END,end=end)
    elif color == 'yellow':
        print(FORMAT.YELLOW + text + FORMAT.END,end=end)
    elif color == 'blue':
        print(FORMAT.BLUE + text + FORMAT.END,end=end)
    elif color == 'cyan':
        print(FORMAT.CYAN + text + FORMAT.END,end=end)
    elif color == 'purple':
        print(FORMAT.PURPLE + text + FORMAT.END,end=end)
    elif color == 'grey':
        print(FORMAT.GREY + text + FORMAT.END,end=end)
    elif color == 'light_red':
        print(FORMAT.LIGHT_RED + text + FORMAT.END,end=end)
    else:
        print(text, end = end)


def get_input(msg="", color=""):
    if msg: print_colored_text(msg, color, end='')
    return input()

def clear_last_console_line():
    sys.stdout.write('\x1b[1A')  # Move cursor up one line
    sys.stdout.write('\x1b[2K')  # Clear the line

