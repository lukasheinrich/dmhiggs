import time
from celery import Celery,task

CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

app = Celery('tasks', backend='redis://localhost', broker='redis://')

import redis
red = redis.StrictRedis(host = 'localhost', db = 0)

import emitter
io=emitter.Emitter({'client': red})

import subprocess
import glob
import jinja2
import yoda
import os

@task
def fiducialeff(jobguid):
  print 'processing job guid: {}'.format(jobguid)
  workdir = 'workdirs/{}'.format(jobguid)
  yodafile = '{}/Rivet.yoda'.format(workdir)
  histos = yoda.readYODA(yodafile)
  cutflow = histos['/DMHiggsFiducial/Cutflow']
  print '{} out of {} events passed the event selection'.format(cutflow.bins[-1].area,cutflow.bins[0].area)
  efficiency = cutflow.bins[-1].area/cutflow.bins[0].area
  print 'fiducial efficiency is {}'.format(efficiency)
  print "publishing to request id: {}".format(fiducialeff.request.id)
  io.Of('/monitor').Emit('efficiency_done_{}'.format(jobguid))

  return efficiency

@task
def rivet(jobguid):
  print 'processing job guid: {}'.format(jobguid)

  print rivet.request
  workdir = 'workdirs/{}'.format(jobguid)
  hepmcfiles = glob.glob('{}/*.hepmc'.format(workdir))
  yodafile = '{}/Rivet.yoda'.format(workdir)
  plotdir = '{}/plots'.format(workdir)
  subprocess.call(['rivet','-a','DMHiggsFiducial','-H',yodafile,'--analysis-path=/Users/lukas/Code/atlas/dmhiggs/rivet']+hepmcfiles)
  subprocess.call(['rivet-mkhtml','-c','../../DMHiggsFiducial.plot','-o',plotdir,yodafile])
  print "publishing to request id: {}".format(rivet.request.id)
  io.Of('/monitor').Emit('rivet_done_{}'.format(jobguidef))

  return jobguid
  
@task
def pythia(jobguid):
  print 'processing job guid: {}'.format(jobguid)

  workdir = 'workdirs/{}'.format(jobguid)

  eventfiles = glob.glob("{}/inputs/*.events".format(workdir))
  env = jinja2.Environment(undefined=jinja2.StrictUndefined)

  for file in eventfiles:
    absinputfname = os.path.abspath(file)
    basefname = os.path.basename(absinputfname)

    steeringfname = '{}/{}.steering'.format(workdir,basefname)
    outfname = workdir+'/'+'.'.join(basefname.split('.')[0:-1]+['hepmc'])

    with open('../../pythiasteering.tplt') as steeringfile:
      template = env.from_string(steeringfile.read())
      with open(steeringfname,'w+') as output:
        output.write(template.render({'INPUTLHEF':absinputfname}))

    subprocess.call(['../../pythia/pythiarun',steeringfname,outfname])

  io.Of('/monitor').Emit('pythia_done_{}'.format(jobguid))

  return jobguid


@task
def prepare_workdir(fileguid,jobguid):
  uploaddir = 'uploads/{}'.format(fileguid)
  workdir = 'workdirs/{}'.format(jobguid)
  
  os.makedirs(workdir)
  os.symlink(os.path.abspath(uploaddir),workdir+'/inputs')
  io.Of('/monitor').Emit('pubsubmsg','prepared workdirectory...')
  return jobguid