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
        self.playback_commands = ['play', 'stop', 'pause', 'resume', 'next']

    def run(self):
        while True:
            user_input = input("> ").split()
            try:
                command = user_input[0]
                args = user_input[1:]

                if command == 'search':
                    self.search(command)

                elif command in self.playback_commands:
                    self.put_instruction(command)
                    # Put the full command in the queue

                elif command == 'add':
                    if not args:
                        raise ValueError

                    # List cantaining the available songs
                    new_args = self.download(args)
                    # Put instruction to add the name of the songs to the queue
                    self.put_instruction(command, new_args)

                elif command == 'del':
                    pass

                else:
                    print(f"Command {command} not supported")

            except IndexError:
                print("Escribe 'up' o 'down' y luego el nombre del archivo")
            except ValueError:
                print("error: Provide the name of the songs\n"
                      f"usage: {command} 'song1' 'song2' ...")

    def connect(self, ip):
        """Connects the client to the server using its ip address"""
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(f'tcp://{ip}:5555')

        """List the files stored in the server"""
        self.socket.send_multipart([command.encode()])
        reply = self.socket.recv_json()
        if 'files' in reply:
            print(*reply['files'], sep='\n')
        else:
            print('No hay archivos en el servidor')

    def download(self, args):
        """Returns a list containing all the available songs, which are the
        ones that were successfully downloaded or are already downloaded"""
        new_args = []
        for filename in args:
            # First check if it's already downloaded
            if os.path.exists(f"{SONGS_DIR}/{filename}"):
                new_args.append(filename)
                print(f"'{filename}' ya se descargó")
                continue

            # Download the song from the server
            self.socket.send_multipart([b'down', filename.encode()])
            data = self.socket.recv()
            if data:
                file = open(f'{SONGS_DIR}/{filename}', 'wb')
                file.write(data)
                file.close()
                new_args.append(filename)
                print(f"'{filename}' downloaded")
            else:
                print(f"'{filename}' not found")

        return new_args

    def delete(self, args):
        """Deletes the songs listed in args"""


    def put_instruction(self, command, args):
        """Puts an instruction in the queue,
        which has a command and a list of args"""
        playback_instruction = {'command': command, 'args': args}
        q.put(playback_instruction)


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

    def add(self, filename):
        """Adds a song name to the playlist"""
        self.playlist.append(filename)
        print(f"'{filename}' added to playlist")

    def play_all(self):
        for index, filename in enumerate(self.playlist):
            wave_obj = simpleaudio.WaveObject.from_wave_file(
                f"{SONGS_DIR}/{filename}")
            self.song_index = index
            self.song_name = filename
            self.current_song = wave_obj.play()
            print(wave_obj, self.current_song)
            self.current_song.wait_done()

    def play_next(self):
        if self.current_song:
            simpleaudio.stop_all()

    def pause_song(self):
        """Pause the song that's currently playing"""
        if not self.current_song:
            print("No song is currently playing")
            return

        if self.paused:
            # TODO se puede obviar
            print(f"'{self.song_name}' is already paused")
            return

        self.current_song.pause()
        self.paused = True

    def resume_song(self):
        if self.paused:
            self.current_song.resume()
            self.paused = False


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
