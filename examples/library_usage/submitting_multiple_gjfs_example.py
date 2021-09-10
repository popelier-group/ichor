from ichor.main.submit_gjfs import submit_gjfs
from ichor.files.trajectory import Trajectory

traj = Trajectory("WATER.xyz")
traj.to_dir("./water_no_angle_change")