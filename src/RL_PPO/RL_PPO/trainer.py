"""Training Node for PPO Navigation."""

import rclpy
from rclpy.node import Node
import numpy as np
import os
from datetime import datetime
from ament_index_python.packages import get_package_share_directory

from RL_PPO.ppo_agent import PPOAgent
from RL_PPO.navigation_env import NavigationEnv


class PPOTrainer(Node):
    """PPO Training Node."""
    
    def __init__(self):
        super().__init__('ppo_trainer')
        
        self.declare_parameters(
            namespace='',
            parameters=[
                ('total_episodes', 1000),
                ('max_steps_per_episode', 500),
                ('batch_size', 64),
                ('update_epochs', 10),
                ('save_interval', 100),
                ('use_real_ros', False),
            ]
        )
        
        self.total_episodes = self.get_parameter('total_episodes').value
        self.max_steps = self.get_parameter('max_steps_per_episode').value
        self.batch_size = self.get_parameter('batch_size').value
        self.update_epochs = self.get_parameter('update_epochs').value
        self.save_interval = self.get_parameter('save_interval').value
        
        # Check if we should use real ROS 2/Gazebo environment
        use_real_ros = self.get_parameter('use_real_ros').value
        
        self.env = NavigationEnv(max_steps=self.max_steps, use_real_ros=use_real_ros)
        state_dim = self.env.get_state_dim()
        action_dim = self.env.action_dim
        
        if use_real_ros:
            self.get_logger().info('Using REAL ROS 2 / Gazebo environment!')
            self.get_logger().info('Make sure Gazebo is running with test.world')
        
        self.agent = PPOAgent(state_dim, action_dim)
        
        pkg_share = get_package_share_directory('RL_PPO')
        self.model_dir = os.path.join(pkg_share, 'models')
        self.logs_dir = os.path.join(pkg_share, 'logs')
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        self.episode_rewards = []
        self.episode_lengths = []
        self.episode_losses = []
        self.best_reward = -float('inf')
        
        self.get_logger().info('PPO Trainer initialized')
        self.get_logger().info(f'State dim: {state_dim}, Action dim: {action_dim}')
        self.get_logger().info(f'Device: {self.agent.device}')
    
    def compute_gae(self, rewards, values, dones, last_state, gamma=0.99, lam=0.95):
        """Compute Generalized Advantage Estimation (GAE)."""
        returns = []
        advantages = []
        
        # Get last value
        if dones[-1]:
            last_value = 0
        else:
            _, _, last_value = self.agent.get_action_and_value(last_state)
        
        gae = 0
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = last_value
            else:
                next_value = values[t + 1]
            
            delta = rewards[t] + gamma * next_value * (1 - dones[t]) - values[t]
            gae = delta + gamma * lam * (1 - dones[t]) * gae
            advantages.insert(0, gae)
            returns.insert(0, gae + values[t])
        
        return np.array(returns), np.array(advantages)
    
    def train(self):
        self.get_logger().info('Starting training...')
        
        for episode in range(self.total_episodes):
            state, _ = self.env.reset()
            episode_reward = 0
            
            states, actions, log_probs, rewards, values, dones = [], [], [], [], [], []
            
            for step in range(self.max_steps):
                action, log_prob, value = self.agent.get_action_and_value(state)
                next_state, reward, done, truncated, info = self.env.step(action)
                
                states.append(state)
                actions.append(action)
                log_probs.append(log_prob)
                rewards.append(reward)
                values.append(value)
                dones.append(done)
                
                episode_reward += reward
                state = next_state
                
                if done:
                    break
            
            # Compute returns and advantages using GAE
            returns, advantages = self.compute_gae(rewards, values, dones, state)
            
            states = np.array(states)
            actions = np.array(actions)
            log_probs = np.array(log_probs)
            returns = np.array(returns)
            advantages = np.array(advantages)
            
            # Only update if we have enough data
            if len(states) >= 4:
                total_loss = 0
                valid_updates = 0
                for _ in range(self.update_epochs):
                    loss = self.agent.update(states, actions, log_probs, returns, advantages)
                    if not np.isnan(loss) and not np.isinf(loss):
                        total_loss += loss
                        valid_updates += 1
                avg_loss = total_loss / max(valid_updates, 1)
            else:
                avg_loss = 0
                self.get_logger().warn(f'Episode {episode + 1} too short ({len(states)} steps), skipping update')
            
            self.episode_rewards.append(episode_reward)
            self.episode_lengths.append(step + 1)
            self.episode_losses.append(avg_loss)
            
            if (episode + 1) % 10 == 0:
                self.get_logger().info(
                    f'Episode {episode + 1}/{self.total_episodes}, '
                    f'Reward: {episode_reward:.2f}, '
                    f'Steps: {step + 1}, '
                    f'Loss: {avg_loss:.4f}'
                )
            
            # Save best model
            if episode_reward > self.best_reward:
                self.best_reward = episode_reward
                best_model_path = os.path.join(self.model_dir, 'ppo_model_best.pt')
                self.agent.save(best_model_path)
                self.get_logger().info(f'New best model saved! Reward: {episode_reward:.2f}')
            
            if (episode + 1) % self.save_interval == 0:
                model_path = os.path.join(
                    self.model_dir, 
                    f'ppo_model_ep{episode + 1}.pt'
                )
                self.agent.save(model_path)
                self.save_plots()
                self.get_logger().info(f'Model and plots saved to {self.logs_dir}')
        
        final_model_path = os.path.join(self.model_dir, 'ppo_model_final.pt')
        self.agent.save(final_model_path)
        self.save_plots()
        self.get_logger().info(f'Final model saved to {final_model_path}')
        self.get_logger().info(f'Training plots saved to {self.logs_dir}')
        self.get_logger().info('Training completed!')
    
    def save_plots(self):
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
        except ImportError as e:
            self.get_logger().warn(f'Failed to import matplotlib: {e}')
            self.get_logger().warn('Skipping plot generation')
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        axes[0, 0].plot(self.episode_rewards)
        axes[0, 0].set_title('Episode Rewards')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Total Reward')
        axes[0, 0].grid(True, alpha=0.3)
        
        window_size = min(50, len(self.episode_rewards))
        if window_size > 1:
            rewards_smooth = np.convolve(self.episode_rewards, np.ones(window_size)/window_size, mode='valid')
            axes[0, 0].plot(range(window_size-1, len(self.episode_rewards)), rewards_smooth, 'r-', linewidth=2, label=f'Moving Avg ({window_size})')
            axes[0, 0].legend()
        
        axes[0, 1].plot(self.episode_lengths)
        axes[0, 1].set_title('Episode Lengths')
        axes[0, 1].set_xlabel('Episode')
        axes[0, 1].set_ylabel('Steps')
        axes[0, 1].grid(True, alpha=0.3)
        
        axes[1, 0].plot(self.episode_losses)
        axes[1, 0].set_title('Training Loss')
        axes[1, 0].set_xlabel('Episode')
        axes[1, 0].set_ylabel('Loss')
        axes[1, 0].grid(True, alpha=0.3)
        
        rewards_bins = np.histogram(self.episode_rewards, bins=30)
        axes[1, 1].hist(self.episode_rewards, bins=30, edgecolor='black', alpha=0.7)
        axes[1, 1].axvline(np.mean(self.episode_rewards), color='r', linestyle='--', linewidth=2, label=f'Mean: {np.mean(self.episode_rewards):.2f}')
        axes[1, 1].set_title('Reward Distribution')
        axes[1, 1].set_xlabel('Total Reward')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        plot_path = os.path.join(self.logs_dir, f'training_plot_{timestamp}.png')
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        np.save(os.path.join(self.logs_dir, f'training_data_{timestamp}.npy'), {
            'rewards': self.episode_rewards,
            'lengths': self.episode_lengths,
            'losses': self.episode_losses
        })
        
        self.get_logger().info(f'Plots saved to {plot_path}')


def main(args=None):
    rclpy.init(args=args)
    trainer = PPOTrainer()
    trainer.train()
    trainer.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()