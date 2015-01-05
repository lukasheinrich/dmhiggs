from flask import Flask, render_template, request, jsonify, send_from_directory

from socketio.namespace import BaseNamespace
from socketio import socketio_manage
from celery.result import BaseAsyncResult

import backendtasks
import uuid
import os
import sqlite3
import models

app = Flask(__name__)
db = sqlite3.connect('database.db')

app.debug = True

import redis

import IPython
import time
import sqlite3

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


#
# ajax routes to be called asynchronously
#
@app.route("/upload",methods=['POST','GET'])
def upload():
  #rudimentary.. better: http://flask.pocoo.org/docs/0.10/patterns/fileuploads/#uploading-files
  mode = request.form.get('mode',None)

  uvmodel = models.Model.create('UVModel','some UV model defined by the files being uploaded')
  db.execute('''INSERT INTO models VALUES (?,?,?)''',(str(uvmodel.modelId),uvmodel.name,uvmodel.description))
  db.commit()
  
  sel = db.execute('''select * from analyses where name = 'HiggsPlusMet' ''').fetchall()
  
  assert len(sel)==1
  analysisId = sel[0][0]

  req = models.BasicRequest.create('lheinric',analysisId,uvmodel.modelId)

  uploaddir = 'uploads/{}'.format(req.requestId)
  os.makedirs(uploaddir)

  for f in request.files.itervalues(): f.save('{}/{}'.format(uploaddir,f.filename))


  db.execute('''INSERT INTO basicRequests VALUES (?,?,?,?,?)''',(req.requestor,req.lhefileglob,str(req.requestId),str(req.analysisId),str(req.modelId)))
  db.commit()

  return jsonify(requestId=req.requestId)

from celery import chain

@app.route('/process/<requestId>')
def process(requestId):
  print "processing requestId: {}".format(requestId)

  jobguid = uuid.uuid1()
  print "assigning jobguid: {}".format(jobguid)

  asyncres = (backendtasks.prepare_workdir.s(requestId,jobguid) | 
              backendtasks.pythia.s() | 
              backendtasks.rivet.s() |
              backendtasks.postresults.s(requestId)).apply_async()

  return jsonify(jobguid=jobguid)


#
# these are the views  
#
@app.route("/")
def home():
    return render_template('home.html')

@app.route("/newrequest")
def uploadform():
    return render_template('upload.html')

@app.route('/monitor/<jobguid>')
def monitorview(jobguid):
  return render_template('monitor.html', jobguid=jobguid)

@app.route('/request/<requestId>')
def requestview(requestId):
  sel = db.execute('''select * from basicRequests where requestId = :id ''',{'id':requestId}).fetchall()
  assert len(sel) == 1
  data = dict(zip(['requestor','fileglob','requestId','analysisId','modelId'],sel[0]))
  return render_template('request.html', requestData=data)

@app.route('/result/<requestId>')
def resultview(requestId):
  return render_template('result.html', requestId=requestId)

@app.route('/requests')
def allrequestsview():
  allrows = db.execute('''select * from basicRequests''').fetchall()
  colnames = ['requestor','fileglob','requestId','analysisId','modelId']
  data = [dict(zip(colnames,row)) for row in allrows]
  return render_template('requests.html', requestsData=data)


#
# API routes
#
@app.route('/efficiency/<requestId>')
def efficiency(requestId):
  result =  backendtasks.fiducialeff(requestId)
  return jsonify(efficiency=result)

@app.route('/status/<requestId>')
def status(requestId):
  resultdir = 'results/{}'.format(requestId)
  available = os.path.exists(resultdir)
  return jsonify(resultsAvailable=available)

#
# helper routes
#

@app.route('/plots/<resultId>/<path:file>')
def plots(resultId,file):
  resultdir = 'results/{}/plots/DMHiggsFiducial'.format(resultId)
  return send_from_directory(resultdir,file)

@app.route('/socket.io/<path:remaining>')
def socketio(remaining):
    # print request.environ
    socketio_manage(request.environ, {
        '/monitor': MonitoringNamespace
    })
    return app.response_class()

from socketio.server import SocketIOServer, serve

if __name__ == "__main__":
  serve(app, port = 8000, host = '0.0.0.0')
