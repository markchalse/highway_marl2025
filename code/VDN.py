
#Attention: If the following error occurs, try using the following solutions
#OMP: Error #15: Initializing libiomp5md.dll, but found libiomp5md.dll already initialized.
#OMP: Hint This means that multiple copies of the OpenMP runtime have been linked into the program. That is dangerous, since it can degrade performance or cause incorrect results. The best thing to do is to ensure that only a single OpenMP runtime is linked into the process, e.g. by avoiding static linking of the OpenMP runtime in any library. As an unsafe, unsupported, undocumented workaround you can set the environment variable KMP_DUPLICATE_LIB_OK=TRUE to allow the program to continue to execute, but that may cause crashes or silently produce incorrect results. For more information, please see http://www.intel.com/software/products/support/.
#import os
#os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


import gymnasium as gym
import highway_env
import numpy as np
import time
from torch.utils.tensorboard import SummaryWriter  # 导入 TensorBoard
from model import VDN,FlattenObs
# 初始化 TensorBoard
writer = SummaryWriter(log_dir="runs/VDN_experiment") # 日志保存到 runs/VDN_experiment 目录

if __name__ == "__main__":
    AGENTS_NUM = 3 #自动驾驶车辆数量
    env = gym.make('merge-multi-agent-v0', render_mode='human',
                   config={
                    "traffic_density": 999,
                    "controlled_vehicles":AGENTS_NUM,
                    "perception_distance":100
                    })
    env.reset()
    #print ('obs:',env.observation_space)
    # init dqn model
    vdn_model = VDN(state_size = 25, action_size=5)
    #vdn_model = VDN(state_size = 25, action_size=5, model_file_path='vdn.pth',use_epsilon=False)
    #vdn_model = VDN(state_size = 25, action_size=5, model_file_path='endpoint/vdn.pth.3-1',use_epsilon=False)
    # 训练循环
    for episode in range(800):
        print (f'episode {episode} begin')
        obs = env.reset()[0] #The first observation information extraction
        #obs = obs[0] #The first observation information extraction
        states=[FlattenObs(obs_i) for obs_i in obs]
        total_reward = 0
        for step in range(200):
            actions = [vdn_model.get_action(state) for state in states]
            next_obs, R, done, truncated, info = env.step(tuple(actions))
            rewards = info['agents_rewards']
            states_ = [FlattenObs(nextobs_i) for nextobs_i in next_obs]
            vdn_step_exp = []
            #print (done)
            #if done:
            #    print (rewards)
            for i in range(AGENTS_NUM):
                vdn_step_exp.append([states[i].tolist(), actions[i], rewards[i], states_[i].tolist(), bool(info['agents_dones'][i])])
            vdn_model.push_experience(vdn_step_exp)
            states = states_
            vdn_model.train()
            total_reward += sum(rewards)
            if done:
                break
            env.render()
        print (f'Episode total reward:{total_reward:.2f}')
        writer.add_scalar("Reward/Episode", total_reward, episode)
        vdn_model.epsilon_change()
        if episode%5==0:
            vdn_model.update_target_model()
            print (f'Epsilon change to {vdn_model.epsilon:.2f}')
            vdn_model.save_model('vdn.pth')
            print (f'Replay buffer size:{len(vdn_model.replay_buffer)}')
            
    writer.close() 
    env.close() 