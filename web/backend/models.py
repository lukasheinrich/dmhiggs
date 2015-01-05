import uuid

class Model(object):
  """new physics model to which we want to recast"""

  @classmethod
  def create(cls,name,description):
    modelId  = uuid.uuid1()
    return Model(name,description,modelId)
    
  def __init__(self,name,description,modelId):
    self.name = name
    self.description = description
    self.modelId = modelId

class Analysis(object):
  """existing analysis that is to be recast"""

  @classmethod
  def create(cls,name,description):
    analysisId  = uuid.uuid1()
    return Analysis(name,description,analysisId)
    
  def __init__(self,name,description,analysisId):
    self.name = name
    self.description = description
    self.analysisId = analysisId

class User(object):
  """class describing an Analysis that can be recast using a new signal model"""
  
  def __init__(self, username, name, email):
    self.username = username
    self.name = name
    self.email = email

class BasicRequest(object):
  """class representation of a basic recast request
     lhefileglob: glob pattern to inputfiles
     requestor: username of the reqeuster
     requestuuid: uuid of the request
     analysisuuid: uuid of the analysis (i.e. the base analysis which to be recast)
     modeluuid: uuid of the new model to which we will recast
  """
  
  @classmethod
  def create(cls,requestor,analysisId,modelId):
    requestId  = uuid.uuid1()
    lhefileglob  = 'uploads/{}/*.events'.format(modelId)
    return BasicRequest(requestor,lhefileglob,requestId,analysisId,modelId)

  def __init__(self, requestor, lhefileglob, requestId, analysisId, modelId):
    self.requestor = requestor
    self.lhefileglob = lhefileglob
    self.requestId = requestId
    self.analysisId = analysisId
    self.modelId = modelId
