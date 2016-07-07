class Connector(object):
    default_name="Default"
    
    def __init__(self, typeX, typeY, connect_fnc, disconnect_fnc=None, 
                 connected_fnc=None, name=default_name):
        self.typeX = typeX
        self.typeY = typeY
        self.connect_fnc = connect_fnc
        self.disconnect_fnc = disconnect_fnc
        self.connected_fnc = connected_fnc
        self.name = name
        
    def typecheck(self, X, Y):
        if not (isinstance(X, self.typeX) and isinstance(Y, self.typeY)):
            raise TypeError("expected types - %s and %s" % (self.typeX, self.typeY))
            
    def connect(self, X, Y):
        self.typecheck(X, Y)
        self.connect_fnc(X, Y)
        
    def disconnect(self, X, Y):
        self.typecheck(X, Y)
        self.disconnect_fnc(X, Y)
        
    def toggle(self, X, Y):
        self.typecheck(X, Y)
        (self.disconnect_fnc if self.connected_fnc(X, Y) else self.connect_fnc)(X, Y)
        
    def connected(self, X, Y):
        self.typecheck(X, Y)
        return self.connected_fnc(X, Y)
        
class Builder(object):
    connector = Connector
    
    def __init__(self):
        self.connectors = dict()
        
    def new_connector(self, typeX, typeY, connect_fnc, disconnect_fnc=None, 
                      connected_fnc=None, name=Connector.default_name):
        connector = Connector(typeX, typeY, connect_fnc, disconnect_fnc, connected_fnc, name)
        self.add_connector(connector)
        
    def add_connector(self, connector):
        try:
            X_connectors = self.connectors[connector.typeX]
        except KeyError:
            X_connectors = self.connectors[connector.typeX] = dict()
        try:
            XY_connectors = X_connectors[connector.typeY]
        except KeyError:
            XY_connectors = X_connectors[connector.typeY] = dict()
        XY_connectors[connector.name] = connector
        
    def get_connector(self, X, Y, name="Default"):
        for typeX in X.mro():
            for typeY in Y.mro():
                try:
                    return self.connectors[typeX][typeY][name]
                except KeyError:
                    pass
        raise ValueError("could not find connector")
        
    def connect(self, X, Y, name=Connector.default_name):
        self.get_connector(X, Y, name).connect(X, Y)
        
    def disconnect(self, X, Y, name=Connector.default_name):
        self.get_connector(X, Y, name).disconnect(X, Y)
        
    def toggle(self, X, Y, name=Connector.default_name):
        self.get_connector(X, Y, name).toggle(X, Y)
        
    def connected(self, X, Y, name=Connector.default_name):
        return self.get_connector(X, Y, name).connected(X, Y)
        