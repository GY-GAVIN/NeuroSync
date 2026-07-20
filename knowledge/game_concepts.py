"""
Stratego 弈策 — 《策略博弈》(Games of Strategy, Dixit & Skeath) 知识模板

这些模板在任务创建时通过 f-string 注入到 task description 中，
为 Agent 提供博弈论核心概念框架，而非通过 RAG 运行时检索。
"""

GAME_CLASSIFICATION = """
## 博弈分类框架（来自《策略博弈》Dixit & Skeath）

### 核心维度
1. **同时行动 vs 顺序行动** (Simultaneous vs Sequential)
   - 同时：参与者不知道对方的选择时做决策
   - 顺序：一方先行动，另一方观察后行动

2. **完全信息 vs 不完全信息** (Complete vs Incomplete Information)
   - 完全：所有参与者知道彼此的收益函数和策略空间
   - 不完全：至少一方不知道对方的收益或类型

3. **一次博弈 vs 重复博弈** (One-shot vs Repeated)
   - 一次：博弈只进行一次，没有未来互动
   - 重复：相同结构重复多次，声誉和报复成为因素

4. **零和 vs 非零和** (Zero-sum vs Non-zero-sum)
   - 零和：一方的收益恰好是另一方的损失
   - 非零和：双方可以同时获益或同时受损

5. **合作博弈 vs 非合作博弈** (Cooperative vs Non-cooperative)
   - 合作：参与者可以达成有约束力的协议
   - 非合作：没有外部强制力，只能依靠自利行为

### 经典博弈类型
- **囚徒困境 (Prisoner's Dilemma)**: 个人理性 → 集体非理性
- **斗鸡博弈 (Chicken/Snowdrift)**: 谁先退让？双方都想硬撑
- **猎鹿博弈 (Stag Hunt)**: 协调风险——信任与合作
- **性别战 (Battle of the Sexes)**: 协调中带有利益冲突
- **协调博弈 (Coordination)**: 纯协调 vs 利益冲突协调
- **最后通牒博弈 (Ultimatum Game)**: 提议 vs 回应，公平与报复
- **鹰鸽博弈 (Hawk-Dove)**: 冲突升级与妥协
"""

EQUILIBRIUM_CONCEPTS = """
## 均衡分析框架（来自《策略博弈》）

### Nash 均衡 (Nash Equilibrium)
每个参与者的策略都是对其他人策略的最佳回应。
没有人可以通过单方面改变自己的策略来获得更高的收益。
```
数学：对于每个参与者 i，策略 s_i* 满足：
u_i(s_i*, s_{-i}*) ≥ u_i(s_i, s_{-i}*) 对所有 s_i 成立
```

### 占优策略 (Dominant Strategy)
- **严格占优**: 无论对方选什么，该策略严格优于其他所有策略
- **弱占优**: 无论对方选什么，该策略至少不差于其他策略，且至少严格优于一次
- **严格劣策略**: 无论对方选什么，该策略都严格更差（应被迭代剔除）

### 混合策略 Nash 均衡 (Mixed Strategy Nash Equilibrium)
当纯策略 Nash 均衡不存在时，参与者以概率分布随机选择策略。
计算方法：使对方在每个纯策略上的期望收益相等。
```
对于 2×2 博弈：p = (d2-c2) / (a2-b2-c2+d2)
其中收益矩阵为 [a1,a2] [b1,b2]
                [c1,c2] [d1,d2]
```

### 子博弈完美 Nash 均衡 (Subgame Perfect Nash Equilibrium)
对顺序博弈使用 **逆向归纳 (Backward Induction)**：
从最后一个决策节点开始，逐步向前推导最优行动。
每个子博弈上的策略组合都构成 Nash 均衡。

### Pareto 最优 (Pareto Optimal)
无法让任何一方变得更好而不损害另一方的结果状态。
- Pareto 改进：至少让一方变得更好而不损害任何其他方
- Pareto 前沿：所有 Pareto 最优结果的集合

### Minimax 定理
在零和博弈中，每个参与者都可以通过混合策略保证一个确定的期望收益。
"""

BEHAVIORAL_CONSIDERATIONS = """
## 行为博弈论视角 (Behavioral Game Theory)

真实人类系统性地偏离完全理性均衡：

1. **公平偏好 (Fairness)**
   - 人们宁可自己受损也要惩罚不公平行为（最后通牒博弈）
   - 参考《策略博弈》第 12 章：公平与心理学

2. **互惠性 (Reciprocity)**
   - 以牙还牙、以德报德——重复博弈中最强大的策略
   - 正向互惠和负向互惠都是人类本能

3. **有限理性 (Bounded Rationality)**
   - 人类无法总是做出完整的博弈树分析
   - 使用启发式（heuristics）和简化策略

4. **损失厌恶 (Loss Aversion)**
   - 损失带来的痛苦 > 同等收益带来的快乐（约 2 倍）
   - 前景理论 (Prospect Theory) 的 S 型价值函数

5. **过度自信 (Overconfidence)**
   - 高估自己的能力和成功概率（>50% 的人认为自己在平均水平之上）
   - 影响对对手策略的判断

6. **框架效应 (Framing Effect)**
   - 问题表述方式显著影响决策
   - 合作框架 vs 竞争框架导致不同结果
"""

STRATEGY_ADVICE = """
## 策略建议框架（来自《策略博弈》）

### 承诺策略 (Commitment)
- **可置信承诺**: 烧桥（burning bridges）使背叛/退出变得不可能
- **不可置信的威胁**: 理性人不会执行时就不构成威慑
- **如何让威胁可置信**: 合同、抵押、声誉、分步投入

### 信号传递 (Signaling)
- **高成本信号**: 昂贵但可信（如名校学历、豪华广告）
- **低成本信号**: 便宜但需要绑定声誉（如口头承诺）
- **分离均衡**: 不同类型发送不同信号
- **混同均衡**: 所有类型发送相同信号

### 重复博弈策略 (Repeated Games)
- **以牙还牙 (Tit-for-Tat)**: 第1轮合作，之后复制对方上一轮行动
- **冷酷触发 (Grim Trigger)**: 一旦对方背叛，永远不再合作
- **宽恕的以牙还牙 (Generous TFT)**: 以一定概率原谅背叛
- **赢-留、输-变 (Win-Stay Lose-Shift)**: 成功则重复，失败则改变

### BATNA (Best Alternative to a Negotiated Agreement)
- 谈判中的最佳替代方案决定了你的保留价格
- BATNA 越强，谈判地位越高
- 如何提高 BATNA：寻找外部选项、建立联盟、改善退路

### 策略行动 (Strategic Moves)
- **无条件行动**: 在对方行动前承诺自己的选择
- **威胁**: 如果对方做 X，我就做 Y（惩罚性）
- **承诺**: 无论对方做什么，我都做 Z（单边性）
- **恐吓**: 如果对方做 X，我就不得不做 Y（被动式）

### 博弈改变策略
- 改变收益结构：引入奖励/惩罚机制
- 改变信息结构：增加透明度或创造模糊性
- 改变参与者：引入第三方或退出博弈
- 改变时间结构：将一次性博弈转化为长期关系
"""

KNOWLEDGE_MAP = {
    "modeler": [GAME_CLASSIFICATION],
    "analyst": [EQUILIBRIUM_CONCEPTS, GAME_CLASSIFICATION],
    "advisor": [BEHAVIORAL_CONSIDERATIONS, STRATEGY_ADVICE, EQUILIBRIUM_CONCEPTS],
}
