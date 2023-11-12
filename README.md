## The chat application

### Implementation of the chat application logic using socket interfaces. 

### The log

- 12.11.2023 - simple chat version with bugs: when the client terminates the connection with `Ctrl + C` -> the app crashes + not tested dropping of the connection using commands
- 12.11.2023 - tested `exit` and `quit` commands towards the connection and chat

### To do 
- implement error handling on connection termination from the client side
- refactor the app following the DDD pattern