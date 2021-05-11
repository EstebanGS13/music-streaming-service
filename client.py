import logging
import os
import queue
import signal
import simpleaudio
import threading
import time
import zmq


SONGS_DIR = 'songs'
BUF_SIZE = 10
q = queue.Queue(BUF_SIZE)
# logging.basicConfig(level=logging.DEBUG, format='(%(threadName)-9s) %(message)s')


class ClientThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(ClientThread, self).__init__()
        self.target = target
        self.name = name
        self.socket = None
        self.playback_instruction = {}
        self.commands_list = ['play', 'stop', 'pause', 'resume', 'next']

    def connect(self, ip):
        """Connect the client to the server using its ip address"""
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(f'tcp://{ip}:5555')

    def search(self, command):
        """List the files stored in the server"""
        self.socket.send_multipart([command.encode()])
        reply = self.socket.recv_json()
        if 'files' in reply:
            print(*reply['files'], sep='\n')
        else:
            print('No hay archivos en el servidor')

    def download(self, filename):
        """Download a song, if it isn't already downloaded"""
        # Checar si ya existe en songs
        if os.path.exists(f"{SONGS_DIR}/{filename}"):
            print(f"'{filename}' ya se descargó")
            return True

        # Descargar la cancion del srv
        self.socket.send_multipart([b'down', filename.encode()])
        data = self.socket.recv()
        if data:
            file = open(f'{SONGS_DIR}/{filename}', 'wb')
            file.write(data)
            file.close()
            print(f"'{filename}' ha sido descargada")
            return True
        else:
            print(f"'{filename}' no se encontró en el servidor")
            return False

    def put_instruction(self, command, filename=None):
        self.playback_instruction['command'] = command
        self.playback_instruction['filename'] = filename
        q.put(self.playback_instruction)

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
                elif command in self.commands_list:
                    # Poner instrucción en la cola
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


class PlaybackThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(PlaybackThread, self).__init__()
        self.target = target
        self.name = name
        self.playlist = []
        self.song_index = None
        self.song_name = None
        self.current_song = None
        self.stopped = False
        self.paused = False
        return

    def add(self, filename):
        self.playlist.append(filename)
        print(f"'{filename}' agregada a la lista")

    def play_all(self):
        for index, filename in enumerate(self.playlist):
            wave_obj = simpleaudio.WaveObject.from_wave_file(
                f"{SONGS_DIR}/{filename}")
            self.song_index = index
            self.song_name = filename
            self.current_song = wave_obj.play()
            self.current_song.wait_done()

    def play_next(self):
        if self.current_song:
            simpleaudio.stop_all()

    def pause_song(self):
        if not self.current_song:
            print("No song is currently playing")
            return

        if self.paused:
            print(f"'{self.song_name}' is already paused")
            return

        self.current_song.pause()
        self.paused = True

    def resume_song(self):
        if self.paused:
            self.current_song.resume()
            self.paused = False

    def run(self):
        while True:
            if not q.empty():
                instruction = q.get()
                command = instruction['command']
                if command == 'add':
                    filename = instruction['filename']
                    self.add(filename)
                elif command == 'play':
                    playlist_thread = threading.Thread(target=self.play_all)
                    playlist_thread.start()
                elif command == 'next':
                    self.play_next()
                elif command == 'stop':
                    simpleaudio.stop_all()
                elif command == 'pause':
                    self.pause_song()
                elif command == 'resume':
                    self.resume_song()

        return


def main():
    client = ClientThread(name='client')
    playback = PlaybackThread(name='playback')

    client.connect("localhost")

    # Agregar canciones descargadas previamente a la cola
    for filename in os.listdir(SONGS_DIR):
        playback.add(filename)

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    client.start()
    time.sleep(1)
    playback.start()
    time.sleep(1)


if __name__ == '__main__':
    main()
