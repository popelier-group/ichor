from ichor.core.files.dl_poly import DlPolyConfig  
from ichor.core.files import Trajectory 

atoms = Trajectory("GLUTATHIONE.xyz")
config = DlPolyConfig("CONFIG","GLUTATHIONE",atoms)
config.write()
