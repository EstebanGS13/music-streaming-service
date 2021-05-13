import os
import signal
import zmq


SRV_DIR = 'server_files'


def list_files(socket, query):
    files = os.listdir(SRV_DIR)
    if query:
        # Only keep the files that match the query
        files = [file for file in files if query[0].lower() in file.lower()]

    socket.send_json({'files': files})


def save_file(filename, data):
    file = open(f'{SRV_DIR}/{filename}', 'wb')
    file.write(data)
    file.close()
    return f"'{filename}' ha sido subido"


def get_file(filename):
    path = f'{SRV_DIR}/{filename}'
    if os.path.exists(path):
        file = open(path, 'rb')
        data = file.read()
        file.close()
        return data
    else:
        return b''


if __name__ == '__main__':
    if not os.path.exists(SRV_DIR):
        os.makedirs(SRV_DIR)

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:5555')
    print('Server is listening...')

    while True:
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        message = socket.recv_json()
        print(f"Request: {message}")
        command = message['command']
        args = message['args']
        if command == 'search':
            list_files(socket, query=args)
        else:
            reply = ''
            filename = message[1].decode()
            if command == 'up':
                reply = save_file(filename, message[2])
                socket.send_string(reply)
            elif command == 'down':
                reply = get_file(filename)
                socket.send(reply)
            else:
                reply = f'{command} no es un comando válido'
