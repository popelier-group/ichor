from ichor.submission_script.aimall import AIMAllCommand
from ichor.submission_script.gaussian import GaussianCommand
from ichor.submission_script.submision_script import SubmissionScript
from pathlib import Path

g1 = GaussianCommand(Path("TRAINING_SET/WATER0001.gjf"))
g2 = GaussianCommand(Path("TRAINING_SET/WATER0002.gjf"))
g3 = GaussianCommand(Path("TRAINING_SET/WATER0003.gjf"))

a1 = AIMAllCommand(Path("TRAINING_SET/WATER0001.wfn"))
a2 = AIMAllCommand(Path("TRAINING_SET/WATER0002.wfn"))
a3 = AIMAllCommand(Path("TRAINING_SET/WATER0003.wfn"))

ss = SubmissionScript(Path("AIMSub.sh"))
ss.add_command(g1)
ss.add_command(g2)
ss.add_command(g3)
ss.add_command(a1)
ss.add_command(a2)
ss.add_command(a3)
ss.write()
