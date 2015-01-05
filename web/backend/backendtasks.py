import time
from celery import Celery,task

CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

app = Celery('tasks', backend='redis://localhost', broker='redis://')


import subprocess
import glob
import jinja2
import yoda
import os
import shutil

import redis
import emitter

red = redis.StrictRedis(host = 'localhost', db = 0)
io  = emitter.Emitter({'client': red})

@task
def postresults(jobguid,requestId):
  workdir = 'workdirs/{}'.format(jobguid)
  yodafile = '{}/Rivet.yoda'.format(workdir)
  resultdir = 'results/{}'.format(requestId)
  
  if(os.path.exists(resultdir)):
    shutil.rmtree(resultdir)
    
  os.makedirs(resultdir)
  
  shutil.copytree('{}/plots'.format(workdir),'{}/plots'.format(resultdir))
  shutil.copyfile('{}/Rivet.yoda'.format(workdir),'{}/Rivet.yoda'.format(resultdir))

  io.Of('/monitor').Emit('postresults_done_{}'.format(jobguid),{'requestId':requestId})


@task
def fiducialeff(requestId):
  resultdir = 'results/{}'.format(requestId)
  yodafile = '{}/Rivet.yoda'.format(resultdir)
  histos = yoda.readYODA(yodafile)
  cutflow = histos['/DMHiggsFiducial/Cutflow']
  efficiency = cutflow.bins[-1].area/cutflow.bins[0].area
  io.Of('/monitor').Emit('efficiency_done_{}'.format(requestId))

  return efficiency

@task
def rivet(jobguid):
  workdir = 'workdirs/{}'.format(jobguid)
  hepmcfiles = glob.glob('{}/*.hepmc'.format(workdir))

  if not hepmcfiles: raise IOError

  yodafile = '{}/Rivet.yoda'.format(workdir)
  plotdir = '{}/plots'.format(workdir)
  analysisdir = os.path.abspath('../../rivet')
  subprocess.call(['rivet','-a','DMHiggsFiducial','-H',yodafile,'--analysis-path={}'.format(analysisdir)]+hepmcfiles)
  subprocess.call(['rivet-mkhtml','-c','../../rivet/DMHiggsFiducial.plot','-o',plotdir,yodafile])
  io.Of('/monitor').Emit('rivet_done_{}'.format(jobguid))

  return jobguid
  
@task
def pythia(jobguid):
  workdir = 'workdirs/{}'.format(jobguid)

  fileglob = "{}/inputs/*.events".format(workdir)
  print "looking for files: {}".format(fileglob)
  eventfiles = glob.glob("{}/inputs/*.events".format(workdir))
  
  print 'found {} event files'.format(len(eventfiles))
  
  env = jinja2.Environment(undefined=jinja2.StrictUndefined)


  if not eventfiles: raise IOError

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