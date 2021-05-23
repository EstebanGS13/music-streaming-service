# Music streaming service

A simple project to transfer files between a server and a client, resembling a music streaming service. A user can play the songs stored in the server (which downloads them) or play songs that are stored locally. The main focus for this project was to use concurrency and client-server communication.

## Installation

1. Install [Python](https://www.python.org) 3.8+.
2. In Ubuntu run the command `sudo apt-get install libasound2-dev`. For Windows, you may need to install Microsoft Visual C++ Build Tools.
3. Install the requirements. It is recommended to first create a [virtual environment](https://docs.python.org/3/library/venv.html).

    ```sh
    pip install -r requirements.txt
    ```

## Usage

Run the server first:

```text
$ py server.py
(Server) INFO: Server is listening ...
```

Then the client:

```text
$ py client.py
(MainThread) INFO: Playlist: ['Coral.wav', 'Fushiguro.wav', 'Solitude.wav']
>
```

The client script gets the commands from the user. These commands are described below, the arguments inside brackets are optional. `>` represents the prompt for user input.

- `search [query]` lists all server files, or the files that match the query.

  ```text
  > search ma
  Magic.wav
  Makani.wav
  ```

- `ls` lists the local files (from `songs/`).

  ```text
  > ls
  Coral.wav
  Fushiguro.wav
  Solitude.wav
  ```

- `play [filename ...]` plays the list of songs. Will play the main playlist made of all the songs from `songs/` if no arguments are passed.

  ```text
  > play Coral.wav Solitude.wav "What If.wav"
  ```

- `stop` stops all audio playback.
- `pause` pauses the current song.
- `resume` resumes the paused song.
- `prev` plays the previous song.
- `next` or `skip` plays the next song.

- `add filename [filename ...]` adds a song (or list of songs) to the main playlist. Use quotes to pass names with spaces.

  ```text
  > add Makani.wav "Hollow Sun.wav"
  (Player) INFO: Playlist: ['Coral.wav', 'Fushiguro.wav', 'Solitude.wav', 'What If.wav', 'Makani.wav', 'Hollow Sun.wav']
  ```

- `del filename [filename ...]` deletes a song (or list of songs) from `songs/`. Also removes them from the main playlist.

  ```text
  > del Fushiguro.wav "What If.wav"
  (Player) INFO: Playlist: ['Coral.wav', 'Solitude.wav', 'Makani.wav', 'Hollow Sun.wav']
  ```

- `rm filename [filename ...]` removes a song (or list of songs) from the main playlist.

  ```text
  > rm Coral.wav "Hollow Sun.wav"
  (Player) INFO: Playlist: ['Solitude.wav', 'Makani.wav']
  ```

- `info` prints the playlist.

  ```text
  > info
  (Player) INFO: Playlist: ['Solitude.wav', 'Makani.wav']
  ```

- `exit` or `CTRL+C` exits the `client.py` execution.

## Licenses

The source code uses the MIT license, while the songs fall under the Creative Commons license.

### Creative Commons Attribution 3.0 Unported

The following songs use the [Creative Commons Attribution 3.0 Unported License](https://creativecommons.org/licenses/by/3.0/deed.en_US).

- Coral by LiQWYD | <https://www.liqwydmusic.com>
- Dreamers by Nettson | <https://soundcloud.com/nettson>
- Hollow Sun by Punch Deck | <https://soundcloud.com/punch-deck>
- Let Go by LiQWYD | <https://www.liqwydmusic.com>
- Makani by Scandinavianz & AXM | <https://soundcloud.com/scandinavianz>
- What If by Jay Someday | <https://soundcloud.com/jaysomeday>

### Creative Commons Attribution-ShareAlike 3.0 Unported

These songs use the [Creative Commons Attribution-ShareAlike 3.0 Unported](https://creativecommons.org/licenses/by-sa/3.0/deed.en_US).

- Fushiguro by Deoxys Beats | <https://soundcloud.com/deoxysbeats1>
- Solitude by Purrple Cat | <https://purrplecat.com>

### Attribution 4.0 International (CC BY 4.0)

This song uses the [Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

- Magic by Savfk | <https://www.youtube.com/savfkmusic>

_Music promoted by <https://www.free-stock-music.com>_
