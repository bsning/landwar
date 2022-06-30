import time #导入时间

from ai.agent import Agent #导入基类
from core.env.train_env import TrainEnv #导入定义的类

RED, BLUE, GREEN = 0, 1, -1 #红、蓝、绿方设置为0、1、-1
SCENARIOS = [2010431153]  #  # 设定场景号
NUM_GAMES = 1  # 游戏数量为1


def run_in_single_agent_mode():#单agent模式
    """
    run demo in single agent mode
    """
    print("Running in single agent mode.")#输出 运行单agent模式
    # instantiate agents and env
    red1 = Agent() #实例化红方
    blue1 = Agent() #实例化蓝方
    env1 = TrainEnv() ##实例化环境
    for scenario in SCENARIOS:#场景号中遍历场景
        for i in range(NUM_GAMES):#循环
            begin = time.time()#设定开始时间
            game_id = f"{time.strftime('%Y-%m-%d-%H-%M-%S')}_{scenario}_{i}"#游戏id=开始时间-场景号-序号


            # setup everything
            state = env1.setup({"scenario": scenario})#根据想定初始化状态
            print("Environment is ready.")#输出 环境准备完毕
            red1.setup(##红方初始化
                {
                    "scenario": scenario,#想定
                    "seat": 1,#席位：1
                    "faction": 0,#阵营id 红方为0
                    "role": 0,#角色 0为连长
                    "user_name": "demo", #用户名：
                    "user_id": 0, #用户id:demo
                    "state": state, #状态
                }
            )
            blue1.setup(#蓝方初始化
                {
                    "scenario": scenario,
                    "state": state,
                    "seat": 11,#??
                    "faction": 1,#阵营id 蓝方为1
                    "role": 0,
                    "user_name": "demo",
                    "user_id": 0,
                }
            )
            print("Agents are ready.")#输出

            # env gets player_info, mandatory
            player_info = gen_player_info(red1, blue1)#把红蓝方的信息赋值给玩家
            state, done = env1.env_config([player_info])#根据获取的玩家信息初始化状态

            # agents generate deploy actions
            deployment_actions = red1.deploy(observation=state[RED])#环境获取红方的部署信息
            deployment_actions += blue1.deploy(observation=state[BLUE])#环境获取蓝方的部署信息
            # env handle deployments actions, optional
            state, done = env1.env_config(deployment_actions)#把环境信息中的动作分别赋值给 state和done

            # loop until the end of game
            print("Step...")
            while not done:#没结束时
                actions = red1.step(state[RED])#动作为空列表
                actions += blue1.step(state[BLUE])#红方状态输入到动作中
                state, done = env1.step(actions)#蓝方状态输入到动作中

            env1.save_replay(game_id)
            env1.reset()#重置环境
            red1.reset()#重置红方
            blue1.reset()#重置蓝方
            print(f"Total time of {game_id}: {time.time() - begin:.3f}s")
        print(f"Finish scenario: {scenario}.")
    print("Finish all games.")


def gen_player_info(*args):#定义函数：获取玩家信息
    """
    generate player_info from agents
    """
    result = {} #返回值为字典
    result["type"] = 102 #?? 增加键值对 102:配置角色信息
    info = {} #信息 为字典
    result["info"] = info #增加键值对
    for arg in args:#遍历
        info[arg.seat] = {#??
            "faction": arg.faction,#阵营id
            "role": arg.role,#角色
            "user_id": arg.user_id,#用户id
            "user_name": arg.user_name,#用户名
        }
    return result #返回结果


def main():
    run_in_single_agent_mode()


if __name__ == "__main__":
    main()
