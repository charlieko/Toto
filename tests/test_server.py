import unittest
import urllib2
import json
import os
import signal
from uuid import uuid4
from toto.secret import *
from multiprocessing import Process, active_children
from toto.server import TotoServer
from time import sleep, time

def run_server(processes=1):
  TotoServer(method_module='web_methods', port=9000, debug=True, processes=processes).run()

class TestWeb(unittest.TestCase):
  
  @classmethod
  def setUpClass(cls):
    print 'Starting server'
    cls.service_process = Process(target=run_server, args=[-1])
    cls.service_process.start()
    sleep(0.5)
  
  @classmethod
  def tearDownClass(cls):
    print 'Stopping server'
    processes = [int(l.split()[0]) for l in os.popen('ps').readlines() if 'python' in l and 'unittest' in l]
    for p in processes:
      if p == os.getpid():
        continue
      print 'killing', p
      os.kill(p, signal.SIGKILL)
    sleep(0.5)
  
  def test_method(self):
    request = {}
    request['method'] = 'return_value'
    request['parameters'] = {'arg1': 1, 'arg2': 'hello'}
    headers = {'content-type': 'application/json'}
    req = urllib2.Request('http://127.0.0.1:9000/', json.dumps(request), headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())['result']
    self.assertEqual(request['parameters'], response['parameters'])
  
  def test_method_async(self):
    request = {}
    request['method'] = 'return_value_async'
    request['parameters'] = {'arg1': 1, 'arg2': 'hello'}
    headers = {'content-type': 'application/json'}
    req = urllib2.Request('http://127.0.0.1:9000/', json.dumps(request), headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())['result']
    self.assertEqual(request['parameters'], response['parameters'])
  
  def test_method_task(self):
    request = {}
    request['method'] = 'return_value_task'
    request['parameters'] = {'arg1': 1, 'arg2': 'hello'}
    headers = {'content-type': 'application/json'}
    req = urllib2.Request('http://127.0.0.1:9000/', json.dumps(request), headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())['result']
    self.assertEqual(request['parameters'], response['parameters'])
  
  def test_no_method(self):
    request = {}
    request['parameters'] = {'arg1': 1, 'arg2': 'hello'}
    headers = {'content-type': 'application/json'}
    req = urllib2.Request('http://127.0.0.1:9000/', json.dumps(request), headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())
    self.assertEqual({'error': {'code': 1002, 'value': 'Missing method.'}}, response)
  
  def test_bad_method(self):
    request = {}
    request['method'] = 'bad_method.test'
    request['parameters'] = {'arg1': 1, 'arg2': 'hello'}
    headers = {'content-type': 'application/json'}
    req = urllib2.Request('http://127.0.0.1:9000/', json.dumps(request), headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())
    self.assertEqual({'error': {'code': 1000, 'value': "'module' object has no attribute 'bad_method'"}}, response)
  
  def test_method_form_post(self):
    request = {}
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    req = urllib2.Request('http://127.0.0.1:9000/return_value', 'arg1=1&arg2=hello', headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())['result']
    self.assertEqual(response['parameters']['arg1'][0], '1')
    self.assertEqual(response['parameters']['arg2'][0], 'hello')
  
  def test_method_no_params(self):
    request = {}
    request['method'] = 'return_value'
    headers = {'content-type': 'application/json'}
    req = urllib2.Request('http://127.0.0.1:9000/', json.dumps(request), headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())['result']
    self.assertFalse(response['parameters'])

  def test_url_method(self):
    request = {}
    request['parameters'] = {'arg1': 1, 'arg2': 'hello'}
    headers = {'content-type': 'application/json'}
    req = urllib2.Request('http://127.0.0.1:9000/return_value', json.dumps(request), headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())['result']
    self.assertEqual(request['parameters'], response['parameters'])

  def test_get_method(self):
    request = {}
    request['parameters'] = {'arg1': '1', 'arg2': 'hello'}
    req = urllib2.Request('http://127.0.0.1:9000/return_value?arg1=1&arg2=hello')
    f = urllib2.urlopen(req)
    response = json.loads(f.read())['result']
    self.assertEqual(request['parameters'], response['parameters'])

  def test_batch_method(self):
    batch = {}
    headers = {'content-type': 'application/json'}
    for i in xrange(3):
      rid = uuid4().hex
      request = {}
      request['method'] = 'return_value'
      request['parameters'] = {'arg1': 1, 'arg2': rid}
      batch[rid] = request
    req = urllib2.Request('http://127.0.0.1:9000/', json.dumps({'batch': batch}), headers)
    f = urllib2.urlopen(req)
    batch_response = json.loads(f.read())['batch']
    for rid, response in batch_response.iteritems():
      request['parameters']['arg2'] = rid
      self.assertEqual(request['parameters'], response['result']['parameters'])
    
  def test_get_method(self):
    request = {}
    request['parameters'] = {'arg1': '1', 'arg2': 'hello'}
    req = urllib2.Request('http://127.0.0.1:9000/return_value?arg1=1&arg2=hello')
    f = urllib2.urlopen(req)
    response = json.loads(f.read())['result']
    self.assertEqual(request['parameters'], response['parameters'])
  
  def test_exception(self):
    request = {}
    request['method'] = 'throw_exception'
    request['parameters'] = {'arg1': 1, 'arg2': 'hello'}
    headers = {'content-type': 'application/json'}
    req = urllib2.Request('http://127.0.0.1:9000/', json.dumps(request), headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())
    self.assertEqual({'error': {'code': 1000, 'value': "Test Exception"}}, response)
  
  def test_toto_exception(self):
    request = {}
    request['method'] = 'throw_toto_exception'
    request['parameters'] = {'arg1': 1, 'arg2': 'hello'}
    headers = {'content-type': 'application/json'}
    req = urllib2.Request('http://127.0.0.1:9000/', json.dumps(request), headers)
    f = urllib2.urlopen(req)
    response = json.loads(f.read())
    self.assertEqual({'error': {'code': 4242, 'value': "Test Toto Exception"}}, response)



