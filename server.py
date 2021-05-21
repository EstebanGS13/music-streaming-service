import logging
import os
import pathlib
import signal
import zmq


logging.basicConfig(level=logging.DEBUG,
                    format='(Server) %(levelname)s: %(message)s')

SRV_DIR = 'server_files/'
CHUNK_SIZE = 1024 * 1024 * 10  # 10 MB


def list_files(query, directory=SRV_DIR):
    files = os.listdir(directory)
    if query:
        # Only keep the files that match the query
        files = [file for file in files if query[0].lower() in file.lower()]

    return files


def send_file(socket, filename, directory=SRV_DIR):
    path = f'{directory}{filename}'
    if os.path.exists(path):
        logging.debug(f"Sending '{filename}'...")
        with open(path, 'rb') as file:
            # Read chunks while not empty
            while data := file.read(CHUNK_SIZE):
                socket.send(data)
                if socket.recv_string() != 'ok':
                    break
            else:
                logging.debug(f"'{filename}' sent")

    socket.send(b'')  # Sent when not found or as the last reply


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
            reply = list_files(query=args)
            socket.send_json({'files': reply})

        elif command == 'down':
            send_file(socket, filename=args)

        else:
            logging.warning(f"Command '{command}' not supported")


if __name__ == '__main__':
    main()
