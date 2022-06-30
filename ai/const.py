"""Constants used in DemoAgent.

It is a part of DemoAgent's policy and is not necessary in your code.
You can change these names in your own policy.
"""


class BopType:
    Infantry, Vehicle, Aircraft = range(1, 4)


class ActionType:
    Move, Shoot, GetOn, GetOff, Occupy, ChangeState, RemoveKeep, JMPlan, GuideShoot, StopMove, WeaponLock, WeaponUnFold, CancelJMPlan = range(1, 14)


class MoveType:
    Maneuver, March, Walk, Fly = range(4)
