def indent(message, indentation=(" " * 4), indent_first=True):
    """Indent the lines in 'message' using a custom indentation string."""
    parts = [""] if indent_first else []
    parts.extend(str(message).splitlines(True))
    return str(indentation).join(parts)


def fit(message, width, ellipsis="(...)", multiline=False):
    """Create a new version of 'message' with size 'width' or less. Returns the original message if
    its size is <= 'width'. Otherwise replaces the middle of the message with 'ellipsis', keeping
    the beginning and end of the message.
    If 'multiline' is true, the message is split into lines and fit() is applied separately on
    each line."""
    if not isinstance(message, str):
        message = str(message)
    if multiline and "\n" in message:
        return "\n".join(fit(line, width, ellipsis=ellipsis, multiline=False)
                         for line in message.split("\n"))
    if len(message) <= width:
        return message
    extra_chars = len(message) + len(ellipsis) - width
    pos = (len(message) - extra_chars) / 2
    return message[:pos] + ellipsis + message[pos+extra_chars:]
