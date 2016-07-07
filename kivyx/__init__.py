import kivy
kivy.require("1.7.2")

"""
List of known kivy "peculiarities":

- do NOT pass 'parent=XXX' to a widget constructor, because the parent widget is not properly
    linked to the child. However, the child widget still thinks he's not an orphan... :D
- passing position and size to a widget constructor will do the two operations in arbitrary order.
    This means that the position may be set before resizing the widget, which can lead to unxpected
    results. As a general rule, do not pass any arguments to widget constructors.

"""
