# Baby Sleep — 哄宝宝睡觉游戏设计文档

**日期：** 2026-04-08
**平台：** Web 浏览器（H5），可扩展至微信小程序 / App
**引擎：** Cocos Creator 3.x + TypeScript
**存档：** localStorage（纯本地，无需后端）

---

## 一、项目概述

一款休闲反应力游戏。宝宝躺在床上准备入睡，玩家需要及时处理房间内随机发生的干扰事件（手机响铃、窗户吹风、蚊子飞入等），防止宝宝被吵醒。游戏共15关：前10关为普通房间场景，后5关进入宝宝梦境，面对抽象的梦幻干扰。

**游戏类型：** 本质上是一个 **Whack-a-Mole（打地鼠）变体** + **反应力/注意力管理**游戏。随机事件在场景中弹出，玩家需在限定时间内响应处理，多个事件并发时需要优先级判断。与传统打地鼠的区别在于：交互方式更丰富（点击/长按/拖拽/组合），事件有不同惩罚权重，玩家需要策略性地优先处理高惩罚事件。

**核心主题：** 点击/长按/拖拽响应随机事件，保持"安睡度"不降为零。

---

## 二、核心玩法机制

### 游戏循环

```
关卡开始 → 安睡度 100，倒计时启动
    │
    ├─ 随机事件触发（手机响铃、窗户吹风……）
    │   ├─ 玩家在时间窗口内处理成功 → 安睡度轻微降低或不变
    │   └─ 玩家超时未处理 → 安睡度大幅下降
    │
    ├─ 安睡度 <= 0 → 宝宝哭醒 → 关卡失败
    └─ 倒计时结束且安睡度 > 0 → 宝宝睡着 → 关卡通过
```

### 安睡度机制

| 情况 | 安睡度变化 |
|------|---------|
| 初始值 | 100 |
| 事件超时未处理 | -15 ~ -30（根据事件难度） |
| 事件成功处理 | 0 ~ -5（高难事件仍有轻微惊扰） |
| 安睡度 <= 0 | 关卡失败 |

### 三星评价

| 星级 | 条件 |
|------|------|
| 1星 | 通关时安睡度 > 0 |
| 2星 | 通关时安睡度 >= 50 |
| 3星 | 通关时安睡度 >= 80 |

### 关卡解锁规则

- 第1关默认解锁
- 第 N+1 关需第 N 关至少 1 星通关
- 第11关（梦境入口）需第10关至少 2 星通关

### 交互类型（三种）

| 交互方式 | 操作说明 | 示例事件 |
|---------|---------|---------|
| **点击** | 快速点一下目标 | 拍蚊子、关闹钟、开门 |
| **长按** | 按住目标 N 秒 | 关手机、关电视、捂墙隔音 |
| **拖拽** | 拖动物品到目标位置 | 关窗户、扶花瓶、盖被子 |
| **组合** | 依次完成多个操作 | 快递员（点击开门→拖拽收包裹） |

### 事件调度规则

- 每关有一个**事件池**（配置该关哪些事件可以出现）
- 事件按固定间隔随机从事件池抽取触发
- 每个事件有**响应时间窗口**，超时判定失败
- 同时最多 N 个事件并发（N 随关卡递增）

---

## 三、随机事件大全（20个）

### 普通房间事件（15个）

| # | 事件ID | 事件名 | 触发表现 | 玩家操作 | 交互类型 | 难度 | 超时惩罚 | 成功惩罚 |
|---|--------|-------|---------|---------|---------|------|---------|---------|
| 1 | phone_ring | 手机响铃 | 手机震动帧动画+铃声 | 长按手机 2 秒 | 长按 | 低 | -15 | 0 |
| 2 | window_wind | 窗户吹风 | 窗帘飘动帧动画 | 拖拽窗户关上 | 拖拽 | 低 | -15 | 0 |
| 3 | vase_fall | 花瓶倾倒 | 花瓶倾斜帧动画 | 点击扶正 | 点击 | 低 | -15 | 0 |
| 4 | door_knock | 有人敲门 | 门上敲击波纹特效 | 快速点击开门 | 点击 | 低 | -15 | 0 |
| 5 | alarm_clock | 闹钟响了 | 闹钟震动帧动画+闹铃声 | 点击关闭 | 点击 | 低 | -15 | 0 |
| 6 | mosquito | 蚊子飞入 | 蚊子在房间随机飞行 | 精确点击拍死移动目标 | 点击 | 中 | -20 | -2 |
| 7 | cat_jump | 小猫跳窗 | 猫从窗口进入走向床 | 拖拽猫到门外 | 拖拽 | 中 | -20 | -3 |
| 8 | tv_on | 电视自动开启 | 电视亮屏帧动画+声音 | 长按遥控器关闭 | 长按 | 中 | -20 | -2 |
| 9 | bird_chirp | 窗外小鸟叫 | 小鸟停在窗台叽喳 | 拖拽面包屑到窗外引走小鸟 | 拖拽 | 中 | -20 | -2 |
| 10 | toy_fall | 玩具掉地上 | 玩具从床头滚落 | 点击接住 | 点击 | 中 | -20 | -2 |
| 11 | thunder | 打雷闪电 | 窗外区域播放闪电帧动画+雷声 | 拖拽被子盖住宝宝头 | 拖拽 | 高 | -30 | -5 |
| 12 | neighbor_drill | 邻居装修 | 墙壁震动特效+钻墙声 | 长按墙壁隔音持续 3 秒 | 长按 | 高 | -25 | -5 |
| 13 | delivery | 快递员按门铃 | 门铃连响+门外快递员图标 | 点击开门→拖拽签收包裹 | 组合 | 高 | -30 | -5 |
| 14 | light_flicker | 灯泡闪烁 | 房间灯光明暗闪烁帧动画 | 拖拽开关到关闭位置 | 拖拽 | 中 | -20 | -2 |
| 15 | firecracker | 窗外鞭炮声 | 窗外闪光特效+爆竹声 | 点击关窗→长按拉窗帘 | 组合 | 高 | -30 | -5 |

### 梦境事件（5个）

梦境关卡场景切换为星空+云朵梦幻背景，事件更抽象：

| # | 事件ID | 事件名 | 触发表现 | 玩家操作 | 交互类型 | 难度 | 超时惩罚 | 成功惩罚 |
|---|--------|-------|---------|---------|---------|------|---------|---------|
| 16 | nightmare | 噩梦黑影 | 黑色影子从屏幕边缘逼近 | 连续点击 5 次驱散 | 点击 | 高 | -30 | -5 |
| 17 | star_fall | 星星坠落 | 星星从天空掉落砸向宝宝 | 拖拽星星放回天空 | 拖拽 | 中 | -20 | -3 |
| 18 | cloud_break | 云朵消散 | 宝宝脚下云朵开始碎裂 | 长按云朵修复 3 秒 | 长按 | 中 | -20 | -3 |
| 19 | dream_monster | 怪物咆哮 | 大怪物从远处逼近 | 拖拽奶瓶喂怪物让它缩小 | 拖拽 | 高 | -30 | -5 |
| 20 | lullaby_break | 摇篮曲断了 | 音符散落漂浮在空中 | 按顺序点击 3-5 个音符（有固定顺序） | 组合 | 高 | -25 | -3 |

---

## 四、关卡配置编排

### 普通关卡（第1-10关）

| 关卡 | 关卡名 | 时长 | 事件池 | 最大并发 | 事件间隔 | 响应时间倍率 |
|------|-------|------|--------|---------|---------|------------|
| 1 | 第一夜·初识 | 60s | phone_ring, alarm_clock | 1 | 8s | 1.0 |
| 2 | 第二夜·微风 | 60s | vase_fall, door_knock, window_wind | 1 | 7s | 1.0 |
| 3 | 第三夜·混合 | 70s | phone_ring, alarm_clock, vase_fall, door_knock, window_wind, toy_fall | 1 | 6s | 0.9 |
| 4 | 第四夜·蚊声 | 70s | phone_ring, alarm_clock, vase_fall, door_knock, window_wind, toy_fall, mosquito | 2 | 6s | 0.9 |
| 5 | 第五夜·猫咪 | 80s | phone_ring, alarm_clock, vase_fall, door_knock, window_wind, toy_fall, mosquito, cat_jump, tv_on | 2 | 5s | 0.9 |
| 6 | 第六夜·鸟鸣 | 80s | phone_ring, alarm_clock, vase_fall, door_knock, window_wind, toy_fall, mosquito, cat_jump, tv_on, bird_chirp | 2 | 5s | 0.85 |
| 7 | 第七夜·灯影 | 90s | phone_ring, alarm_clock, vase_fall, door_knock, window_wind, toy_fall, mosquito, cat_jump, tv_on, bird_chirp, light_flicker | 2 | 4.5s | 0.85 |
| 8 | 第八夜·风雨 | 90s | phone_ring, alarm_clock, vase_fall, door_knock, window_wind, toy_fall, mosquito, cat_jump, tv_on, bird_chirp, light_flicker, thunder, neighbor_drill | 3 | 4s | 0.8 |
| 9 | 第九夜·快递 | 100s | phone_ring, alarm_clock, vase_fall, door_knock, window_wind, toy_fall, mosquito, cat_jump, tv_on, bird_chirp, light_flicker, thunder, neighbor_drill, delivery | 3 | 3.5s | 0.8 |
| 10 | 第十夜·终极 | 120s | phone_ring, alarm_clock, vase_fall, door_knock, window_wind, toy_fall, mosquito, cat_jump, tv_on, bird_chirp, light_flicker, thunder, neighbor_drill, delivery, firecracker | 3 | 3s | 0.75 |

> 响应时间倍率说明：1.0 = 使用 EventConfig 中原始 timeWindow；0.8 = 缩短至原始的 80%

### 梦境关卡（第11-15关）

| 关卡 | 关卡名 | 时长 | 梦境事件池 | 混入普通事件 | 最大并发 | 事件间隔 | 响应时间倍率 |
|------|-------|------|----------|------------|---------|---------|------------|
| 11 | 梦境·初入 | 80s | star_fall, cloud_break | 无 | 1 | 6s | 1.0 |
| 12 | 梦境·黑影 | 90s | star_fall, cloud_break, nightmare | 无 | 2 | 5s | 0.9 |
| 13 | 梦境·怪物 | 100s | 全部5个梦境事件 | 无 | 2 | 4.5s | 0.85 |
| 14 | 梦境·混沌 | 110s | 全部5个梦境事件 | mosquito, light_flicker | 3 | 4s | 0.8 |
| 15 | 梦境·终焉 | 120s | 全部5个梦境事件 | thunder, delivery | 3 | 3s | 0.75 |

---

## 五、整体架构

### 技术选型

| 层次 | 选型 | 说明 |
|------|------|------|
| 游戏引擎 | Cocos Creator 3.x | 可视化编辑器，H5/微信小程序/App 多端导出 |
| 语言 | TypeScript | 类型安全，Cocos 官方推荐 |
| 动画 | 帧动画 + Animation Clip | Cocos 内置动画编辑器，无需额外工具 |
| 存档 | localStorage | 浏览器原生 API，SaveManager 封装读写 |
| 构建产物 | H5（Web Mobile） | Cocos 一键构建 |

### 场景设计：两个场景复用，不为每关建独立 Scene

- **普通关卡**：共用 `RoomLevel.scene`
- **梦境关卡**：共用 `DreamLevel.scene`
- 关卡差异完全由 `LevelConfig` 配置驱动，LevelController 读取配置初始化

### 项目目录结构

```
BabySleep/
├── assets/
│   ├── scenes/
│   │   ├── MainMenu.scene          # 主菜单
│   │   ├── LevelSelect.scene       # 关卡选择界面（展示15关解锁/星级状态）
│   │   ├── RoomLevel.scene         # 普通房间关卡（第1-10关共用）
│   │   └── DreamLevel.scene        # 梦境关卡（第11-15关共用）
│   ├── scripts/
│   │   ├── core/
│   │   │   ├── GameManager.ts      # 全局单例，场景切换，传递当前关卡ID
│   │   │   ├── SaveManager.ts      # localStorage 存档读写
│   │   │   └── EventBus.ts         # 跨组件通信（事件触发/处理通知）
│   │   ├── level/
│   │   │   ├── LevelController.ts  # 关卡主控：计时、安睡度管理、胜负判定
│   │   │   └── EventScheduler.ts   # 随机事件调度：按配置间隔随机抽取触发
│   │   ├── events/
│   │   │   ├── BaseEvent.ts        # 事件基类：时间窗口倒计时、成功/失败回调
│   │   │   ├── ClickEvent.ts       # 点击类事件处理逻辑
│   │   │   ├── LongPressEvent.ts   # 长按类事件处理逻辑（进度条显示）
│   │   │   ├── DragEvent.ts        # 拖拽类事件处理逻辑
│   │   │   └── ComboEvent.ts       # 组合类事件：按步骤序列依次触发子事件
│   │   ├── ui/
│   │   │   ├── LevelSelectUI.ts    # 关卡格子渲染（解锁状态、星级显示）
│   │   │   ├── HUD.ts              # 安睡度条、倒计时、事件提示图标
│   │   │   └── ResultPanel.ts      # 通关/失败结算面板（星级评价、重试、下一关）
│   │   └── data/
│   │       ├── EventConfig.ts      # 20个事件配置表
│   │       └── LevelConfig.ts      # 15关配置表
│   ├── textures/
│   │   ├── room/                   # 房间背景及互动物品（床、窗、门、手机、花瓶等）
│   │   ├── dream/                  # 梦境背景及元素（云朵、星星、怪物、黑影等）
│   │   ├── baby/                   # 宝宝帧动画（安睡、翻身/不安、哭醒）
│   │   ├── effects/                # 事件特效帧（闪电、震动波纹、声波扩散等）
│   │   └── ui/                     # 按钮、安睡度条、星级图标、结算面板
│   ├── audio/
│   │   ├── bgm/                    # 房间白噪音 BGM、梦境音乐 BGM
│   │   └── sfx/                    # 各事件音效（铃声、雷声、敲门声、猫叫等）
│   ├── prefabs/                    # 每个事件对应一个预制体（含动画、交互逻辑组件）
│   └── resources/                  # 需要动态加载的资源
```

### 场景切换流程

```
LevelSelect → GameManager.startLevel(levelId)
    │
    ▼  根据 LevelConfig.isDream 决定加载哪个 Scene
RoomLevel.scene 或 DreamLevel.scene
    │
    ▼
LevelController.init(levelConfig)
    │  读取事件池、并发数、间隔、响应时间倍率
    ▼
EventScheduler 按配置随机调度事件 → 实例化对应事件预制体
    │
    ├─ 安睡度 <= 0 → 关卡失败 → ResultPanel（重试 / 返回选关）
    └─ 倒计时结束 → 关卡通过 → ResultPanel（星级评价 → 下一关 / 返回选关）
```

---

## 六、数据配置表

### EventConfig.ts（核心字段）

```typescript
export type InteractionType = 'click' | 'longPress' | 'drag' | 'combo';

export interface EventConfig {
  id: string;
  name: string;
  interactionType: InteractionType;
  comboSteps?: InteractionType[];   // combo类型时的操作步骤序列
  timeWindow: number;               // 响应时间窗口（秒），乘以关卡倍率后使用
  sleepPenalty: number;             // 超时未处理的安睡度惩罚
  sleepMinorPenalty: number;        // 成功处理后的轻微惩罚（0 = 无）
  difficulty: 'easy' | 'medium' | 'hard';
  isDream: boolean;
  prefabName: string;               // 对应 prefabs/ 目录下的预制体名称
  sfxName: string;                  // 触发时播放的音效名称
}
```

### LevelConfig.ts（核心字段）

```typescript
export interface LevelConfig {
  id: number;                       // 关卡编号 1-15
  name: string;
  duration: number;                 // 关卡时长（秒）
  eventPool: string[];              // 该关可出现的事件 ID 列表
  maxConcurrent: number;            // 最大并发事件数
  eventInterval: number;            // 事件触发间隔（秒）
  responseTimeMultiplier: number;   // 响应时间倍率（0.75 ~ 1.0）
  isDream: boolean;                 // true = 加载 DreamLevel.scene
  unlockCondition: {
    type: 'default' | 'clear_level';
    levelId?: number;               // 前置关卡编号
    minStars?: number;              // 需要前置关卡达到的最低星级
  };
}
```

### SaveData 存档结构

```typescript
interface SaveData {
  levelStars: Record<number, number>; // { 1: 3, 2: 2, 3: 1 } 关卡号 → 星级（0=未通关）
}
// localStorage key: "baby_sleep_save"
```

---

## 七、美术资产规范

### 宝宝帧动画

| 状态 | 帧数 | 触发时机 |
|------|------|---------|
| 安睡中（idle） | 4帧循环 | 关卡正常进行时 |
| 翻身/不安（disturbed） | 4帧 | 安睡度每次下降时播放一次 |
| 哭醒（cry） | 4-6帧 | 安睡度归零，关卡失败时 |
| 睡着（sleep） | 2-3帧 | 关卡通过时 |

### 占位素材推荐来源

| 资源类型 | 推荐来源 | 说明 |
|---------|---------|------|
| 房间背景/物品 | **Kenny.nl** `Interior Pack` | 床、窗、门、桌、电视等家居元素 |
| UI 元素 | **Kenny.nl** `UI Pack` | 按钮、进度条、面板，风格统一 |
| 动物（猫/鸟） | **Kenny.nl** `Animal Pack` | 有猫、鸟等 Q 版素材 |
| 宝宝角色 | **OpenGameArt.org** 搜 `baby` / `character` | 找 Q 版小人占位 |
| 梦境元素 | **OpenGameArt.org** 搜 `fantasy cloud star` | 初期可用简单色块代替 |
| 音效 | **freesound.org** | 铃声、雷声、敲门声、猫叫等生活音效 |

**美术风格：** Q版/卡通扁平风格，色彩温馨，优先从 Kenny.nl 统一取素材避免风格不一致。

### 特效实现方式

| 特效 | 实现方式 |
|------|---------|
| 闪电 | 3帧 PNG 帧动画，播放在窗外区域节点上 |
| 震动波纹 | 3帧 PNG 帧动画 |
| 声波扩散 | 3帧 PNG 帧动画 或 Cocos 粒子系统 |
| 蚊子飞行 | 2帧循环 + Cocos Tween 随机路径移动 |
| 长按进度 | Cocos ProgressBar 组件，无需额外美术 |
