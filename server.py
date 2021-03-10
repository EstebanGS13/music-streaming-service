import os
import zmq


FOLDER = 'server_files'


def list_files(socket):
    files = os.listdir(FOLDER)
    socket.send_json({'files': files})


def save_file(filename, data):
    file = open(f'{FOLDER}/{filename}', 'wb')
    file.write(data)
    file.close()
    return f"'{filename}' ha sido subido"


def get_file(filename):
    path = f'{FOLDER}/{filename}'
    if os.path.exists(path):
        file = open(path, 'rb')
        data = file.read()
        file.close()
        return data
    else:
        return b''


if __name__ == '__main__':
    if not os.path.exists(FOLDER):
        os.makedirs(FOLDER)
    
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:5555')
    print('Server is listening...')

    while True:
        message = socket.recv_multipart()
        command = message[0].decode()
        if command == 'search':
            list_files(socket)
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
            
