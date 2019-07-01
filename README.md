# Django SockSync
Easily bind django model data with a websocket client.

This library was created for and being used in [CryptoPilot](https://github.com/osum4est/cryptopilot), but feel free
to use it in your own projects as well!

It uses channels + redis, so those must be set up as well in order for the library to function.

## Client Libraries
These libraries will handle all the websocket communication for you and make binding to data easier:
* [vue-socksync](https://github.com/osum4est/vue-socksync)

## Setup
Install:
```
pip install django-socksync
```

Modify django settings:
```python
INSTALLED_APPS = [
    'socksync',
    'channels'
]

ASGI_APPLICATION = "routing.application"
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

Create routing.py in the main app module next to urls.py:
```python
from socksync import consumers

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/socksync/', consumers.SockSyncConsumer),
            # You could add your own websocket routes here if you need custom ones
        ])
    )
})
```

Install and start redis:
```
(macOS): brew install redis && brew services start redis
(linux): sudo apt install redis && sudo service redis-server start
```

## Usage

## Protocol Overview
Currently data can only be bound one way: server → client, since this library is mainly intended to be used for keeping
a client updated with information from the server. Data can be sent from the client to the server through the use of
functions.

### Bound Variables
A single variable can be bound and contain anything that json supports.

Client:
```json5
{
  "func": "get",
  "type": "var",
  "name": "..."
}
```

Server:
```json5
{
  "func": "update",
  "type": "var",
  "name": "...",
  "value": "..."
}
```

### Bound Lists
If a list or database table is requested from the server, the server can provide change updates instead of sending 
the whole list each time it updates. This requires each object in the array to have a unique "id" field. Related tables
can be handled by passing the id of related field with each list item and making separate variable/list calls.

Client:
```json5
{
  "func": "get",
  "type": "list",
  "name": "...",
  "id": "..."  // Optional, use if you just want one item in a list. An update func will be returned
}
```

Server:

Send the initial whole list:
```json5
{
  "func": "update_all",
  "type": "list",
  "name": "...",
  "items": [
    {
      "id": "...",
      "value": "..."
    }
  ]
}
```

Add an item:
```json5
{
  "func": "add",
  "type": "list",
  "name": "...",
  "id": "...",
  "value": "..."
}
```

Update an item:
```json5
{
  "func": "update",
  "type": "list",
  "name": "...",
  "id": "...",
  "value": "..."
}
```

Delete an item:
```json5
{
  "func": "delete",
  "type": "list",
  "name": "...",
  "id": "..."
}
```

### Bound Functions
Functions can be used to call a function on the server from the client or vise versa with arguments.

Call a function:
```json5
{
  "func": "call",
  "type": "function",
  "name": "...",
  "args": {
    "...": "..."
  }
}
```

Return from a function:
```json5
{
  "func": "return",
  "type": "function",
  "name": "...",
  "value": "..."
}
```

### Subscriptions
A websocket by default will receive no data updates. A client must first be subscribed to an update group to start
receiving updates. This will happen automatically the first time it requests data by it's name. A group can be
left by using the `unsubscribe` websocket func:

```json5
{
  "func": "unsubscribe",
  "type": "...",             // var or list
  "name": "...",
  "id": "..."                // Optional, use for list item
}
```
Or unsubscribe from all updates:
```json5
{
  "func": "unsubscribe_all"
}
```
You can also subscribe to data without getting it's value:
```json5
{
  "func": "subscribe",
  "type": "...",             // var or list
  "name": "...",
  "id": "..."                // Optional, use for list items
}
```

### Errors
Errors for unknown variables, lists, or functions:
```json5
{
  "func": "error",
  "type": "...",             // var, list, or function
  "name": "...",
  "id": "...",               // Optional, use for list items
  "message": "..."           // Optional, use for more descriptive error messages
}
```

General error for malformed requests or other problems:
```json5
{
  "func": "error",
  "message": "..."
}
```
