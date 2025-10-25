#DQLTrainingScript
import random, numpy as np, torch
import torch.nn as nn, torch.optim as optim
from collections import deque, namedtuple

# -------------------- CONFIG --------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
NUM_DECKS = 6
NUM_ACTIONS = 5  # HIT, STAND, DOUBLE, SPLIT, SURRENDER
ACTION_NAMES = ["HIT","STAND","DOUBLE","SPLIT","SURRENDER"]
COUNT_BINS = list(range(-5,6))  # True count bins
NUM_EPISODES = 500000
BATCH_SIZE = 256
REPLAY_CAPACITY = 200000
TARGET_UPDATE_STEPS = 2000
EPS_START = 1.0
EPS_END = 0.05
EPS_DECAY = 400000
GAMMA = 0.99
LR = 1e-4
MAX_STEPS_PER_EP = 200
SEED = 42
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)

# -------------------- SHOE & COUNT --------------------
def make_shoe(num_decks=NUM_DECKS):
    shoe=[]
    for _ in range(num_decks):
        for r in range(1,14):
            shoe.extend([min(r,10)]*4)
    random.shuffle(shoe)
    return deque(shoe)

def shoe_draw(shoe): return shoe.popleft()

def hi_lo_value(card):
    if 2<=card<=6: return 1
    if 7<=card<=9: return 0
    return -1

def true_count_bin_from_running(running_count, cards_remaining):
    decks_left = max(cards_remaining/52.0,0.25)
    tc = running_count/decks_left
    tc_round=int(round(tc))
    tc_round = max(min(tc_round, COUNT_BINS[-1]), COUNT_BINS[0])
    return tc_round + abs(COUNT_BINS[0])

# -------------------- HAND HELPERS --------------------
def hand_value(cards):
    total=sum(cards)
    usable_ace=(1 in cards and total+10<=21)
    if usable_ace: total+=10
    return total, usable_ace

def is_blackjack(cards): return len(cards)==2 and sum(cards)==11+1

def play_dealer(deck, shoe, running_count):
    total,_ = hand_value(deck)
    while total<17:
        c=shoe_draw(shoe)
        deck.append(c)
        running_count += hi_lo_value(c)
        total,_ = hand_value(deck)
    return total, running_count

# -------------------- OTHER PLAYERS --------------------
def conservative_strategy(cards):
    t,_=hand_value(cards); return 0 if t<12 else 1
def normal_strategy(cards):
    t,_=hand_value(cards); return 0 if t<17 else 1
def aggressive_strategy(cards):
    t,_=hand_value(cards); return 0 if t<19 else 1
PLAYER_TYPES = [conservative_strategy, normal_strategy, aggressive_strategy]

def play_fixed_player(cards, dealer_up, shoe, running_count, strat_fn):
    done=False
    while not done:
        a=strat_fn(cards)
        if a==0:
            c=shoe_draw(shoe)
            cards.append(c)
            running_count += hi_lo_value(c)
            t,_=hand_value(cards)
            if t>21: done=True
        else: done=True
    return hand_value(cards)[0], running_count

# -------------------- DQN --------------------
class DuelingMLP(nn.Module):
    def __init__(self,in_dim,out_dim):
        super().__init__()
        self.fc=nn.Sequential(nn.Linear(in_dim,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU())
        self.value=nn.Linear(128,1)
        self.adv=nn.Linear(128,out_dim)
    def forward(self,x):
        x=self.fc(x)
        v=self.value(x)
        a=self.adv(x)
        return v + (a-a.mean(dim=1,keepdim=True))

def encode_state_vec(cards,dealer_up,tc_idx):
    total,usable = hand_value(cards)
    total_clamped = min(max(total,4),21)
    return np.array([
        (total_clamped-4)/(21-4),
        1.0 if usable else 0.0,
        (dealer_up-1)/9.0,
        tc_idx/(len(COUNT_BINS)-1)
    ],dtype=np.float32)

Transition=namedtuple('Transition',('state','action','reward','next_state','done'))

class ReplayBuffer:
    def __init__(self,capacity): self.buffer=deque(maxlen=capacity)
    def push(self,*args): self.buffer.append(Transition(*args))
    def sample(self,batch_size):
        batch=random.sample(self.buffer,batch_size)
        return Transition(*zip(*batch))
    def __len__(self): return len(self.buffer)

# -------------------- AGENT STEP --------------------
def can_split_allowed(hand, can_split_flag):
    return can_split_flag and len(hand)==2 and hand[0]==hand[1]

def agent_step(hand,dealer_up,action,can_split,shoe,running_count):
    total,_=hand_value(hand)
    # SPLIT
    if action==3 and can_split_allowed(hand,can_split):
        c1=shoe_draw(shoe); running_count+=hi_lo_value(c1)
        c2=shoe_draw(shoe); running_count+=hi_lo_value(c2)
        return "split", [[hand[0],c1],[hand[1],c2]], running_count
    # HIT
    if action==0:
        c=shoe_draw(shoe); hand.append(c); running_count+=hi_lo_value(c)
        t,_=hand_value(hand)
        return hand,-1.0 if t>21 else None,t>21,running_count,1
    # STAND
    if action==1: return hand,None,True,running_count,1
    # DOUBLE
    if action==2:
        c=shoe_draw(shoe); hand.append(c); running_count+=hi_lo_value(c)
        return hand,None,True,running_count,2
    # SURRENDER
    if action==4: return hand,-0.5,True,running_count,1
    return hand,None,False,running_count,1

# -------------------- PLAY SINGLE HAND --------------------
def play_single_hand_dqn(policy_net,shoe,running_count,dealer_hand,hand,tc_idx,eps,can_split=True,depth=0):
    steps=0
    while True:
        steps+=1
        state_vec=encode_state_vec(hand,dealer_hand[0],tc_idx)
        if random.random()<eps: action=random.randrange(NUM_ACTIONS)
        else:
            with torch.no_grad():
                s=torch.tensor(state_vec,dtype=torch.float32,device=DEVICE).unsqueeze(0)
                q=policy_net(s).cpu().numpy()[0]
                action=int(np.argmax(q))
        res=agent_step(hand,dealer_hand[0],action,can_split,shoe,running_count)
        # SPLIT
        if isinstance(res[0],str) and res[0]=="split":
            subhands=res[1]; running_count=res[2]; total=0.0
            for sh in subhands:
                tc_idx=true_count_bin_from_running(running_count,len(shoe))
                rsub,running_count=play_single_hand_dqn(policy_net,shoe,running_count,dealer_hand,sh,tc_idx,eps,can_split=False,depth=depth+1)
                total+=rsub
            return total,running_count
        hand,reward_or_none,done,running_count,double_mult=res
        if done and reward_or_none is not None: return reward_or_none*double_mult,running_count
        if done and reward_or_none is None:
            dealer_total,running_count=play_dealer(list(dealer_hand),shoe,running_count)
            player_total,_=hand_value(hand)
            if is_blackjack(hand) and len(hand)==2: payoff=1.5*double_mult
            elif player_total>21: payoff=-1.0*double_mult
            elif dealer_total>21 or player_total>dealer_total: payoff=1.0*double_mult
            elif player_total==dealer_total: payoff=0.0
            else: payoff=-1.0*double_mult
            return payoff,running_count
        tc_idx=true_count_bin_from_running(running_count,len(shoe))
        if steps>MAX_STEPS_PER_EP: return 0.0,running_count

# -------------------- TRAINING --------------------
def train_and_export(num_episodes=NUM_EPISODES):
    state_dim=4
    policy_net=DuelingMLP(state_dim,NUM_ACTIONS).to(DEVICE)
    target_net=DuelingMLP(state_dim,NUM_ACTIONS).to(DEVICE)
    target_net.load_state_dict(policy_net.state_dict()); target_net.eval()
    optimizer=optim.Adam(policy_net.parameters(),lr=LR)
    replay=ReplayBuffer(REPLAY_CAPACITY)
    eps=EPS_START; step_count=0

    for ep in range(num_episodes):
        if ep%2000==0: print(f"Episode {ep}")
        shoe=make_shoe(); running_count=0
        dealer_hand=[shoe_draw(shoe),shoe_draw(shoe)]
        # play other players
        for strat_fn in PLAYER_TYPES:
            play_fixed_player([shoe_draw(shoe),shoe_draw(shoe)],dealer_hand[0],shoe,running_count,strat_fn)
        # agent
        player_hand=[shoe_draw(shoe),shoe_draw(shoe)]
        tc_idx=true_count_bin_from_running(running_count,len(shoe))
        reward,running_count=play_single_hand_dqn(policy_net,shoe,running_count,dealer_hand,player_hand,tc_idx,eps)
        # simple one-step transition storage
        state_vec=encode_state_vec(player_hand,dealer_hand[0],tc_idx)
        next_vec=state_vec.copy()
        replay.push(state_vec,0,reward,next_vec,True)
        # optimize
        if len(replay)>=BATCH_SIZE:
            batch=replay.sample(BATCH_SIZE)
            s=torch.tensor(batch.state,dtype=torch.float32,device=DEVICE)
            a=torch.tensor(batch.action,dtype=torch.long,device=DEVICE).unsqueeze(1)
            r=torch.tensor(batch.reward,dtype=torch.float32,device=DEVICE).unsqueeze(1)
            ns=torch.tensor(batch.next_state,dtype=torch.float32,device=DEVICE)
            done=torch.tensor(batch.done,dtype=torch.float32,device=DEVICE).unsqueeze(1)
            with torch.no_grad():
                target_val=r + GAMMA*(1-done)*target_net(ns).max(1,keepdim=True)[0]
            current_val=policy_net(s).gather(1,a)
            loss=nn.MSELoss()(current_val,target_val)
            optimizer.zero_grad(); loss.backward(); optimizer.step()
        eps=max(EPS_END, EPS_START-(EPS_START-EPS_END)*(ep/EPS_DECAY))
        step_count+=1
        if step_count%TARGET_UPDATE_STEPS==0: target_net.load_state_dict(policy_net.state_dict())

    # -------------------- EXPORT POLICY --------------------
    table_shape=(22,2,11) # player 4-21, usable ace, true count bin
    policy_table=np.zeros(table_shape,dtype=np.uint8)
    for pt in range(4,22):
        for ua in [0,1]:
            for tc in range(len(COUNT_BINS)):
                best_actions=[]
                for dealer in range(1,11):
                    hand=[pt-10 if ua else pt-2,2] # mock hand
                    state_vec=encode_state_vec(hand,dealer,tc)
                    with torch.no_grad():
                        s=torch.tensor(state_vec,dtype=torch.float32,device=DEVICE).unsqueeze(0)
                        q=policy_net(s).cpu().numpy()[0]
                        policy_table[pt,ua,tc]=np.argmax(q)
    # save files
    np.save("blackjack_policy.npy",policy_table)
    np.savetxt("blackjack_policy.csv",policy_table,fmt="%d",delimiter=",")
    with open("blackjack_policy.h","w") as f:
        f.write("const uint8_t blackjack_policy[22][2][11]={\n")
        for pt in range(22):
            f.write("  {")
            for ua in range(2):
                f.write("{"+",".join(str(int(policy_table[pt,ua,tc])) for tc in range(11))+"}")
                f.write("," if ua==0 else "")
            f.write("},\n")
        f.write("};\n")
    print("Training complete & policy exported!")

# -------------------- MAIN --------------------
if __name__=="__main__":
    train_and_export()
