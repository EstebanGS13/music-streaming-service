import logging
import os
import queue
import threading
import time
import zmq

from pydub import AudioSegment
from pydub.playback import play


# logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s')
# l = logging.getLogger("pydub.converter")
# l.setLevel(logging.CRITICAL)
# l.addHandler(logging.StreamHandler())

FOLDER = 'songs'
BUF_SIZE = 10
q = queue.Queue(BUF_SIZE)


class ClientThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(ClientThread, self).__init__()
        self.target = target
        self.name = name
        self.socket = None
        self.player_instruction = {}

    def connect(self, ip):
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(f'tcp://{ip}:5555')

    def search(self, command):
        self.socket.send_multipart([command.encode()])
        reply = self.socket.recv_json()
        if reply['files']:
            print(*reply['files'], sep='\n')
        else:
            print('No hay archivos en el servidor')

    def download(self, filename):
        # Checar si ya existe en songs
        if os.path.exists(f"{FOLDER}/{filename}"):
            print(f"'{filename}' ya se descargó")
            return True
        
        # Descargar la cancion del srv
        self.socket.send_multipart([b'down', filename.encode()])
        data = self.socket.recv()
        if data:
            file = open(f'{FOLDER}/{filename}', 'wb')
            file.write(data)
            file.close()
            print(f"'{filename}' ha sido descargada")
            return True
        else:
            print(f"'{filename}' no se encontró en el servidor")
            return False
    
    def put_instruction(self, command, filename=None):
        self.player_instruction['command'] = command
        self.player_instruction['filename'] = filename 
        q.put(self.player_instruction)
    
    def run(self):
        while True:
            user_input = input("> ")
            # if user_input == 'exit':
            #     break
            try:
                user_input = user_input.split()
                command = user_input[0]
                if command == 'search':
                    self.search(command)
                elif command == 'play':
                    # Poner instrucción para reproducir la lista
                    self.put_instruction(command)
                else:
                    filename = user_input[1]
                    if command == 'add':
                        # Si se descargó o ya está descargada
                        if self.download(filename):
                            # Poner instrucción de agregar filename a la cola
                            self.put_instruction(command, filename)
                    else:
                        print("Escribe 'up' o 'down' y luego el nombre del archivo")
            except:
                print("Escribe 'up' o 'down' y luego el nombre del archivo")
        
        return


class PlayerThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(PlayerThread, self).__init__()
        self.target = target
        self.name = name
        self.playlist = [] # TODO llenarla PRIMERO-----------
        self.current_song = None
        return

    def run(self):
        while True:
            if not q.empty():
                instruction = q.get()
                command = instruction['command']
                if command == 'add':
                    filename = instruction['filename']
                    self.add(filename)
                elif command == 'play':
                    sound = AudioSegment.from_mp3(f"{FOLDER}/{filename}")
                    play(sound)
                    
        return

    def add(self, filename):
        # if filename not in self.playlist:
        self.playlist.append(filename)
        # logging.debug('Getting ' + str(item))
        

if __name__ == '__main__':

    client = ClientThread(name='client')
    player = PlayerThread(name='player')

    client.connect("localhost")
    client.start()

    time.sleep(2)
    player.start()
    time.sleep(2)
