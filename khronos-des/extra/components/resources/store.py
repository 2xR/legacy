from khronos.des import Process, Request
from khronos.utils import INF, Deque, Namespace, FunctionProxy

class ContentProxy(FunctionProxy):
    pass
    
class Store(Process):
    def constructor(self, capacity=INF):
        self.__capacity = capacity
        self.__content = Deque()
        self.__getreqs = Deque()
        self.__putreqs = Deque()
        self.__content_proxy = ContentProxy(self)
        
    def status(self):
        status = "%d items (requests: get=%d / put=%d)" % \
            (len(self.__content), len(self.__getreqs), len(self.__putreqs))
        if len(self.__content) > 0:
            status += "\n" + "\n".join(str(item) for item in self.__content)
        return status
        
    def reset(self):
        self.__content.clear()
        self.__getreqs.clear()
        self.__putreqs.clear()
        
    # -----------------------------------------------------
    # 'content' methods -----------------------------------
    @property
    def content(self):
        return self.__content_proxy
        
    @ContentProxy.include("__len__")
    def __content_len(self):
        return len(self.__content)
        
    @ContentProxy.include("__iter__")
    def __content_iter(self):
        return iter(self.__content)
        
    @ContentProxy.include("__contains__")
    def __content_contains(self, item):
        return item in self.__content
        
    @ContentProxy.include("put")
    def __content_put(self, item):
        return Request(Namespace(type="put", item=item),
                       deploy_fnc=self.__deploy_put, 
                       retract_fnc=self.__putreqs.remove)
        
    @ContentProxy.include("get")
    def __content_get(self, filter=None):
        return Request(Namespace(type="get", filter=filter),
                       deploy_fnc=self.__deploy_get, 
                       retract_fnc=self.__getreqs.remove)
        
    @ContentProxy.include("remove")
    def __content_remove(self, item):
        self.__content.remove(item)
        if len(self.__putreqs) > 0:
            self.__fulfill_put()
            
    @ContentProxy.include("clear")
    def __content_clear(self):
        self.__content.clear()
        if len(self.__putreqs) > 0:
            self.__fulfill_put()
            
    @ContentProxy.include("capacity")
    def __content_capacity(self, capacity=None):
        """Set or get (default) the store's capacity."""
        if capacity is not None:
            if self.running:
                if capacity < len(self.__content):
                    raise ValueError("unable to reduce store size to %d" % (capacity,))
                self.__capacity = capacity
                self.__fulfill_put()
            else:
                self.__capacity = capacity
        return self.__capacity
        
    # -----------------------------------------------------
    # Auxiliary methods for request deployment ------------
    def __deploy_put(self, request):
        self.__putreqs.append(request)
        if len(self.__content) < self.__capacity:
            self.__fulfill_put()
            
    def __fulfill_put(self):
        """Fulfills put requests while there is enough free space in the store."""
        while len(self.__content) < self.__capacity and len(self.__putreqs) > 0:
            request = self.__putreqs.popleft()
            item = request.data.item
            if len(self.__getreqs) == 0 or not self.__fulfill_get(item):
                self.__content.append(item)
            request.fulfill()
            
    def __fulfill_get(self, item):
        """Checks if 'item' fulfills any get request. Returns a boolean indicating success or 
        failure of the fulfillment of a get request."""
        destination = None
        for request in self.__getreqs:
            filter = request.data.filter
            if filter is None or filter(item):
                destination = request
                break
        if destination is None:
            return False
        destination.fulfill(item)
        return True
        
    def __deploy_get(self, request):
        """Check the store's contents for any item that is accepted by the get request. If so, 
        the request is immediately fulfilled, otherwise it is placed in the get request list."""
        filter = request.data.filter
        for item in self.__content:
            if filter is None or filter(item):
                self.__content.remove(item)
                request.fulfill(item)
                if len(self.__putreqs) > 0 and len(self.__content) < capacity:
                    self.__fulfill_put()
                return
        self.__getreqs.append(request)
        
