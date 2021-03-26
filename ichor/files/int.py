import json
import re

import numpy as np

from ichor import constants, patterns
from ichor.common.functools import buildermethod, classproperty
from ichor.common.io import move
from ichor.files.file import File
from ichor.geometry import GeometryData


class INT(GeometryData, File):
    def __init__(self, path, atom=None):
        File.__init__(self, path)
        GeometryData.__init__(self)

        self.parent = atom

        self.integration_data = GeometryData()
        self.multipoles_data = GeometryData()
        self.iqa_data = GeometryData()

    @property
    def atom(self) -> str:
        return self.path.stem.upper()

    @classproperty
    def filetype(cls) -> str:
        return ".int"

    @buildermethod
    def _read_file(self, atom=None):
        self.parent = atom
        try:
            self.read_json()
        except json.decoder.JSONDecodeError:
            self.read_int()
            # Backup only if read correctly
            # E_IQA_Inter(A) Last Line that needs to be parsed, if this is here then the
            # rest of the values we care about should be
            if "E_IQA_Inter(A)" in self.iqa_data.keys():
                self.backup_int()
                self.write_json()
            else:
                # Delete corrupted file so it can be regenerated
                self.delete()

    @buildermethod
    def read_int(self):
        with open(self.path, "r") as f:
            for line in f:
                if "Results of the basin integration:" in line:
                    line = next(f)
                    while line.strip():
                        for match in re.finditer(patterns.AIMALL_LINE, line):
                            tokens = match.group().split("=")
                            try:
                                self.integration_data[
                                    tokens[0].strip()
                                ] = float(tokens[-1])
                            except ValueError:
                                print(f"Cannot convert {tokens[-1]} to float")
                        line = next(f)
                if "Real Spherical Harmonic Moments Q[l,|m|,?]" in line:
                    line = next(f)
                    line = next(f)
                    line = next(f)
                    line = next(f)
                    while line.strip():
                        if "=" in line:
                            tokens = line.split("=")
                            try:
                                multipole = (
                                    tokens[0]
                                    .strip()
                                    .replace("[", "")
                                    .replace(",", "")
                                    .replace("]", "")
                                )
                                self.multipoles_data[
                                    multipole.lower()
                                ] = float(tokens[-1])
                            except ValueError:
                                print(f"Cannot convert {tokens[-1]} to float")
                        line = next(f)
                if 'IQA Energy Components (see "2EDM Note"):' in line:
                    line = next(f)
                    line = next(f)
                    while line.strip():
                        if "=" in line:
                            tokens = line.split("=")
                            try:
                                self.iqa_data[tokens[0].strip()] = float(
                                    tokens[-1]
                                )
                            except ValueError:
                                print(f"Cannot convert {tokens[-1]} to float")
                        line = next(f)
        if self.parent:
            self.rotate_multipoles()

    def delete(self):
        self.path.unlink()

    def rotate_multipoles(self):
        self.rotate_dipole()
        self.rotate_quadrupole()
        self.rotate_octupole()
        self.rotate_hexadecapole()

    @property
    def C(self):
        try:
            return self._C
        except KeyError:
            r12 = np.array(self.parent.vec_to(self.parent.x_axis))
            r13 = np.array(self.parent.vec_to(self.parent.xy_plane))

            mod_r12 = self.parent.dist(self.parent.x_axis)

            r12 /= mod_r12

            ex = r12
            s = sum(ex * r13)
            ey = r13 - s * ex

            ey /= np.sqrt(sum(ey * ey))
            ez = np.cross(ex, ey)
            self._C = np.array([ex, ey, ez])
            return self._C

    def rotate_dipole(self):
        d = np.array([self.q11c, self.q11s, self.q10])
        rotated_d = np.einsum("ia,a->i", self.C, d)
        self.q10 = rotated_d[2]
        self.q11c = rotated_d[0]
        self.q11s = rotated_d[1]

    def rotate_quadrupole(self):
        q_xx = 0.5 * constants.rt3 * self.q22c - self.q20
        q_xy = 0.5 * constants.rt3 * self.q22s
        q_xz = 0.5 * constants.rt3 * self.q21c
        q_yy = -0.5 * constants.rt3 * self.q22c + self.q20
        q_yz = 0.5 * constants.rt3 * self.q21s
        q_zz = self.q20

        q = np.array(
            [[q_xx, q_xy, q_xz], [q_xy, q_yy, q_yz], [q_xz, q_yz, q_zz]]
        )

        rotated_q = np.einsum("ia,jb,ab->ij", self.C, self.C, q)

        self.q20 = rotated_q[2, 2]
        self.q21c = constants.rt12_3 * rotated_q[0, 2]
        self.q21s = constants.rt12_3 * rotated_q[1, 2]
        self.q22c = constants.rt3_3 * (rotated_q[0, 0] - rotated_q[1, 1])
        self.q22s = constants.rt12_3 * rotated_q[0, 1]

    def rotate_octupole(self):
        o_xxx = constants.rt5_8 * self.q33c - constants.rt3_8 * self.q31c
        o_xxy = constants.rt5_8 * self.q33s - constants.rt1_24 * self.q31s
        o_xxz = constants.rt5_12 * self.q32c - 0.5 * self.q30
        o_xyy = -(constants.rt5_8 * self.q33c + constants.rt1_24 * self.q31c)
        o_xyz = constants.rt5_12 * self.q32s
        o_xzz = constants.rt2_3 * self.q31c
        o_yyy = -(constants.rt5_8 * self.q33s + constants.rt3_8 * self.q31s)
        o_yyz = -(constants.rt5_12 * self.q32c + 0.5 * self.q30)
        o_yzz = constants.rt2_3 * self.q31s
        o_zzz = self.q30

        o = np.array(
            [
                [
                    [o_xxx, o_xxy, o_xxz],
                    [o_xxy, o_xyy, o_xyz],
                    [o_xxz, o_xyz, o_xzz],
                ],
                [
                    [o_xxy, o_xyy, o_xyz],
                    [o_xyy, o_yyy, o_yyz],
                    [o_xyz, o_yyz, o_yzz],
                ],
                [
                    [o_xxz, o_xyz, o_xzz],
                    [o_xyz, o_yyz, o_yzz],
                    [o_xzz, o_yzz, o_zzz],
                ],
            ]
        )

        rotated_o = np.einsum("ia,jb,kc,abc->ijk", self.C, self.C, self.C, o)

        self.q30 = rotated_o[2, 2, 2]
        self.q31c = constants.rt_3_3 * rotated_o[0, 2, 2]
        self.q31s = constants.rt_3_3 * rotated_o[1, 2, 2]
        self.q32c = constants.rt_3_5 * (
            rotated_o[0, 0, 2] - rotated_o[1, 1, 2]
        )
        self.q32s = 2 * constants.rt_3_5 * rotated_o[0, 1, 2]
        self.q33c = constants.rt_1_10 * (
            rotated_o[0, 0, 0] - 3 * rotated_o[0, 1, 1]
        )
        self.q33s = constants.rt_1_10 * (
            3 * rotated_o[0, 0, 1] - rotated_o[1, 1, 1]
        )

    def rotate_hexadecapole(self):
        h_xxxx = (
            0.375 * self.q40
            - 0.25 * constants.rt5 * self.q42c
            + 0.125 * constants.rt35 * self.q44c
        )
        h_xxxy = 0.125 * (
            constants.rt35 * self.q44s - constants.rt5 * self.q42s
        )
        h_xxxz = 0.0625 * (
            constants.rt70 * self.q43c - 3.0 * constants.rt10 * self.q41c
        )
        h_xxyy = 0.125 * self.q40 - 0.125 * constants.rt35 * self.q44c
        h_xxyz = 0.0625 * (
            constants.rt70 * self.q43s - constants.rt10 * self.q41s
        )
        h_xxzz = 0.5 * (0.5 * constants.rt5 * self.q42c - self.q40)
        h_xyyy = -0.125 * (
            constants.rt5 * self.q42s + constants.rt35 * self.q44s
        )
        h_xyyz = -0.0625 * (
            constants.rt10 * self.q41c + constants.rt70 * self.q43c
        )
        h_xyzz = 0.25 * constants.rt5 * self.q42s
        h_xzzz = constants.rt5_8 * self.q41c
        h_yyyy = (
            0.375 * self.q40
            + 0.25 * constants.rt5 * self.q42c
            + 0.125 * constants.rt35 * self.q44c
        )
        h_yyyz = -0.0625 * (
            3.0 * constants.rt10 * self.q41s + constants.rt70 * self.q43s
        )
        h_yyzz = -0.5 * (0.5 * constants.rt5 * self.q42c + self.q40)
        h_yzzz = constants.rt5_8 * self.q41s
        h_zzzz = self.q40

        h = np.array(
            [
                [
                    [
                        [h_xxxx, h_xxxy, h_xxxz],
                        [h_xxxy, h_xxyy, h_xxyz],
                        [h_xxxz, h_xxyz, h_xxzz],
                    ],
                    [
                        [h_xxxy, h_xxyy, h_xxyz],
                        [h_xxyy, h_xyyy, h_xyyz],
                        [h_xxyz, h_xyyz, h_xyzz],
                    ],
                    [
                        [h_xxxz, h_xxyz, h_xxzz],
                        [h_xxyz, h_xyyz, h_xyzz],
                        [h_xxzz, h_xyzz, h_xzzz],
                    ],
                ],
                [
                    [
                        [h_xxxy, h_xxyy, h_xxyz],
                        [h_xxyy, h_xyyy, h_xyyz],
                        [h_xxyz, h_xyyz, h_xyzz],
                    ],
                    [
                        [h_xxyy, h_xyyy, h_xyyz],
                        [h_xyyy, h_yyyy, h_yyyz],
                        [h_xyyz, h_yyyz, h_yyzz],
                    ],
                    [
                        [h_xxyz, h_xyyz, h_xyzz],
                        [h_xyyz, h_yyyz, h_yyzz],
                        [h_xyzz, h_yyzz, h_yzzz],
                    ],
                ],
                [
                    [
                        [h_xxxz, h_xxyz, h_xxzz],
                        [h_xxyz, h_xyyz, h_xyzz],
                        [h_xxzz, h_xyzz, h_xzzz],
                    ],
                    [
                        [h_xxyz, h_xyyz, h_xyzz],
                        [h_xyyz, h_yyyz, h_yyzz],
                        [h_xyzz, h_yyzz, h_yzzz],
                    ],
                    [
                        [h_xxzz, h_xyzz, h_xzzz],
                        [h_xyzz, h_yyzz, h_yzzz],
                        [h_xzzz, h_yzzz, h_zzzz],
                    ],
                ],
            ]
        )

        h_rotated = np.einsum(
            "ia,jb,kc,ld,abcd->ijkl", self.C, self.C, self.C, self.C, h
        )

        self.q40 = h_rotated[2, 2, 2, 2]
        self.q41c = constants.rt_8_5 * h_rotated[0, 2, 2, 2]
        self.q41s = constants.rt_8_5 * h_rotated[1, 2, 2, 2]
        self.q42c = (
            2
            * constants.rt_1_5
            * (h_rotated[0, 0, 2, 2] - h_rotated[1, 1, 2, 2])
        )
        self.q42s = 4 * constants.rt_1_5 * h_rotated[0, 1, 2, 2]
        self.q43c = (
            2
            * constants.rt_2_35
            * (h_rotated[0, 0, 0, 2] - 3 * h_rotated[0, 1, 1, 2])
        )
        self.q43s = (
            2
            * constants.rt_2_35
            * (3 * h_rotated[0, 0, 1, 2] - h_rotated[1, 1, 1, 2])
        )
        self.q44c = constants.rt_1_35 * (
            h_rotated[0, 0, 0, 0]
            - 6 * h_rotated[0, 0, 1, 1]
            + h_rotated[1, 1, 1, 1]
        )
        self.q44s = (
            4
            * constants.rt_1_35
            * (h_rotated[0, 0, 0, 1] - h_rotated[0, 1, 1, 1])
        )

    @buildermethod
    def read_json(self):
        with open(self.path, "r") as f:
            int_data = json.load(f)
            self.integration_data = int_data["integration"]
            self.multipoles_data = int_data["multipoles"]
            self.iqa_data = int_data["iqa_data"]

    @property
    def backup_path(self):
        return self.path.parent / (self.path.name + ".bak")

    def backup_int(self):
        self.move(self.backup_path)

    def write_json(self):
        int_data = {
            "integration": self.integration_data,
            "multipoles": self.multipoles_data,
            "iqa_data": self.iqa_data,
        }

        with open(self.path, "w") as f:
            json.dump(int_data, f)

    @property
    def num(self):
        return int(re.findall("\d+", self.atom)[0])

    @property
    def integration_error(self):
        return self.integration_data["L"]

    @property
    def eiqa(self):
        return self.iqa_data["E_IQA(A)"]

    @property
    def iqa(self):
        return self.eiqa

    @property
    def multipoles(self):
        return {
            multipole: self.multipoles_data[multipole]
            for multipole in constants.multipole_names
        }

    @property
    def q(self):
        return self.integration_data["q"]

    @property
    def q00(self):
        return self.q

    @property
    def dipole(self):
        return np.sqrt(sum([self.q10 ** 2, self.q11c ** 2, self.q11s ** 2]))

    def revert_backup(self):
        move(self.backup_path, self.path)

    def getattr_as_dict(self, attr):
        pass
