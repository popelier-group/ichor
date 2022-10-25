from collections import namedtuple

AtomForce = namedtuple("AtomForce", "x y z")
MolecularDipole = namedtuple("MolecularDipole", "x y z total")
MolecularQuadrupole = namedtuple("MolecularQuadrupole", "xx yy zz xy xz yz")
TracelessMolecularQuadrupole = namedtuple("TracelessMolecularQuadrupole", "xx yy zz xy xz yz")
MolecularOctapole = namedtuple("MolecularOctapole", "xxx yyy zzz xyy xxy xxz xzz yzz yyz xyz")
MolecularHexadecapole = namedtuple("MolecularHexadecapole", "xxxx yyyy zzzz xxxy xxxz yyyx yyyz zzzx zzzy xxyy xxzz yyzz xxyz yyxz zzxy")