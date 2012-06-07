import cPickle as pickle
from threading import Thread
from collections import deque
from tornado.web import *
from tornado.ioloop import IOLoop
from zqm.eventloop.ioloop import ZQMPoller
from traceback import format_exc
from tornado.options import options
import zmq
import logging
import zlib

_server_sockets = []

def add_socket(address):
  _server_sockets.append(address)

class EventManager():

  def __init__(self, address):
    self.__handlers = {}
    self.address = address
    self.__zmq_context = zmq.Context()
    self.__socket = self.__zmq_context.socket(zmq.PULL)
    self.__socket.bind(address)
    self.__remote_servers = {}
    self.__thread = None
  
  def register_server(self, address):
    if address in self.__remote_servers:
      raise Exception('Server already registered: %s', address)
    socket = self.__zmq_context.socket(zmq.PUSH)
    socket.connect(address)
    self.__remote_servers[address] = socket

  def remove_server(self, address):
    del self.__remote_servers[address]
    
  def remove_all_servers(self):
    self.__remote_servers.clear()

  def remove_handler(self, handler_sig):
    self.__handlers[handler_sig[0]].discard(handler_sig[1])
  
  def register_handler(self, event_name, event_handler, run_on_main_loop=False, request_handler=None, persist=False):
    if not event_name in self.__handlers:
      self.__handlers[event_name] = set()
    handler_tuple = (event_handler, run_on_main_loop, request_handler, persist)
    self.__handlers[event_name].add(handler_tuple)
    return (event_name, handler_tuple)

  def receive(self, event):
    event_name = event['name']
    event_args = event['args']
    if event_name in self.__handlers:
      handlers = self.__handlers[event_name]
      persistent_handlers = set()
      while handlers:
        handler = handlers.pop()
        if handler[2] and handler[2]._finished:
          continue
        if handler[1]:
          handler[0](event_args)
        else:
          IOLoop.instance().add_callback(lambda: handler[0](event_args))
        if handler[3]:
          persistent_handlers.add(handler)
      handlers |= persistent_handlers
  
  def send_to_server(self, address, event_name, event_args):
    event = {'name': event_name, 'args': event_args}
    event_data = zlib.compress(pickle.dumps(event))
    self.__remote_servers[address].send(event_data)
  
  def send(self, event_name, event_args, broadcast=False):
    event = {'name': event_name, 'args': event_args}
    event_data = zlib.compress(pickle.dumps(event))
    for route in _server_routes:
      if route == _local_route:
        self.receive(event)
      else:
        try:
          urlopen(Request(route, event_data, {'x-toto-event-key': _private_event_key}))
        except Exception as e:
          logging.error("Bad event route: %s - %s", route, options.debug and format_exc() or e)

  def start(self):
    def run():
      while(True):
        self.receive(pickle.loads(zlib.decompress(self.__socket.recv())))
        
    self.thread = threading.Thread()

  @staticmethod
  def instance():
    if not hasattr(EventManager, "_instance"):
      EventManager._instance = EventManager(options.address)
    return EventManager._instance
      
