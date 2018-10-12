from importlib import reload
from morphic.mesher import Mesh
from morphic.data import Data
from morphic.fitter import Fit
from morphic.fasteval import FEMatrix

reload_modules = True
if reload_modules:
    import morphic.mesher
    reload(morphic.mesher)
    import morphic.interpolator
    reload(morphic.interpolator)
    from morphic.mesher import Mesh
    import morphic.fitter
    reload(morphic.fitter)
    from morphic.fitter import Fit

