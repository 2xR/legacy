from khronos.des.primitives.action import Action, UNDEPLOYED

class Request(Action):
    """The Request primitive is a completely flexible action type that must be extended to meet 
    the user's requirements for custom applications. It can be used for any case where the owner 
    process blocks until another process verifies a condition and calls the succeed() method on 
    the request. Requests have an associated 'result' attribute, i.e. a value that represents the 
    fulfillment of the request, which can be passed to the succeed() method.
        TODO: add an example of Request usage."""
    def __init__(self, *args, **kwargs):
        Action.__init__(self)
        self.constructor(*args, **kwargs)
        self.result = None
        
    def constructor(self, *args, **kwargs):
        raise NotImplementedError()
        
    def __info__(self):
        if self.result is None:
            return ""
        return "-> %s" % (self.result,)
        
    def reset(self):
        self.result = None
        
    def deploy(self):
        raise NotImplementedError()
        
    def retract(self):
        raise NotImplementedError()
        
    def succeed(self, result=None):
        self.result = result
        Action.succeed(self)
        
class CustomRequest(Request):
    """A custom request can have its own individual deployment functions, which may be different 
    for every CustomRequest object."""
    def constructor(self, data=None, deploy_fnc=None, retract_fnc=None):
        self.data = data
        self.deploy_fnc = deploy_fnc
        self.retract_fnc = retract_fnc
        
    def configure(self, deploy_fnc=None, retract_fnc=None):
        if deploy_fnc is not None: self.deploy_fnc = deploy_fnc
        if retract_fnc is not None: self.retract_fnc = retract_fnc
        
    def __info__(self):
        info = str(self.data) if self.data is not None else ""
        if self.result is not None:
            info += " -> %s" % (self.result,)
        return info
        
    def deploy(self):
        if self.deploy_fnc is None or self.retract_fnc is None:
            raise Exception("missing deployment method(s) in custom request")
        self.deploy_fnc(self)
        
    def retract(self):
        self.retract_fnc(self)
        
Request.custom = CustomRequest
