from flask import Flask, render_template, request, jsonify, send_from_directory

from socketio.namespace import BaseNamespace
from socketio import socketio_manage
from celery.result import BaseAsyncResult

import backendtasks
import uuid
import os

app = Flask(__name__)

app.debug = True

import redis

import IPython
import time
import gevent
from gevent import monkey; monkey.patch_all()

import msgpack

class MonitoringNamespace(BaseNamespace):
  def subscriber(self):
    print "subscribing with id: {}".format(id)
    red = redis.StrictRedis(host = 'localhost', db = 0)
    self.emit('pubsubmsg','subscribing to pubsub')
    pubsub = red.pubsub()
    pubsub.subscribe('socket.io#emitter')
    for m in pubsub.listen():
      print m
      if m['type'] == 'message':
        data =  msgpack.loads(m['data'])[0]
        if(data['nsp'] == '/monitor'):
          print "emitting {}".format(data['data'])
          self.emit(*data['data'])

  def on_subscribe(self,msg):
    self.spawn(self.subscriber)

@app.route("/")
def uploadform():
    return render_template('upload.html')

@app.route("/upload",methods=['POST','GET'])
def upload():
  #rudimentary.. better: http://flask.pocoo.org/docs/0.10/patterns/fileuploads/#uploading-files
  mode = request.form.get('mode',None)
  guid = uuid.uuid1()
  uploaddir = 'uploads/{}'.format(guid)
  os.makedirs(uploaddir)

  for f in request.files.itervalues(): f.save('{}/{}'.format(uploaddir,f.filename))
  return jsonify(fileguid=guid)

from celery import chain

@app.route('/process/<fileguid>')
def process(fileguid):
  print "processing file guid: {}".format(fileguid)
  jobguid = uuid.uuid1()
  print "assigning jobguid: {}".format(fileguid)

  asyncres = (backendtasks.prepare_workdir.s(fileguid,jobguid) | backendtasks.pythia.s() | backendtasks.rivet.s()).apply_async()
  return jsonify(jobguid=jobguid)

@app.route('/efficiency/<jobguid>')
def efficiency(jobguid):
  result =  backendtasks.fiducialeff(jobguid)
  return jsonify(efficiency=result)

@app.route('/plots/<jobguid>/<path:file>')
def plots(jobguid,file):
  workdir = 'workdirs/{}/plots/DMHiggsFiducial'.format(jobguid)
  print workdir
  return send_from_directory(workdir,file)

  
@app.route('/monitor/<jobguid>')
def monitor(jobguid):
  return render_template('monitor.html', jobguid=jobguid)


@app.route('/', defaults={'remaining': ''})
@app.route('/<path:remaining>')
def socketio(remaining):
    # print request.environ
    socketio_manage(request.environ, {
        '/monitor': MonitoringNamespace
    })
    return app.response_class()  

from socketio.server import SocketIOServer

if __name__ == "__main__":
  server = SocketIOServer(('0.0.0.0', 5000), app, resource="socket.io")
  server.serve_forever()
