class Extensible(object):
    """An extensible object is an object whose structure is not fully known until runtime. Plugins 
    may be added to the object during execution, and the object may define operations that are 
    propagated to its plugins."""
    def __init__(self, plugins=()):
        self.plugins = []
        for plugin in plugins:
            self.extend(plugin)
            
    def extend(self, plugin):
        self.plugins.append(plugin)
        plugin.init(self)
        
    def propagate(self, operation, *args, **kwargs):
        for plugin in self.plugins:
            function = getattr(plugin, operation, None)
            if function is not None:
                function(self, *args, **kwargs)
                
                