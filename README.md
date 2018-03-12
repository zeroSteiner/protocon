# protocon
Protocon is a socket-centric framework for rapidly prototyping connections
through simple send and receive commands. Think socat with pretty hex output
and more send / receive automation control.

[![asciicast](https://asciinema.org/a/153917.png)][1]

## Installing
Protocon requires Python 3.4+ and can be installed via pip using the command
`python3 -m pip install protocon`.

## Example Usage
### Manual Mode
Starting Protocon requires a `target_url` argument which describes the type of
socket to open and the endpoint to connect to. Protocon will then switch to an
interactive console where various commands are available to send and receive
data.

```
user@localhost:~$ ./protocon tcp://github.com:22
[*] Loaded 4 connection drivers
[+] Initialized protocon engine v1.0 at 2017-12-22 08:13:09
[+] Connected to: tcp://github.com:22
pro > # this is a comment
pro > # next we're going to receive all the data we can read in 1 second
pro > recv_time 1
[*] RX:     22 bytes (CRC: 0xd533)
0000  53 53 48 2d 32 2e 30 2d  6c 69 62 73 73 68 5f 30   SSH-2.0-libssh_0
0010  2e 37 2e 30 0d 0a                                  .7.0..          
pro > exit
```

### Trans(script) Mode
When starting Protocon, one or more resource files containing commands can be
specified and will be executed in sequence.

```
user@localhost:~$ ./protocon udp://8.8.8.8:53 examples/dns_query.txt       
[*] Loaded 4 connection drivers
[+] Initialized protocon engine v1.0 at 2017-12-22 08:26:28
[+] Connected to: udp://8.8.8.8:53
encoding - was: utf-8
now: hex
[*] TX:     55 bytes (CRC: 0xa139)
0000  37 49 01 20 00 01 00 00  00 00 00 01 03 77 77 77   7I. .........www
0010  06 67 6f 6f 67 6c 65 03  63 6f 6d 00 00 01 00 01   .google.com.....
0020  00 00 29 10 00 00 00 00  00 00 0c 00 0a 00 08 4e   ..)............N
0030  c1 3b 36 79 86 a5 d5                               .;6y...         
[*] RX:     59 bytes (CRC: 0x5210)
0000  37 49 81 80 00 01 00 01  00 00 00 01 03 77 77 77   7I...........www
0010  06 67 6f 6f 67 6c 65 03  63 6f 6d 00 00 01 00 01   .google.com.....
0020  c0 0c 00 01 00 01 00 00  00 57 00 04 ac d9 06 e4   .........W......
0030  00 00 29 02 00 00 00 00  00 00 00                  ..)........     
[*] The connection has been closed
```

For more examples of resource files, see the [examples directory][2].

## Data Expansion
Data passed by the user (such as the parameter to the `send` and
`recv_until` commands) will be expanded using a basic escape sequence.
Additionally these sequences can be escaped by being prefixed with `\`.

| Sequence | Description          |
|----------|----------------------|
| `\\`     | Literal backslash    |
| `\n`     | New line             |
| `\r`     | Carrige return       |
| `\t`     | Tab                  |
| `\x00`   | Literal byte `0x00`  |
| `${var}` | Variable named `var` |

### Variables
The expansion supports variables inserted with `${var}`. The following
variables are defined automatically.

| Variable Name  | Description                     |
|----------------|---------------------------------|
| `url.host`     | The host portion of the URL     |
| `url.password` | The password portion of the URL |
| `url.port`     | The port portion of the URL     |
| `url.scheme`   | The scheme portion of the URL   |
| `url.username` | The username portion of the URL |

## Credits
  - Spencer McIntyre - zeroSteiner ([\@zeroSteiner][3])

[1]: https://asciinema.org/a/153917
[2]: https://github.com/zeroSteiner/protocon/tree/master/examples
[3]: https://twitter.com/zeroSteiner
