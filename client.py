import logging
import os
import queue
import shlex
import signal
import simpleaudio
import threading
import time
import zmq


SONGS_DIR = 'songs/'
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
        self.playback_commands = [
            'play', 'stop', 'pause', 'resume', 'next', 'skip', 'prev'
        ]

    def run(self):
        while True:
            # shlex is used to also split quoted inputs
            user_input = shlex.split(input("> "))
            try:
                command = user_input[0].lower()
                args = user_input[1:]

                if command in self.playback_commands:
                    # Put the full command in the queue
                    self.put_instruction(command, args)

                elif command == 'search':
                    self.search(command, args)

                elif command == 'add':
                    if not args:
                        raise ValueError

                    # List cantaining the available songs
                    new_args = self.download(args)
                    # Put instruction to add the songs to the playlist
                    self.put_instruction(command, new_args)

                elif command == 'del':
                    if not args:
                        raise ValueError
                    self.delete(args)
                    self.put_instruction(command, args)

                else:
                    print(f"Command '{command}' not supported")

            except IndexError:
                print("error: Enter a valid command")
            except ValueError:
                print("error: Provide the name of the songs\n"
                      f"usage: {command} 'song1' 'song2' ...")

    def connect(self, ip):
        """Connects the client to the server using its ip address."""
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(f'tcp://{ip}:5555')

    def search(self, command, args):    # TODO add -l flag:locally
        """Lists all the files stored in the server, if no query is given."""
        self.socket.send_json({'command': command, 'args': args})
        reply = self.socket.recv_json()
        if reply['files']:
            print(*reply['files'], sep='\n')
        else:
            print(f"No files containing {args} were found in the server")

    def download(self, args):
        """Returns a list containing all the available songs, which are the
        ones that were successfully downloaded or are already downloaded."""
        new_args = []
        for filename in args:
            # First check if it's already downloaded
            if os.path.exists(f"{SONGS_DIR}{filename}"):
                new_args.append(filename)
                print(f"'{filename}' already downloaded")
                continue

            # Download the song from the server
            self.socket.send_json({'command': 'down', 'args': filename})
            data = self.socket.recv()
            if data:
                file = open(f'{SONGS_DIR}{filename}', 'wb')
                file.write(data)
                file.close()
                new_args.append(filename)
                print(f"'{filename}' downloaded")
            else:
                print(f"'{filename}' not found or it's empty")

        return new_args

    def delete(self, args):
        """Deletes all the songs listed in args."""
        for filename in args:
            try:
                os.remove(f"{SONGS_DIR}{filename}")
                print(f"'{filename}' deleted")
            except OSError:
                print(f"Can't delete '{filename}', not found")

    def put_instruction(self, command, args):
        """Puts an instruction in the queue,
        which has a command and a list of args."""
        playback_instruction = {'command': command, 'args': args}
        q.put(playback_instruction)


class PlaybackThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
        super(PlaybackThread, self).__init__()
        self.target = target
        self.name = name
        self.playlist = []
        self.temp_playlist = []
        self.playlist_thread = None
        self.thread_running = False
        self.index = 0
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
                args = instruction['args']

                if command == 'add':
                    self.add(args)

                elif command == 'play':
                    if self.paused:
                        self.resume_song()  # Using play to unpause a song
                        continue

                    self.play()  # todo add args

                elif command == 'stop':
                    self.stop()
                elif command == 'pause':
                    self.pause_song()
                elif command == 'resume':
                    self.resume_song()
                elif command == 'prev':
                    self.switch_song(-1)
                elif command in ('next', 'skip'):
                    self.switch_song(1)
                elif command == 'del':
                    self.remove(args)

    def add(self, args):
        """Adds the songs listed in args to the playlist."""
        for filename in args:
            self.playlist.append(filename)
            print(f"'{filename}' added to playlist")

    def play(self):
        """Handles the playback logic."""
        if self.thread_running:
            return

        self.playlist_thread = threading.Thread(target=self.play_all, args=())
        self.stopped = False
        self.thread_running = True
        self.playlist_thread.start()

    def play_all(self):
        # if args:
        #     self.temp_playlist = [
        #         file for file in args if os.path.exists(f"{SONGS_DIR}{file}")
        #     ]
        #     for filename in self.temp_playlist:
        #         if self.stopped:
        #             break
        #         self.play_song(filename)

        # else:
        # Plays all the songs in playlist starting from index
        for filename in self.playlist[self.index:]:
            if self.stopped:
                break
            self.play_song(filename)

        self.thread_running = False

    def play_song(self, filename):
        try:
            wave_obj = simpleaudio.WaveObject.from_wave_file(
                f"{SONGS_DIR}{filename}")
            self.song_name = filename
            self.current_song = wave_obj.play()
            self.current_song.wait_done()
            if not self.stopped:
                # Only increment index when a song stops playing on its own
                self.index += 1
        except FileNotFoundError:
            print(f"Can't play '{filename}', not found")
            self.remove_song(filename)
        finally:
            self.song_name = self.current_song = None

    def stop(self, reset=True):
        """Stops whichever song is currently playing."""
        if not self.current_song:
            print("No song is currently playing")
            return

        # This prevents a paused song from not being stopped
        # (allowing the playlist_thread to terminate)
        self.resume_song()
        self.stopped = True
        simpleaudio.stop_all()
        self.paused = False

        # If playback is stopped by user
        if reset:
            self.index = 0

    def pause_song(self):
        """Pauses the song that's currently playing."""
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
            self.paused = False
            self.current_song.resume()

    def switch_song(self, amount):
        """Switches to the next or to the previous song."""
        if not self.current_song:
            print("Play a playlist first")
            return

        if not self.valid_index(amount):
            print(f"index no valido! {self.index + amount}")
            return

        self.stop(reset=False)  # Stop and don't reset the index
        self.playlist_thread.join()  # Wait until playlist_thread finishes
        self.index += amount
        self.play()

    def valid_index(self, amount):
        """Checks whether the next (or pervious) index is valid or not."""
        return True if 0 <= self.index + amount < len(self.playlist) else False

    def remove(self, args):
        """Removes all the songs in args from the playlist."""
        for filename in args:
            self.remove_song(filename)

    def remove_song(self, filename):
        """Removes only a song from the playlist."""
        try:
            self.playlist.remove(filename)
            print(f"'{filename}' removed from the playlist")
        except ValueError:
            print(f"'{filename}' not in playlist")


def main():
    client = ClientThread(name='client')
    playback = PlaybackThread(name='playback')

    client.connect("localhost")

    # Agregar canciones descargadas previamente a la cola
    playback.add(os.listdir(SONGS_DIR))

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    client.start()
    time.sleep(1)
    playback.start()
    time.sleep(1)


if __name__ == '__main__':
    main()
