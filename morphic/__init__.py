from morphic.mesher import Mesh
from morphic.data import Data
from morphic.fitter import Fit
from morphic.fasteval import FEMatrix
from importlib import reload

reload_modules = True
if reload_modules:
    from morphic import mesher
    reload(mesher)
    from morphic import interpolator
    reload(interpolator)
    from morphic.mesher import Mesh
    from morphic import fitter
    reload(fitter)
    from morphic.fitter import Fit

