from khronos.des.extra.components.queueing.fifoqueue import FIFOQueue
from khronos.des.extra.components.queueing.psqueue import PSQueue
from khronos.des.extra.components.queueing.isqueue import ISQueue
from khronos.utils import Namespace
queue = Namespace(FIFO=FIFOQueue, PS=PSQueue, IS=ISQueue)

__all__ = ["FIFOQueue", "PSQueue", "ISQueue", "queue"]
