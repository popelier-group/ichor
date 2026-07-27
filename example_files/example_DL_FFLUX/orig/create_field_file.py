from ichor.core.files.dl_poly import DlPolyField
from ichor.core.files import PointDirectory
from ichor.core.files import GJF,XYZ

atoms = XYZ("GLUTATHIONE.xyz").atoms
config = DlPolyField("FIELD",atoms,"GLUTATHIONE")
config.write()
