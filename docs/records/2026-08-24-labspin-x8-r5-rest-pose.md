# LABSPIN X8 r5 joint-satisfied preview rest pose

The r5 package derives from the qualified r4 contact-control package without
changing raw files, joint frames, limits, drives, collision, mass, inertia,
the fixed base joint, or the embedded behavior graph. It authors each dynamic
link at the closed zero-joint solution computed from the existing joint local
frames. For this asset every body1 local frame is zero/identity, so the link
translation equals the corresponding body0 `localPos0`.

Isaac Sim 4.1 measured zero constraint residual and zero reset/ten-step jump
for lid, rotor, encoder, START, STOP, and LID OPEN links. The existing physical
contact qualification was rerun unchanged: OPEN reaches and holds about 78°,
the spinning-rotor interlock blocks opening, and STOP transitions power to off.
The package is promoted as
`labspin_x8_centrifuge_task11_r5_rest_pose_isaac41`; robot and Task11 success
remain unclaimed.
