# Django SockSync
Easily bind django model data with a websocket client.

This library was created for and being used in [CryptoPilot](https://github.com/osum4est/cryptopilot), but feel free
to use it in your own projects as well!

It uses channels + redis, so those must be set up as well in order for the library to function.

## Client Libraries
These libraries will handle all the websocket communication for you and make binding to data easier:
* [vue-socksync](https://github.com/osum4est/vue-socksync)

## Server Setup
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
from socksync.sockets import SockSyncConsumer

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/socksync/', SockSyncConsumer),
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

## Client Setup

## Usage

## Protocol Overview
Every message must at least include a `func` parameter that tells the other side of the connection what to do. The 
`type` parameter is used to describe what type of data we performing the function on. `name` refers to the name of the
data. By default neither side of the connection receives any sets or function calls from the other side. To receive
these they must be subscribed to. Every function should work on both the client and the server, so data can by synced
bidirectionally. 

**Note**: All requests that attempt to modify data (`set`, `set_all`, `add`, `delete`, and function calls) are ignored 
if the receiver of the request hasn't subscribed to that item. This should be checked on both sides, in the case of a 
nonconforming client. This ensures that data only gets changed if that side allows it to. Keep in mind that this causes 
`get` to only work if that side has first subscribed to that data.

### Variables
A single variable can be bound and contain anything that json supports.

Request a parameter:
```json5
{
  "func": "get",
  "type": "var",
  "name": "..."
}
```

Set the value of a parameter or respond to a `get` request:
```json5
{
  "func": "set",
  "type": "var",
  "name": "...",
  "value": "..."
}
```

### Lists
If a list or database table is requested, a change func can be provided instead of sending the whole list each time it 
changes. This requires each object in the array to have a unique "id" field. Related tables can be handled by passing 
the id of related field with each list item and making separate variable/list calls.

Request a list:
```json5
{
  "func": "get",
  "type": "list",
  "name": "...",
  "id": "..."  // Optional, use if you just want one item in a list. A set func will be returned
}
```

Set the entire list or respond to a `get` request. This should *replace* the existing list:
```json5
{
  "func": "set_all",
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

Change an item:
```json5
{
  "func": "set",
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

### Functions
Functions can be used to call a function on the server from the client or vise versa with arguments. Note that a
function on the server will only be called if the server subscribes to it on all the clients that should have access.
A `return` is required to be sent anytime a side that's been subscribed to sends a `call`.

Call a function:
```json5
{
  "func": "call",
  "type": "function",
  "name": "...",
  "id": "...",               // Should be a unique uuid in order to match up the right return to the call
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
  "id": "...",               // Should match the one provided in the call func
  "value": "..."             // Optional, include if there is data to be returned
}
```

### Subscriptions
A websocket by default will receive no data updates. A side must first be subscribed to an update group to start 
receiving updates:
```json5
{
  "func": "subscribe",
  "type": "...",             // var, list, or function
  "name": "...",
  "id": "..."                // Optional, use for list items
}
```

To leave a group and stop receiving updates:
```json5
{
  "func": "unsubscribe",
  "type": "...",             // var, list, or function
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
