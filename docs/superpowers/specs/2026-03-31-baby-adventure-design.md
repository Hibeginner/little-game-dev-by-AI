# Baby Adventure — 游戏设计文档

**日期：** 2026-03-31  
**平台：** Web 浏览器（H5），后期可扩展至微信小程序  
**引擎：** Cocos Creator 3.x + TypeScript  
**存档：** localStorage（纯本地，无需后端）

---

## 一、项目概述

一款休闲关卡集合式2D游戏。玩家扮演一个人类小婴儿，在中国著名地标场景中闯关打怪。每个地标对应一个副本关卡，每个关卡采用不同的小游戏玩法（贪吃蛇、雷霆战机等）。通关后解锁新武器，解锁后续关卡。

**核心主题元素：**
- 主角：婴儿（Q版卡通风格）
- 武器：奶瓶、饼干、叉子、勺子
- 敌人：蚂蚁、蜜蜂、小狗、小猫
- 场景：上海东方明珠、杭州西湖、广州塔等中国著名地标

---

## 二、整体架构

### 技术选型

| 层次 | 选型 | 说明 |
|------|------|------|
| 游戏引擎 | Cocos Creator 3.x | TypeScript，支持H5/微信小程序多端导出 |
| 语言 | TypeScript | 类型安全，Cocos官方推荐 |
| 动画 | 帧动画 + Animation Clip | Cocos内置动画编辑器，无需额外工具 |
| 存档 | localStorage | 浏览器原生API，SaveManager封装读写 |
| 构建产物 | H5（Web Mobile） | Cocos一键构建 |
| 版本管理 | Git | 代码+场景文件均纳入版本控制 |

### 架构方案

采用**单体式 Cocos Creator 项目 + Scene 管理**。所有关卡在同一项目中，每种小游戏玩法是一个独立的 Scene，共享一套公共模块。

**核心原则：**
- `GameManager` 是唯一全局状态持有者，负责场景跳转
- 每种玩法继承 `BaseLevelController`，实现统一接口
- 新增关卡只需：新建 Scene + 新增 LevelConfig 条目，零改动核心代码

### 项目目录结构

```
BabyAdventure/
├── assets/
│   ├── scenes/                      # Cocos .scene 场景文件（关卡蓝图，非美术资产）
│   │   ├── MainMenu.scene           # 主菜单
│   │   ├── WorldMap.scene           # 世界地图（地标副本选择）
│   │   ├── Level_Snake.scene        # 贪吃蛇玩法
│   │   ├── Level_Shooter.scene      # 雷霆战机玩法
│   │   └── Level_Template.scene     # 新关卡模板（可复制扩展）
│   ├── scripts/
│   │   ├── core/
│   │   │   ├── GameManager.ts       # 全局单例，场景切换
│   │   │   ├── SaveManager.ts       # localStorage 存档读写
│   │   │   └── EventBus.ts          # 跨组件通信
│   │   ├── levels/
│   │   │   ├── BaseLevelController.ts  # 所有关卡继承的基类
│   │   │   ├── SnakeLevel.ts
│   │   │   └── ShooterLevel.ts
│   │   ├── ui/
│   │   │   ├── WorldMapUI.ts
│   │   │   └── HUD.ts               # 血量、武器、分数
│   │   └── data/
│   │       ├── LevelConfig.ts       # 关卡配置表
│   │       └── WeaponConfig.ts      # 武器配置表
│   ├── textures/
│   │   ├── characters/
│   │   │   ├── baby/                # 婴儿帧动画 PNG（按动作分文件夹）
│   │   │   └── enemies/
│   │   │       ├── ant/
│   │   │       ├── bee/
│   │   │       ├── dog/
│   │   │       └── cat/
│   │   ├── weapons/                 # 奶瓶、饼干、叉子、勺子图标
│   │   ├── backgrounds/             # 各地标场景背景图
│   │   ├── ui/                      # 按钮、血条、地图UI
│   │   └── effects/                 # 爆炸、子弹特效帧
│   ├── audio/
│   │   ├── bgm/
│   │   └── sfx/
│   ├── prefabs/                     # 预制体（敌人、武器、子弹等可复用节点）
│   └── resources/                   # 需要动态加载的资源
```

---

## 三、角色与美术资产规范

### 动画方式

采用**帧动画（Sprite Sheet）**。将角色每一帧图片排列在一张大图上，Cocos Creator Animation Editor 按顺序播放产生动画效果。

### 主角（婴儿）所需帧动画

| 动画状态 | 帧数建议 | 说明 |
|---------|---------|------|
| idle（待机） | 4-6帧 | 轻微呼吸/眨眼循环 |
| move（移动） | 6-8帧 | 爬行或走路 |
| attack（攻击） | 4-6帧 | 挥舞武器 |
| hurt（受伤） | 2-3帧 | 闪红 |
| die（死亡） | 4-6帧 | 倒地 |

### 敌人每种所需帧动画

每种敌人需要：idle / move / attack / die — 各 3-6 帧。

### 美术素材策略

初期使用**免费素材库占位**，跑通游戏逻辑后再替换正式美术：
- **Kenny.nl** — 高质量免费Q版素材，风格统一
- **OpenGameArt.org** — 完全免费，CC协议，搜索 `baby` / `cute monster`
- **Cocos Store** — 中文资源，部分免费

美术风格定位：**Q版/卡通风格**（圆润、色彩鲜艳、夸张比例），与婴儿+可爱怪物主题高度匹配。

### 工具链

| 工具 | 用途 | 费用 |
|------|------|------|
| Cocos Creator | 引擎+编辑器+动画编辑器 | 免费 |
| VS Code | TypeScript 编写 | 免费 |
| TexturePacker（可选） | 打包 Sprite Sheet | 免费版够用 |
| Audacity（可选） | 音效剪辑 | 免费 |

---

## 四、数据配置表

### 关卡配置表 `LevelConfig.ts`

```typescript
export interface LevelConfig {
  id: string;              // 唯一标识，如 "shanghai_snake"
  name: string;            // 显示名称，如 "上海·东方明珠"
  sceneName: string;       // Cocos Scene 文件名
  gameMode: GameMode;      // 玩法类型枚举
  landmark: string;        // 地标名（用于加载对应背景图）
  enemies: string[];       // 该副本出现的敌人 ID 列表
  unlockCondition: {
    type: 'default' | 'clear_level';
    levelId?: string;      // 需要通关哪个关卡才解锁
  };
  reward: {
    weaponId: string;      // 通关后解锁的武器 ID
  };
}

export enum GameMode {
  SNAKE   = 'snake',
  SHOOTER = 'shooter',
  // 后续扩展：RUNNER, PUZZLE, etc.
}

export const LEVELS: LevelConfig[] = [
  {
    id: 'shanghai_snake',
    name: '上海·东方明珠',
    sceneName: 'Level_Snake',
    gameMode: GameMode.SNAKE,
    landmark: 'oriental_pearl',
    enemies: ['ant', 'bee'],
    unlockCondition: { type: 'default' },
    reward: { weaponId: 'cookie' }, // 通关奖励饼干（奶瓶为初始武器，无需奖励）
  },
  {
    id: 'guangzhou_shooter',
    name: '广州·广州塔',
    sceneName: 'Level_Shooter',
    gameMode: GameMode.SHOOTER,
    landmark: 'canton_tower',
    enemies: ['dog', 'cat'],
    unlockCondition: { type: 'clear_level', levelId: 'shanghai_snake' },
    reward: { weaponId: 'fork' },
  },
  // 新增关卡：只需在此追加一条记录
];
```

### 武器配置表 `WeaponConfig.ts`

```typescript
export interface WeaponConfig {
  id: string;
  name: string;
  damage: number;
  attackSpeed: number;     // 攻击间隔（秒）
  projectileSpeed: number; // 投掷物飞行速度（px/s）
  iconKey: string;         // textures/weapons/ 下的图片名
  unlockedByDefault: boolean;
}

export const WEAPONS: WeaponConfig[] = [
  { id: 'bottle', name: '奶瓶', damage: 10, attackSpeed: 1.0, projectileSpeed: 300, iconKey: 'weapon_bottle', unlockedByDefault: true  }, // 初始武器，玩家开局即持有
  { id: 'cookie', name: '饼干', damage: 15, attackSpeed: 0.8, projectileSpeed: 350, iconKey: 'weapon_cookie', unlockedByDefault: false },
  { id: 'fork',   name: '叉子', damage: 25, attackSpeed: 0.6, projectileSpeed: 400, iconKey: 'weapon_fork',   unlockedByDefault: false },
  { id: 'spoon',  name: '勺子', damage: 20, attackSpeed: 0.7, projectileSpeed: 380, iconKey: 'weapon_spoon',  unlockedByDefault: false },
];
```

### 存档结构

```typescript
interface SaveData {
  clearedLevels: string[];   // 已通关关卡 ID 列表
  unlockedWeapons: string[]; // 已解锁武器 ID 列表
  selectedWeapon: string;    // 当前选中武器
}
// localStorage key: "baby_adventure_save"
```

---

## 五、关卡基类与各玩法接口

### 关卡基类 `BaseLevelController.ts`

```typescript
export abstract class BaseLevelController extends Component {
  // 子类必须实现
  abstract onLevelStart(): void;
  abstract onLevelUpdate(): void;
  abstract onLevelComplete(): void;
  abstract onLevelFail(): void;

  // 基类提供的公共能力
  protected showHUD(): void { ... }
  protected saveProgress(): void { ... }
  protected loadNextScene(id: string): void { ... }
}
```

### 各玩法职责边界

| 玩法 | Scene 名 | 核心机制 | 胜利条件 |
|------|---------|---------|---------|
| 贪吃蛇 | `Level_Snake` | 婴儿作为蛇头，吃掉敌人使身体延伸，碰边界或自身失败 | 吃够 N 只敌人 |
| 雷霆战机 | `Level_Shooter` | 婴儿飞行，自动发射武器，击落从上方飞来的敌人 | 击败 Boss 或撑过限时 |
| （预留）跑酷 | `Level_Runner` | 横向跑动，跳跃躲避障碍，踩踏敌人 | 到达终点 |

### 场景切换流程

```
WorldMap（选择副本）
    │
    ▼
GameManager.loadLevel(levelId)
    │  查 LevelConfig → 找到 sceneName
    ▼
Cocos director.loadScene(sceneName)
    │
    ▼
BaseLevelController.onLevelStart()
    │
    ├─ 通关 → onLevelComplete() → SaveManager 存档 → 返回 WorldMap
    └─ 失败 → onLevelFail()     → 显示重试界面
```

### 世界地图（WorldMap Scene）职责

- 读取 `LevelConfig` + `SaveData`，渲染各地标节点
- 已通关：显示星级评分
- 已解锁未通关：可点击进入
- 未解锁：显示锁定状态 + 解锁条件提示

---

## 六、开发路线

### 阶段一：框架搭建（优先）
- 搭建 Cocos Creator 项目基础结构
- 实现 GameManager / SaveManager / EventBus
- 实现 WorldMap 场景（带锁定/解锁状态）
- 用占位图跑通完整流程：选关 → 进入关卡 → 通关 → 存档 → 返回

### 阶段二：第一个玩法（验证可行性）
- 实现贪吃蛇关卡（`Level_Snake`）
- 接入 BaseLevelController 接口
- 基本 HUD（血量、分数）

### 阶段三：第二个玩法（验证可扩展性）
- 实现雷霆战机关卡（`Level_Shooter`）
- 验证新增一个 Scene + 一条 LevelConfig 是否真的不需要改核心代码

### 阶段四：内容填充
- 替换占位素材为正式美术资源
- 补充音效、BGM
- 添加更多关卡、武器、敌人
