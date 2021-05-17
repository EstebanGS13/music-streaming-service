import logging
import os
import pathlib
import signal
import zmq


logging.basicConfig(level=logging.INFO,
                    format='(Server) %(levelname)s: %(message)s')

SRV_DIR = 'server_files/'


def list_files(directory, query):
    files = os.listdir(directory)
    if query:
        # Only keep the files that match the query
        files = [file for file in files if query[0].lower() in file.lower()]

    return files


def save_file(filename, data):
    file = open(f'{SRV_DIR}{filename}', 'wb')
    file.write(data)
    file.close()
    return f"'{filename}' ha sido subido"


def get_file(directory, filename):
    path = f'{directory}{filename}'
    if os.path.exists(path):
        file = open(path, 'rb')
        data = file.read()
        file.close()
        return data
    else:
        return b''


def main():
    pathlib.Path(SRV_DIR).mkdir(exist_ok=True)

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:5555')
    logging.info('Server is listening...')

    while True:
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        message = socket.recv_json()
        logging.info(f"Request = {message}")
        command = message['command']
        args = message['args']

        if command == 'search':
            reply = list_files(SRV_DIR, query=args)
            socket.send_json({'files': reply})

        elif command == 'down':
            reply = get_file(SRV_DIR, filename=args)
            socket.send(reply)

        else:
            logging.warning(f"Command '{command}' not supported")


if __name__ == '__main__':
    main()
