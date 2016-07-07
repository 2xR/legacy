from sys import stdout
from khronos.utils import indentation, FunctionProxy

class MembersProxy(FunctionProxy):
    """A proxy class that provides methods to access the members of a component."""
    pass
    
class TreeProxy(FunctionProxy):
    """A proxy class that provides methods for component tree access and manipulation."""
    pass
    
class Component(object):
    """This class supports the creation of trees of components, allowing a hierarchical 
    organization of models. Each component may be inside a parent component, and may contain 
    other components as members. A component with no parent is called a root component. 
    Components also have a name (which must be locally unique, i.e. unique among its siblings), 
    and a globally unique path that identifies how to reach the component starting from the 
    root component."""
    # -----------------------------------------------------
    # Path format control attributes ----------------------
    path_separator = "."
    path_parent    = "<"
    path_root      = "#"
    path_illegal   = set(path_separator + path_parent + path_root)
    
    # -----------------------------------------------------
    # Magic methods ---------------------------------------
    def __init__(self, name=None, parent=None, members=()):
        if name is None:
            name = self.__class__.autoname_generate()
        name = Component.validate_name(name)
        self.__name = name
        self.__path = ""
        self.__parent = None
        self.__root = self
        self.__members = dict()
        self.__members_proxy = MembersProxy(self)
        self.__tree_proxy = TreeProxy(self)
        if parent is not None:
            parent.__members_add(self)
        for member in members:
            self.__members_add(member)
            
    def __repr__(self):
        return "<%s - %s object at 0x%08x>" % (self.full_path, self.__class__.__name__, id(self))
        
    def __str__(self):
        return self.full_path
        
    # -----------------------------------------------------
    # Basic component properties --------------------------
    @property
    def name(self):
        return self.__name
        
    @name.setter
    def name(self, name):
        name = Component.validate_name(name)
        if self.__parent is not None:
            if name in self.__parent.__members:
                raise KeyError("name '%s' already in use at %s" % (name, self.__parent))
            # Rebind name in parent component
            del self.__parent.__members[self.__name]
            self.__parent.__members[name] = self
        self.__name = name
        self.__hierarchy_update()
        
    @property
    def path(self):
        return self.__path
        
    @property
    def full_path(self):
        if self.__parent is None:
            return self.__name
        return Component.path_separator.join((self.__root.__name, self.__path))
        
    @property
    def parent(self):
        return self.__parent
        
    @parent.setter
    def parent(self, parent):
        if parent is not self.__parent:
            if self.__parent is not None:
                self.__parent.__members_remove(self)
            if parent is not None:
                parent.__members_add(self)
                
    @property
    def root(self):
        return self.__root
        
    @property
    def members(self):
        return self.__members_proxy

    @property
    def tree(self):
        return self.__tree_proxy
        
    # -----------------------------------------------------
    # 'members' methods -----------------------------------
    @MembersProxy.include
    def __len__(self):
        """Returns the number of members of the component."""
        return len(self.__members)
        
    @MembersProxy.include
    def __iter__(self):
        """Iterates over the members of the component."""
        return self.__members.itervalues()
        
    @MembersProxy.include
    def __contains__(self, member):
        """When a component is provided, this method checks that there is a member with 
        the same name in the local space, AND it must also be the exact same object that 
        was passed as argument.
        If an object of another type is provided, it checks whether the component has a 
        member whose name is equal to the string representation of the argument."""
        if isinstance(member, Component):
            try:
                return member is self.__members[member.__name]
            except KeyError:
                return False
        else:
            return str(member) in self.__members
            
    @MembersProxy.include
    def __getitem__(self, name):
        return self.__members[str(name)]
        
    @MembersProxy.include
    def __setitem__(self, name, member):
        name = Component.validate_name(name)
        if name in self.__members:
            raise KeyError("name '%s' already in use at %s" % (name, self))
        if member.__parent is not None:
            member.__parent.__members_remove(member)
        member.__name = name
        self.__members_add(member)
        
    @MembersProxy.include
    def __delitem__(self, name):
        target = self.__members[str(name)]
        self.__members_remove(target)
        
    @MembersProxy.include
    def add(self, member):
        """Add a member to a component."""
        name = member.__name
        if name in self.__members:
            raise KeyError("name '%s' already in use at %s" % (name, self))
        if member.__parent is not None:
            member.__parent.__members_remove(member)
        member.__parent = self
        member.__hierarchy_update()
        self.__members[name] = member
        
    @MembersProxy.include
    def extend(self, members):
        """Add a collection of members to the component. Equivalent to:
            for member in members:
                component.add(member)
        """
        for member in members:
            self.__members_add(member)
            
    @MembersProxy.include
    def remove(self, member):
        """Remove a member from a component."""
        if not self.__members_contains(member):
            raise KeyError("member %s not found in %s" % (member, self))
        member.__parent = None
        member.__hierarchy_update()
        del self.__members[member.__name]
        
    @MembersProxy.include
    def clear(self):
        """Clear a component of all its members."""
        for member in list(self.__members.itervalues()):
            self.__members_remove(member)
            
    # Keep private references to the original methods for internal use.
    __members_len      = __len__
    __members_iter     = __iter__
    __members_contains = __contains__ 
    __members_getitem  = __getitem__
    __members_setitem  = __setitem__
    __members_delitem  = __delitem__
    __members_add      = add
    __members_extend   = extend
    __members_remove   = remove
    __members_clear    = clear
    # -----------------------------------------------------
    # 'tree' methods --------------------------------------
    @TreeProxy.include("__len__")
    def tree_len(self):
        if len(self.__members) == 0:
            return 1
        return 1 + sum(member.__tree_len() for member in self.__members.itervalues())
        
    @TreeProxy.include("__getitem__")
    def tree_get(self, path):
        """Find a component in the hierarchy tree by its path. 
        TODO: write documentation for path format."""
        target = self
        path = str(path)
        if len(path) > 0:
            for symbol in path.split(Component.path_separator):
                if symbol == Component.path_root:
                    target = target.__root
                elif symbol == Component.path_parent:
                    target = target.__parent
                else:
                    target = target.__members[symbol]
        return target
        
    @TreeProxy.include("__setitem__")
    def tree_set(self, path, member):
        """Add a component to the model tree at the point specified by 'path'."""
        parts = str(path).split(Component.path_separator)
        parent = self.__tree_getitem(Component.path_separator.join(parts[:-1]))
        parent.__members_setitem(parts[-1], member)
        
    @TreeProxy.include("__delitem__")
    def tree_del(self, path):
        """Remove the component specified by 'path' from the model tree."""
        parts = str(path).split(Component.path_separator)
        parent = self.__tree_getitem(Component.path_separator.join(parts[:-1]))
        parent.__members_delitem(parts[-1])
        
    @TreeProxy.include("iter")
    def tree_iter(self, order=None, depth=0):
        """Make a pre-order visit to all the components in the model tree, from this point down. 
        The order by which the members of a component are visited is controlled by the 'order' 
        argument, which should be a function as taken by the built-in sorted() function's 'key' 
        argument. By default members are ordered by their name.
        This method returns a generator, traversing the model using the specified ordering. The 
        generator yields (component, depth) tuples, where depth represents the level in the 
        hierarchy tree where the component is located (0 for the component where the first call
        was made)."""
        if order is None:
            order = Component.name.__get__
        yield self, depth
        for member in sorted(self.__members.itervalues(), key=order):
            for m, d in member.__tree_iter(order, depth + 1):
                yield m, d
                
    @TreeProxy.include("status")
    def tree_status(self, order=None, out=stdout):
        """This method prints the status of a whole model tree, using __tree_iter() and status().
        Text is indented using __tree_iter()'s depth information, providing an intuitive view
        of the model's tree structure. An output stream may be provided, such as a file or string 
        buffer (default=sys.stdout), where the status tree will be printed. Additionally, the 
        'order' argument of the __tree_iter() method can be specified."""
        nl = "\n"
        status_indent = "| "
        for comp, depth in self.__tree_iter(order=order):
            indent = indentation(depth)
            status = str(comp.status()).replace(nl, nl + indent + status_indent)
            out.write("%s* %s (%s:%d) %s\n" % (indent, comp.__name, 
                                               comp.__class__.__name__, 
                                               len(comp.__members), status))
        out.flush()
        
    # Keep private references to the original methods for internal use.
    __tree_len     = tree_len
    __tree_getitem = tree_get
    __tree_setitem = tree_set
    __tree_delitem = tree_del
    __tree_iter    = tree_iter
    __tree_status  = tree_status
    # -----------------------------------------------------
    # Utilities -------------------------------------------
    __autoname_counter = {}
    
    @classmethod
    def autoname_generate(cls):
        """Generate a name for an instance of the argument class, by appending an integer to the
        class' name, e.g. Foo.autoname_generate() -> 'Foo0'."""
        n = Component.__autoname_counter.get(cls, 0)
        name = "%s%d" % (cls.__name__, n)
        Component.__autoname_counter[cls] = n + 1
        return name
        
    @classmethod
    def autoname_reset(cls):
        """Reset the counter of class instances used for automatic name generation. The next 
        instance of class 'Foo' that requests an automatic name will be named 'Foo0'."""
        if cls in Component.__autoname_counter:
            del Component.__autoname_counter[cls]
            
    @staticmethod
    def validate_name(name):
        """Component name validation procedure. This method checks the type and value of a name. 
        Names must be non-empty and may not contain any illegal characters."""
        name = str(name)
        if len(name) == 0:
            raise NameError("empty component name")
        illegal = Component.path_illegal.intersection(name)
        if len(illegal) > 0:
            raise NameError("illegal chars found %s" % (list(illegal),))
        return name
        
    def __hierarchy_update(self):
        """This private method is called after changes in the hierarchy. Hierarchy changes 
        include setting a component's parent or name."""
        if self.__parent is None:
            self.__root = self
            self.__path = ""
        else:
            self.__root = self.__parent.__root
            if self.__root is self.__parent:
                self.__path = self.__name
            else:
                self.__path = Component.path_separator.join((self.__parent.__path, self.__name))
        for member in self.__members.itervalues():
            member.__hierarchy_update()
            
    def status(self):
        """This method should be redefined in subclasses. It is used for printing a model's state, 
        so it should return any information that is relevant for understanding the component's 
        state at the time of the call."""
        return ""
        