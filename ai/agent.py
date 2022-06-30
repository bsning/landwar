"""A simple agent implementation.

DemoAgent class inherits from BaseAgent and implement all three
abstract methods: setup(), step() and reset().
"""
import json #导入json包 实现格式的转换(字符串和字典的转换)
import os #导入os 与操作系统相关的模块
import random  #导入random 包

from ai.const import BopType, ActionType, MoveType #从文件夹中导入
from core.agent.base_agent import BaseAgent
from core.utils.map import Map


class Agent(BaseAgent): #定义基类
    def __init__(self):
        self.scenario = None  # 想定为空
        self.color = None  # 颜色
        self.priority = None  # 优先级
        self.observation = None
        self.map = None  # 地图
        self.scenario_info = None  # 想定信息
        self.map_data = None  # 地图信息
        self.seat = None  # 席位
        self.faction = None
        self.role = None  # 角色
        self.controllable_ops = None
        self.team_info = None  # 队伍信息
        self.my_direction = None  # 我的方向
        self.my_mission = None  # 我的任务
        self.user_name = None  # 用户名
        self.user_id = None  # 用户id
        self.history = None  # 历史

    def setup(self, setup_info):#定义设置函数
        self.scenario = setup_info["scenario"]#传入参数 想定
        self.state = setup_info["state"]#传入
        self.color = setup_info["faction"]#传入颜色
        self.faction = setup_info["faction"]
        self.seat = setup_info["seat"]#传入席位
        self.role = setup_info["role"]#传入角色
        self.user_name = setup_info["user_name"]#传入用户名
        self.user_id = setup_info["user_id"]#传入用户id
        self.priority = {#定义优先级
            ActionType.Occupy: self.gen_occupy,#占据
            ActionType.Shoot: self.gen_shoot,#射击
            ActionType.GuideShoot: self.gen_guide_shoot,#引导射击
            ActionType.JMPlan: self.gen_jm_plan,#间瞄
            ActionType.GetOn: self.gen_get_on,#上车
            ActionType.GetOff: self.gen_get_off,#下车
            ActionType.ChangeState: self.gen_change_state,#改变状态
            ActionType.RemoveKeep: self.gen_remove_keep,#移除压制
            ActionType.Move: self.gen_move, #移动
            ActionType.StopMove: self.gen_stop_move,#停止
            ActionType.WeaponLock: self.gen_WeaponLock,#武器锁定
            ActionType.WeaponUnFold: self.gen_WeaponUnFold,#武器解锁
            ActionType.CancelJMPlan: self.gen_cancel_JM_plan#取消间瞄
        }  # choose action by priority
        self.observation = None #设置参数为空
        self.map = Map(setup_info["scenario"])  # 传入想定号对应的地图
        self.map_data = self.map.get_map_data()#得到地图信息

    def command(self, observation):
        self.team_info = observation["role_and_grouping_info"]
        return self.gen_grouping_info(observation) + self.gen_battle_direction_info(observation) + self.gen_battle_mission_info(observation)

    def deploy(self, observation):#定义部署函数 参数为observation
        self.team_info = observation["role_and_grouping_info"]#给队伍信息赋值
        self.controllable_ops = observation["role_and_grouping_info"][self.seat]["operators"]#??
        communications = observation["communication"]#群队级任务分配
        for command in communications:#遍历
            if command["info"]["company_id"] == self.seat:#如果席位值=信息中的队伍id
                if command["type"] == 200:#如果类型=200 下达作战任务
                    self.my_mission = command
                elif command["type"] == 201:#如果类型=201 下达作战方向
                    self.my_direction = command
        actions = []#把动作定义为空列表
        for item in observation["operators"]:#在算子属性中遍历
            if item["obj_id"] in self.controllable_ops:#如果算子id在可控算子中
                operator = item #赋值
                if operator["sub_type"] == 2 or operator["sub_type"] == 4:#如果类型为人员2/无人战车4
                    actions.append({ #增加动作
                        "actor": self.seat, #动作发出者席位
                        "obj_id": operator["obj_id"],
                        "type": 303,#部署上车
                        "target_obj_id": operator["launcher"]#车辆算子ID
                    })
        return actions #通过调用deploy来返回战前部署动作列表

    def reset(self):#重置函数
        self.scenario = None #想定为空
        self.color = None #颜色
        self.priority = None#优先级
        self.observation = None
        self.map = None #地图
        self.scenario_info = None #想定信息为空
        self.map_data = None #地图信息为空

    def step(self, observation: dict): #step函数传入的参数是对局的态势信息,输出的则是agent的动作列表。
        self.observation = observation  # 传入态势数据save observation for later use
        self.team_info = observation["role_and_grouping_info"] #保留队伍信息
        if observation["role_and_grouping_info"]:
            self.controllable_ops = observation["role_and_grouping_info"][self.seat]["operators"] #??
        communications = observation["communication"] #群队级下的任务分配
        for command in communications:
            if command["info"]["company_id"] == self.seat:
                if command["type"] == 200:#如果类型=200 下达作战任务
                    self.my_mission = command
                elif command["type"] == 201:#如果类型=200下达作战方向
                    self.my_direction = command
        total_actions = [] #用列表表示总操作
        # loop all bops and their valid actions
        for obj_id, valid_actions in observation['valid_actions'].items(): #获取合法算子中的key、value分别在 算子id和有效动作中遍历
            if obj_id not in self.controllable_ops: #？？保证算子在可控范围内
                continue
            for action_type in self.priority:  # 在优先级中遍历动作类型'dict' is order-preserving since Python 3.6
                if action_type not in valid_actions: #保证动作类型在有效动作中继续
                    continue
                # find the action generation method based on type
                gen_action = self.priority[action_type]#优先级中的动作类型赋值给gen_action
                action = gen_action(obj_id, valid_actions[action_type])
                if action:# #动作不为空
                    total_actions.append(action) #添加动作
                    break  # one action per bop at a time
        # if total_actions:
        #     print(
        #         f'{self.color} actions at step: {observation["time"]["cur_step"]}', end='\n\t')
        #     print(total_actions)
        return total_actions #返回总体动作

    def get_bop(self, obj_id): #根据id值返回整个算子的信息
        """Get bop in my observation based on its id."""
        for bop in self.observation['operators']:
            if obj_id == bop['obj_id']: #当输入的id和遍历的算子id相等时返回对应id值得信息
                return bop

    def gen_occupy(self, obj_id, candidate):
        """Generate occupy action."""
        return {
            'actor': self.seat,
            'obj_id': obj_id,
            'type': ActionType.Occupy,
        }

    def gen_shoot(self, obj_id, candidate):
        """Generate shoot action with the highest attack level."""
        best = max(candidate, key=lambda x: x['attack_level'])
        return {
            'actor': self.seat,
            'obj_id': obj_id,
            'type': ActionType.Shoot,
            'target_obj_id': best['target_obj_id'],#按照攻击大小排序后的target_id
            'weapon_id': best['weapon_id'], #按照攻击大小排序后的weapon_id
        }

    def gen_guide_shoot(self, obj_id, candidate):
        """Generate guide shoot action with the highest attack level."""
        best = max(candidate, key=lambda x: x['attack_level'])
        return {
            'actor': self.seat,
            'obj_id': obj_id,
            'type': ActionType.GuideShoot,
            'target_obj_id': best['target_obj_id'],
            'weapon_id': best['weapon_id'],
            'guided_obj_id': best['guided_obj_id'],
        }

    def gen_jm_plan(self, obj_id, candidate):
        """Generate jm plan action aimed at a random city."""
        weapon_id = random.choice(candidate)['weapon_id']
        jm_pos = random.choice([city['coord']
                                for city in self.observation['cities']])
        return {
            'actor': self.seat,
            'obj_id': obj_id,
            'type': ActionType.JMPlan,
            'jm_pos': jm_pos,
            'weapon_id': weapon_id,
        }

    def gen_get_on(self, obj_id, candidate):
        """Generate get on action with some probability."""
        get_on_prob = 0.5
        if random.random() < get_on_prob:
            target_obj_id = random.choice(candidate)['target_obj_id']
            return {
                'actor': self.seat,
                'obj_id': obj_id,
                'type': ActionType.GetOn,
                'target_obj_id': target_obj_id,
            }

    def gen_get_off(self, obj_id, candidate):
        """Generate get off action only if the bop is within some distance of a random city."""
        bop = self.get_bop(obj_id)
        destination = random.choice([city['coord']
                                     for city in self.observation['cities']])
        if bop and self.map.get_distance(bop['cur_hex'], destination) <= 10:
            target_obj_id = random.choice(candidate)['target_obj_id']
            return {
                'actor': self.seat,
                'obj_id': obj_id,
                'type': ActionType.GetOff,
                'target_obj_id': target_obj_id,
            }

    def gen_change_state(self, obj_id, candidate):
        """Generate change state action with some probability."""
        change_state_prob = 0.5
        if random.random() < change_state_prob:
            target_state = random.choice(candidate)['target_state']
            return {
                'actor': self.seat,
                'obj_id': obj_id,
                'type': ActionType.ChangeState,
                'target_state': target_state,
            }

    def gen_remove_keep(self, obj_id, candidate):
        """Generate remove keep action with some probability."""
        remove_keep_prob = 0.5
        if random.random() < remove_keep_prob:
            return {
                'actor': self.seat,
                'obj_id': obj_id,
                'type': ActionType.RemoveKeep,
            }

    def gen_move(self, obj_id, candidate): #停止移动，可以有返回也可以没有返回
        """Generate move action to a random city."""
        bop = self.get_bop(obj_id) #根据id值返回整个算子的信息
        if bop['sub_type'] == 3:
            return
        destination = random.choice([city['coord'] #随机的返回一个夺控点的坐标
                                     for city in self.observation['cities']])
        if self.my_direction:
            destination = self.my_direction["info"]["target_pos"]
        if bop and bop['cur_hex'] != destination: #当bop为none与当前坐标与目标坐标相同时不执行
            move_type = self.get_move_type(bop) #获取移动类型
            route = self.map.gen_move_route( #根据当前与目标坐标生成路线
                bop['cur_hex'], destination, move_type)
            return {
                'actor': self.seat,
                'obj_id': obj_id,
                'type': ActionType.Move,
                'move_path': route,
            }

    def get_move_type(self, bop):
        """Get appropriate move type for a bop."""
        bop_type = bop['type']
        if bop_type == BopType.Vehicle:
            if bop['move_state'] == MoveType.March:
                move_type = MoveType.March
            else:
                move_type = MoveType.Maneuver
        elif bop_type == BopType.Infantry:
            move_type = MoveType.Walk
        else:
            move_type = MoveType.Fly
        return move_type

    def gen_stop_move(self, obj_id, candidate): #停止移动，可以有返回也可以没有返回发给
        """Generate stop move action only if the bop is within some distance of a random city.

        High probability for the bop with passengers and low for others.
        """
        bop = self.get_bop(obj_id) #根据id值返回整个算子的信息
        destination = random.choice([city['coord'] 
                                     for city in self.observation['cities']])
        if self.map.get_distance(bop['cur_hex'], destination) <= 10: #当前坐标与目的坐标距离<=10，进行判断，否则没有返回值
            stop_move_prob = 0.9 if bop['passenger_ids'] else 0.01 #当前坐标与目的坐标距离<=10，进行判断，否则没有返回值
            if random.random() < stop_move_prob:
                return {
                    'actor': self.seat,
                    'obj_id': obj_id,
                    'type': ActionType.StopMove,
                }

    def gen_WeaponLock(self, obj_id, candidate):
        bop = self.get_bop(obj_id)
        prob_weaponlock = 0.1
        if max(self.map_data[bop['cur_hex'] // 100][bop['cur_hex'] % 100]["roads"]) > 0 or random.random() < prob_weaponlock:
            return {
                'actor': self.seat,
                "obj_id": obj_id,
                "type": ActionType.WeaponLock
            }

    def gen_WeaponUnFold(self, obj_id, candidate):
        bop = self.get_bop(obj_id)
        destination = random.choice([city['coord']
                                     for city in self.observation['cities']])
        if self.map.get_distance(bop['cur_hex'], destination) <= 10:
            return {
                'actor': self.seat,
                "obj_id": obj_id,
                "type": ActionType.WeaponUnFold
            }

    def gen_cancel_JM_plan(self, obj_id, candidate):
        cancel_prob = 0.1
        if random.random() > cancel_prob:
            return {
                'actor': self.seat,
                "obj_id": obj_id,
                "type": ActionType.CancelJMPlan
            }

    def gen_grouping_info(self, observation):
        def partition(lst, n):
            return [lst[i::n] for i in range(n)]
        operator_ids = []
        for operator in observation["operators"] + observation["passengers"]:
            if operator["color"] == self.color:
                operator_ids.append(operator["obj_id"])
        lists_of_ops = partition(operator_ids, len(self.team_info.keys()))
        grouping_info = {
            "actor": self.seat,
            "type": 100
        }
        info = {}
        for teammate_id in self.team_info.keys():
            info[teammate_id] = {"operators": lists_of_ops.pop()}
        grouping_info["info"] = info
        return [grouping_info]

    def gen_battle_direction_info(self, observation):
        direction_info = []
        for teammate_id in self.team_info.keys():
            direction = {
                "actor": self.seat,
                "type": 201,
                "info": {
                    "company_id": teammate_id,
                    "target_pos": random.choice(observation["cities"])["coord"],
                    "start_time": 0,
                    "end_time": 1800
                }
            }
            direction_info.append(direction)
        return direction_info

    def gen_battle_mission_info(self, observation):
        mission_info = []
        for teammate_id in self.team_info.keys():
            mission = {
                "actor": self.seat,
                "type": 200,
                "info": {
                    "company_id": teammate_id,
                    "mission_type": random.randint(0, 2),
                    "target_pos":  random.choice(observation["cities"])["coord"],
                    "route": [random.randint(0, 9000), random.randint(0, 9000), random.randint(0, 9000)],
                    "start_time": 0,
                    "end_time": 1800
                }
            }
            mission_info.append(mission)
        return mission_info
