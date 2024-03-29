# TODO: Make int fields ints

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
these they must be subscribed to. Every subscription works one-way, bidirectional syncing is not supported. Any client
should handle both providing data and subscribing to data (there is no distinction between a 'client' and a 'server').

**Note**: All requests that attempt to modify data (`set`, `set_all`, `add`, `delete`, and function calls) will cause 
an error with code 1 if the receiver of the request hasn't subscribed to that item. This should be checked on both 
sides, in the case of a bad client. This ensures that data only gets changed if that side allows it to. Keep in mind 
that this causes `get` to only work if that side has first subscribed to that data.

**All fields are required unless marked otherwise!**

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
changes.  Lists are ordered and support pagination. A client should allow the user to set a maximum page size for a list 
to prevent too many items being sent. Indexes start at 0 for each page. 

Updates are sent to any client that would expect to see a change to their current page. This means that any change to 
the clients current page should be sent, as well an any change occurring to previous elements (Inserting or deleting an 
item at index 0 would cause all elements in the list to shift to the left or right). Inserts and deletes should be sent 
sequentially in order to keep the client list at the specified page size (deleting an item should cause a new item to be 
inserted at the end if there are more items in the list, and inserting an item should delete the last item in the list 
since it is no longer on that page).

Request a list:
```json5
{
  "func": "get",
  "type": "list",
  "name": "...",
  "page": "...",             // Optional, if not provided the first page will be sent (zero-indexed)
  "page_size": "...",        // Optional, if not provided the owner will use their max page size
}
```

Set the entire list or respond to a `get` request. This should *replace* the existing list:
```json5
{
  "func": "set_all",
  "type": "list",
  "name": "...",
  "page": "...",
  "page_size": "...",
  "total_item_count": "...",
  "items": [
    "..."
  ]
}
```

Set the total item count. This should be sent any time the number of total items change. (If an `insert` or `delete` is 
sent a `set_count` needs to be sent as well):
```json5
{
  "func": "set_count",
  "type": "list",
  "name": "...",
  "total_item_count": "..."
}
```

Insert an item:
```json5
{
  "func": "insert",
  "type": "list",
  "name": "...",
  "index": "...",
  "value": "..."
}
```

Change an item:
```json5
{
  "func": "set",
  "type": "list",
  "name": "...",
  "index": "...",
  "value": "..."
}
```

Delete an item:
```json5
{
  "func": "delete",
  "type": "list",
  "name": "...",
  "index": "..."
}
```

### Functions
Functions can be used to call a function on the server from the client or vise versa with arguments. Note that a
function on the server will only be called if the server subscribes to it on all the clients that should have access.
A `return` or `error` is required to be sent anytime a side that's been subscribed to sends a `call`.

Call a function:
```json5
{
  "func": "call",
  "type": "function",
  "name": "...",
  "id": "...",               // Should be a unique uuid in order to match up the right return to the call
  "args": {                  // Optional, use if needed
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
  "value": "..."             // Optional, use if needed
}
```

### Subscriptions
A websocket by default will receive no data updates. A side must first be subscribed to an update group to start 
receiving updates:
```json5
{
  "func": "subscribe",
  "type": "...",             // var, list, or function
  "name": "..."
}
```

To leave a group and stop receiving updates:
```json5
{
  "func": "unsubscribe",
  "type": "...",             // var, list, or function
  "name": "..."
}
```

Or unsubscribe from all updates:
```json5
{
  "func": "unsubscribe_all"
}
```

### Errors
Errors are sent in order to help the user of a client debug their code. There should be *no* errors in a finished
production environment.

| Error Code | Name          | Description                                                                       |
| ---------- | ------------- | --------------------------------------------------------------------------------- |
| 1          | Invalid func  | The requested func does not exist or is not available for a group.                |
| 2          | Invalid type  | The requested type does not exist.                                                |
| 3          | Invalid name  | The requested name has not been registered.                                       |
| 4          | Missing field | A field that is required for a func is missing.                                   |
| 5          | Bad index     | An index for a list operation is out of bounds.                                   |
| 6          | Bad id        | An id for a function return is invalid.                                           |
| 7          | Invalid json  | The sent json could not be parsed.                                                |
| 8          | Other         | Any other error (recommended to add description in message).                      |

```json5
{
  "func": "error",
  "error_code": "...",
  "message": "..."           // Optional, use for more descriptive error messages
}
```
