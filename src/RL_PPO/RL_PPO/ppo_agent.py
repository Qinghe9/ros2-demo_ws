"""Proximal Policy Optimization (PPO) Agent Implementation."""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical


class ActorCritic(nn.Module):
    """Actor-Critic Network for PPO with LayerNorm for stability."""
    
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super(ActorCritic, self).__init__()
        
        # Actor network with LayerNorm
        self.actor_fc1 = nn.Linear(state_dim, hidden_dim)
        self.actor_ln1 = nn.LayerNorm(hidden_dim)
        self.actor_fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.actor_ln2 = nn.LayerNorm(hidden_dim)
        self.actor_out = nn.Linear(hidden_dim, action_dim)
        
        # Critic network with LayerNorm
        self.critic_fc1 = nn.Linear(state_dim, hidden_dim)
        self.critic_ln1 = nn.LayerNorm(hidden_dim)
        self.critic_fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.critic_ln2 = nn.LayerNorm(hidden_dim)
        self.critic_out = nn.Linear(hidden_dim, 1)
        
        # Initialize weights with smaller values
        self._init_weights()
        
    def _init_weights(self):
        """Initialize weights with orthogonal initialization."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.orthogonal_(m.weight, gain=np.sqrt(2))
                nn.init.constant_(m.bias, 0)
        
    def forward(self, state):
        # Actor forward
        x = F.tanh(self.actor_ln1(self.actor_fc1(state)))
        x = F.tanh(self.actor_ln2(self.actor_fc2(x)))
        action_logits = self.actor_out(x)
        
        # Critic forward
        v = F.tanh(self.critic_ln1(self.critic_fc1(state)))
        v = F.tanh(self.critic_ln2(self.critic_fc2(v)))
        value = self.critic_out(v)
        
        return action_logits, value
    
    def get_action(self, state, deterministic=False):
        action_logits, _ = self.forward(state)
        action_probs = F.softmax(action_logits, dim=-1)
        if deterministic:
            return torch.argmax(action_probs, dim=-1)
        dist = Categorical(action_probs)
        return dist.sample()
    
    def get_action_log_probs(self, state):
        action_logits, _ = self.forward(state)
        action_probs = F.softmax(action_logits, dim=-1)
        dist = Categorical(action_probs)
        return dist


class PPOAgent:
    """PPO Agent for Navigation with improved stability."""
    
    def __init__(self, state_dim, action_dim, lr=3e-4, gamma=0.99, 
                 epsilon_clip=0.2, c1=0.5, c2=0.01, max_grad_norm=0.5,
                 use_lr_scheduler=True, entropy_decay=0.995):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon_clip = epsilon_clip
        self.c1 = c1  # Value loss coefficient
        self.c2 = c2  # Entropy coefficient (initial)
        self.max_grad_norm = max_grad_norm
        self.entropy_decay = entropy_decay
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.policy = ActorCritic(state_dim, action_dim).to(self.device)
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=lr, eps=1e-5)
        
        # Learning rate scheduler
        if use_lr_scheduler:
            self.scheduler = torch.optim.lr_scheduler.StepLR(
                self.optimizer, step_size=100, gamma=0.9
            )
        else:
            self.scheduler = None
        
        self.update_count = 0
        
    def select_action(self, state, deterministic=False):
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            action = self.policy.get_action(state_tensor, deterministic)
        return action.cpu().numpy()[0]
    
    def get_action_and_value(self, state):
        # Ensure state is a numpy array and normalize
        if isinstance(state, list):
            state = np.array(state, dtype=np.float32)
        # Normalize state to prevent extreme values
        state = np.clip(state, -10, 10)
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            action_logits, value = self.policy(state_tensor)
            # Clip logits for numerical stability
            action_logits = torch.clamp(action_logits, -10, 10)
            action_probs = F.softmax(action_logits, dim=-1)
            # Ensure no zero probabilities
            action_probs = torch.clamp(action_probs, 1e-8, 1.0)
            action_probs = action_probs / action_probs.sum(dim=-1, keepdim=True)
            dist = Categorical(action_probs)
            action = dist.sample()
            log_prob = dist.log_prob(action)
        return action.cpu().numpy()[0], log_prob.cpu().numpy()[0], value.cpu().numpy()[0]
    
    def update(self, states, actions, old_log_probs, returns, advantages):
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        old_log_probs = torch.FloatTensor(old_log_probs).to(self.device)
        returns = torch.FloatTensor(returns).to(self.device)
        advantages = torch.FloatTensor(advantages).to(self.device)
        
        # Normalize advantages only if we have more than one sample
        if len(advantages) > 1:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        else:
            # For single sample, just zero-center
            advantages = advantages - advantages.mean()
        
        for _ in range(10):
            action_probs, values = self.policy(states)
            # Add numerical stability with clamp and prevent overflow
            action_probs = torch.clamp(action_probs, -100, 100)
            # Use log_softmax for better numerical stability
            logits = F.log_softmax(action_probs, dim=-1)
            # Convert to probabilities while ensuring numerical stability
            probs = torch.exp(logits)
            # Ensure probabilities sum to 1 and no nans
            probs = torch.clamp(probs, 1e-10, 1 - 1e-10)
            probs = probs / probs.sum(dim=-1, keepdim=True)
            # Create distribution
            dist = Categorical(probs)
            log_probs = dist.log_prob(actions)
            # Flatten log_probs and old_log_probs to ensure same shape
            log_probs = log_probs.view(-1)
            old_log_probs = old_log_probs.view(-1)
            entropy = dist.entropy().mean()
            
            ratios = torch.exp(log_probs - old_log_probs)
            
            # Ensure all tensors have the same shape
            ratios = ratios.view(-1)
            advantages = advantages.view(-1)
            
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1 - self.epsilon_clip, 1 + self.epsilon_clip) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()
            
            # Value loss with proper shape handling - ensure both are 1D
            values = values.view(-1)  # Flatten to [batch_size]
            returns = returns.view(-1)  # Flatten to [batch_size]
            
            # Ensure same shape
            if values.shape[0] != returns.shape[0]:
                min_len = min(values.shape[0], returns.shape[0])
                values = values[:min_len]
                returns = returns[:min_len]
            
            value_loss = F.mse_loss(values, returns)
            
            loss = policy_loss + self.c1 * value_loss - self.c2 * entropy
            
            self.optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
            self.optimizer.step()
        
        return loss.item()
    
    def save(self, path):
        torch.save(self.policy.state_dict(), path)
    
    def load(self, path):
        self.policy.load_state_dict(torch.load(path, map_location=self.device))
        self.policy.eval()