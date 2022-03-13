# Networks

In UDP, the client does not form a connection with the server like in TCP and instead just sends a datagram. Similarly, the server need not accept a connection and just waits for datagrams to arrive. Datagrams upon arrival contain the address of sender which the server uses to send data to the correct client.

Basic working of UDP Socket

1. The server starts and waits for filename.
2. The client sends a filename.
3. The server receives filename.
   If file is present,
   server starts reading file 
   and continues to send a buffer filled with
   file contents encrypted until file-end is reached.
4. End is marked by EOF.
5. File is received as buffers until EOF is 
received. Then it is decrypted.
6. If Not present, a file not found is sent.
