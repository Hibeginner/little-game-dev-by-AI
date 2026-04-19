# Baby Sleep Level 1 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a playable Level 1 MVP of Baby Sleep — a whack-a-mole variant where the player handles two event types (click and long-press) to keep a baby asleep for 60 seconds. Includes a main menu, one gameplay level with placeholder art, and a result panel.

**Architecture:** Cocos Creator 3.8.8 project with data-driven framework. GameManager (static singleton) handles scene switching. LevelController reads LevelConfig to run gameplay. EventScheduler spawns event prefabs from `resources/` at timed intervals. BaseEvent class hierarchy (ClickEvent, LongPressEvent) handles player interaction. EventBus provides cross-component communication. All node references found by name at runtime — no `@property` wiring needed in the editor.

**Tech Stack:** Cocos Creator 3.8.8, TypeScript, Cocos MCP tools for scene/prefab creation.

**Design spec:** `team_dev_log/design/spec/design_spec_20260418_120000.md`

**Design resolution:** 1280x720 landscape (current project setting).

---

### File Structure

**Scripts (12 files):**

| File | Responsibility |
|------|---------------|
| `assets/scripts/core/EventBus.ts` | Event bus singleton + event name enum |
| `assets/scripts/core/GameManager.ts` | Static singleton: current level ID, scene loading |
| `assets/scripts/data/EventConfig.ts` | EventConfig interface + 2 event data entries |
| `assets/scripts/data/LevelConfig.ts` | LevelConfig interface + level 1 data |
| `assets/scripts/events/BaseEvent.ts` | Event base class: time window countdown, success/fail |
| `assets/scripts/events/ClickEvent.ts` | Click interaction: touch → success |
| `assets/scripts/events/LongPressEvent.ts` | Long-press interaction: hold duration, progress bar |
| `assets/scripts/level/LevelController.ts` | Level main controller: sleep value, timer, win/lose |
| `assets/scripts/level/EventScheduler.ts` | Timed event spawning from event pool |
| `assets/scripts/ui/MainMenuUI.ts` | Start button handler → GameManager.startLevel(1) |
| `assets/scripts/ui/HUD.ts` | Sleep bar + timer display updates |
| `assets/scripts/ui/ResultPanel.ts` | Result popup: title, sleep value, replay/menu buttons |

**Scenes (2):**

| Scene | Path |
|-------|------|
| MainMenu | `assets/scenes/MainMenu.scene` |
| RoomLevel | `assets/scenes/RoomLevel.scene` |

**Prefabs (3, under `resources/` for dynamic loading):**

| Prefab | Path |
|--------|------|
| PhoneRingEvent | `assets/resources/prefabs/events/PhoneRingEvent.prefab` |
| AlarmClockEvent | `assets/resources/prefabs/events/AlarmClockEvent.prefab` |
| ResultPanel | `assets/resources/prefabs/ui/ResultPanel.prefab` |

### Key Implementation Notes

1. **Dynamic loading**: All prefabs are in `assets/resources/` so `resources.load()` works. EventConfig.prefabPath values (e.g., `'prefabs/events/PhoneRingEvent'`) are relative to `assets/resources/`.
2. **No ProgressBar component**: All progress bars use direct `UITransform.width` manipulation on a Sprite node. Bar fill nodes use `anchorX=0` for left-aligned shrinking.
3. **Touch detection**: Event prefab root nodes must be `2DNode` type (auto-creates UITransform) with a non-zero content size for touch events to register.
4. **Find by name**: All scripts locate sibling/child nodes via `getChildByName()`. Node names must exactly match the names in the scene/prefab hierarchy below.
5. **Build scenes list**: Both scenes must be added to Project Settings → Scenes for `director.loadScene()` to work.

---

### Task 1: Core & Data Scripts

**Goal:** Create EventBus, GameManager, EventConfig, and LevelConfig — the foundation everything else depends on.

**Files:**
- Create: `BabySleep/assets/scripts/core/EventBus.ts`
- Create: `BabySleep/assets/scripts/data/EventConfig.ts`
- Create: `BabySleep/assets/scripts/data/LevelConfig.ts`
- Create: `BabySleep/assets/scripts/core/GameManager.ts`

- [ ] **Step 1: Create EventBus.ts**

```typescript
// assets/scripts/core/EventBus.ts
import { EventTarget } from 'cc';

export enum GameEvents {
    SLEEP_CHANGED = 'SLEEP_CHANGED',
    EVENT_SPAWNED = 'EVENT_SPAWNED',
    EVENT_RESOLVED = 'EVENT_RESOLVED',
    EVENT_FAILED = 'EVENT_FAILED',
    LEVEL_END = 'LEVEL_END',
}

export const eventBus = new EventTarget();
```

- [ ] **Step 2: Create EventConfig.ts**

```typescript
// assets/scripts/data/EventConfig.ts
export type InteractionType = 'click' | 'longPress' | 'drag' | 'combo';

export interface EventConfig {
    id: string;
    name: string;
    interactionType: InteractionType;
    timeWindow: number;
    requiredDuration?: number;
    comboSteps?: InteractionType[];
    sleepPenalty: number;
    sleepMinorPenalty: number;
    difficulty: 'easy' | 'medium' | 'hard';
    isDream: boolean;
    prefabPath: string;
    spawnAnchor: string;
}

export const EVENT_CONFIGS: Record<string, EventConfig> = {
    phone_ring: {
        id: 'phone_ring',
        name: '手机响铃',
        interactionType: 'longPress',
        timeWindow: 5,
        requiredDuration: 2,
        sleepPenalty: -15,
        sleepMinorPenalty: 0,
        difficulty: 'easy',
        isDream: false,
        prefabPath: 'prefabs/events/PhoneRingEvent',
        spawnAnchor: 'AnchorPhone',
    },
    alarm_clock: {
        id: 'alarm_clock',
        name: '闹钟响了',
        interactionType: 'click',
        timeWindow: 4,
        sleepPenalty: -15,
        sleepMinorPenalty: 0,
        difficulty: 'easy',
        isDream: false,
        prefabPath: 'prefabs/events/AlarmClockEvent',
        spawnAnchor: 'AnchorAlarm',
    },
};
```

- [ ] **Step 3: Create LevelConfig.ts**

```typescript
// assets/scripts/data/LevelConfig.ts
export interface LevelConfig {
    id: number;
    name: string;
    duration: number;
    eventPool: string[];
    maxConcurrent: number;
    eventInterval: number;
    responseTimeMultiplier: number;
    isDream: boolean;
    sceneName: string;
}

export const LEVEL_CONFIGS: Record<number, LevelConfig> = {
    1: {
        id: 1,
        name: '第一夜·初识',
        duration: 60,
        eventPool: ['phone_ring', 'alarm_clock'],
        maxConcurrent: 1,
        eventInterval: 8,
        responseTimeMultiplier: 1.0,
        isDream: false,
        sceneName: 'RoomLevel',
    },
};
```

- [ ] **Step 4: Create GameManager.ts**

```typescript
// assets/scripts/core/GameManager.ts
import { director } from 'cc';
import { LEVEL_CONFIGS, LevelConfig } from '../data/LevelConfig';

export class GameManager {
    private static _currentLevelId: number = 1;

    public static get currentLevelId(): number {
        return this._currentLevelId;
    }

    public static get currentLevelConfig(): LevelConfig | null {
        return LEVEL_CONFIGS[this._currentLevelId] ?? null;
    }

    public static startLevel(levelId: number): void {
        const config = LEVEL_CONFIGS[levelId];
        if (!config) {
            console.error(`LevelConfig not found for level ${levelId}`);
            return;
        }
        this._currentLevelId = levelId;
        director.loadScene(config.sceneName);
    }

    public static backToMenu(): void {
        director.loadScene('MainMenu');
    }
}
```

- [ ] **Step 5: Refresh assets and verify no compile errors**

Run: Refresh asset database in Cocos Creator (MCP: `refresh_assets`).
Check: Console should show no TypeScript compilation errors for the 4 new files.

- [ ] **Step 6: Commit**

```
git add BabySleep/assets/scripts/core/ BabySleep/assets/scripts/data/
git commit -m "feat: add core data layer (EventBus, GameManager, EventConfig, LevelConfig)"
```

---

### Task 2: Event System Scripts

**Goal:** Create BaseEvent base class and ClickEvent/LongPressEvent subclasses that handle player interaction.

**Files:**
- Create: `BabySleep/assets/scripts/events/BaseEvent.ts`
- Create: `BabySleep/assets/scripts/events/ClickEvent.ts`
- Create: `BabySleep/assets/scripts/events/LongPressEvent.ts`

- [ ] **Step 1: Create BaseEvent.ts**

```typescript
// assets/scripts/events/BaseEvent.ts
import { _decorator, Component, Node, UITransform } from 'cc';
import { EventConfig } from '../data/EventConfig';
import { eventBus, GameEvents } from '../core/EventBus';

const { ccclass } = _decorator;

@ccclass('BaseEvent')
export class BaseEvent extends Component {

    protected eventConfig: EventConfig | null = null;
    protected timeRemaining: number = 0;
    protected timeWindow: number = 0;
    protected isResolved: boolean = false;

    // Time bar references (found by name in onLoad)
    protected timeBarFill: Node | null = null;
    protected timeBarTotalWidth: number = 120;

    onLoad(): void {
        const timeBar = this.node.getChildByName('TimeBar');
        if (timeBar) {
            this.timeBarFill = timeBar.getChildByName('BarFill');
            if (this.timeBarFill) {
                const ut = this.timeBarFill.getComponent(UITransform);
                if (ut) {
                    this.timeBarTotalWidth = ut.width;
                }
            }
        }
    }

    public init(config: EventConfig, responseTimeMultiplier: number): void {
        this.eventConfig = config;
        this.timeWindow = config.timeWindow * responseTimeMultiplier;
        this.timeRemaining = this.timeWindow;
        this.isResolved = false;
    }

    update(dt: number): void {
        if (this.isResolved || !this.eventConfig) return;

        this.timeRemaining -= dt;

        // Update time bar visual
        if (this.timeBarFill) {
            const ut = this.timeBarFill.getComponent(UITransform);
            if (ut) {
                ut.width = Math.max(0, this.timeRemaining / this.timeWindow) * this.timeBarTotalWidth;
            }
        }

        if (this.timeRemaining <= 0) {
            this.onTimeout();
        }
    }

    protected onSuccess(): void {
        if (this.isResolved) return;
        this.isResolved = true;
        eventBus.emit(GameEvents.EVENT_RESOLVED, {
            eventId: this.eventConfig!.id,
            penalty: this.eventConfig!.sleepMinorPenalty,
        });
        this.node.destroy();
    }

    protected onTimeout(): void {
        if (this.isResolved) return;
        this.isResolved = true;
        eventBus.emit(GameEvents.EVENT_FAILED, {
            eventId: this.eventConfig!.id,
            penalty: this.eventConfig!.sleepPenalty,
        });
        this.node.destroy();
    }
}
```

- [ ] **Step 2: Create ClickEvent.ts**

```typescript
// assets/scripts/events/ClickEvent.ts
import { _decorator, Node, EventTouch } from 'cc';
import { BaseEvent } from './BaseEvent';

const { ccclass } = _decorator;

@ccclass('ClickEvent')
export class ClickEvent extends BaseEvent {

    onLoad(): void {
        super.onLoad();
        this.node.on(Node.EventType.TOUCH_END, this.onTouchEnd, this);
    }

    onDestroy(): void {
        this.node.off(Node.EventType.TOUCH_END, this.onTouchEnd, this);
    }

    private onTouchEnd(event: EventTouch): void {
        this.onSuccess();
    }
}
```

- [ ] **Step 3: Create LongPressEvent.ts**

```typescript
// assets/scripts/events/LongPressEvent.ts
import { _decorator, Node, EventTouch, UITransform } from 'cc';
import { BaseEvent } from './BaseEvent';
import { EventConfig } from '../data/EventConfig';

const { ccclass } = _decorator;

@ccclass('LongPressEvent')
export class LongPressEvent extends BaseEvent {

    private pressBarFill: Node | null = null;
    private pressBarTotalWidth: number = 120;
    private isPressing: boolean = false;
    private pressTime: number = 0;
    private requiredDuration: number = 2;

    onLoad(): void {
        super.onLoad();

        const pressBar = this.node.getChildByName('PressBar');
        if (pressBar) {
            this.pressBarFill = pressBar.getChildByName('BarFill');
            if (this.pressBarFill) {
                const ut = this.pressBarFill.getComponent(UITransform);
                if (ut) {
                    this.pressBarTotalWidth = ut.width;
                }
            }
        }

        this.node.on(Node.EventType.TOUCH_START, this.onTouchStart, this);
        this.node.on(Node.EventType.TOUCH_END, this.onTouchEnd, this);
        this.node.on(Node.EventType.TOUCH_CANCEL, this.onTouchEnd, this);
    }

    onDestroy(): void {
        this.node.off(Node.EventType.TOUCH_START, this.onTouchStart, this);
        this.node.off(Node.EventType.TOUCH_END, this.onTouchEnd, this);
        this.node.off(Node.EventType.TOUCH_CANCEL, this.onTouchEnd, this);
    }

    public init(config: EventConfig, responseTimeMultiplier: number): void {
        super.init(config, responseTimeMultiplier);
        this.requiredDuration = config.requiredDuration ?? 2;
        this.pressTime = 0;
        this.isPressing = false;
    }

    private onTouchStart(event: EventTouch): void {
        this.isPressing = true;
    }

    private onTouchEnd(event: EventTouch): void {
        this.isPressing = false;
        this.pressTime = 0;
        if (this.pressBarFill) {
            const ut = this.pressBarFill.getComponent(UITransform);
            if (ut) {
                ut.width = 0;
            }
        }
    }

    update(dt: number): void {
        super.update(dt);
        if (this.isResolved) return;

        if (this.isPressing) {
            this.pressTime += dt;
            if (this.pressBarFill) {
                const ut = this.pressBarFill.getComponent(UITransform);
                if (ut) {
                    ut.width = Math.min(1, this.pressTime / this.requiredDuration) * this.pressBarTotalWidth;
                }
            }
            if (this.pressTime >= this.requiredDuration) {
                this.onSuccess();
            }
        }
    }
}
```

- [ ] **Step 4: Refresh assets and verify no compile errors**

Run: Refresh asset database.
Check: No TypeScript errors for the 3 event scripts.

- [ ] **Step 5: Commit**

```
git add BabySleep/assets/scripts/events/
git commit -m "feat: add event system (BaseEvent, ClickEvent, LongPressEvent)"
```

---

### Task 3: UI Scripts

**Goal:** Create MainMenuUI, HUD, and ResultPanel scripts.

**Files:**
- Create: `BabySleep/assets/scripts/ui/MainMenuUI.ts`
- Create: `BabySleep/assets/scripts/ui/HUD.ts`
- Create: `BabySleep/assets/scripts/ui/ResultPanel.ts`

- [ ] **Step 1: Create MainMenuUI.ts**

```typescript
// assets/scripts/ui/MainMenuUI.ts
import { _decorator, Component, Button } from 'cc';
import { GameManager } from '../core/GameManager';

const { ccclass } = _decorator;

@ccclass('MainMenuUI')
export class MainMenuUI extends Component {

    onLoad(): void {
        const btnStart = this.node.getChildByName('BtnStart');
        if (btnStart) {
            btnStart.on(Button.EventType.CLICK, this.onStart, this);
        }
    }

    private onStart(): void {
        GameManager.startLevel(1);
    }
}
```

- [ ] **Step 2: Create HUD.ts**

```typescript
// assets/scripts/ui/HUD.ts
import { _decorator, Component, Label, UITransform, Sprite, Color } from 'cc';

const { ccclass } = _decorator;

@ccclass('HUD')
export class HUD extends Component {

    private sleepBarFill: Sprite | null = null;
    private sleepBarFillUT: UITransform | null = null;
    private sleepBarTotalWidth: number = 300;
    private sleepLabel: Label | null = null;
    private timerLabel: Label | null = null;

    onLoad(): void {
        const barBg = this.node.getChildByName('SleepBarBg');
        const barFillNode = barBg?.getChildByName('SleepBarFill');
        if (barFillNode) {
            this.sleepBarFill = barFillNode.getComponent(Sprite);
            this.sleepBarFillUT = barFillNode.getComponent(UITransform);
            if (this.sleepBarFillUT) {
                this.sleepBarTotalWidth = this.sleepBarFillUT.width;
            }
        }

        this.sleepLabel = this.node.getChildByName('SleepLabel')?.getComponent(Label) ?? null;
        this.timerLabel = this.node.getChildByName('TimerLabel')?.getComponent(Label) ?? null;
    }

    public updateSleep(value: number): void {
        if (this.sleepBarFillUT) {
            this.sleepBarFillUT.width = (value / 100) * this.sleepBarTotalWidth;
        }
        // Color gradient: green (100) → red (0)
        if (this.sleepBarFill) {
            const r = Math.round(255 * (1 - value / 100));
            const g = Math.round(255 * (value / 100));
            this.sleepBarFill.color = new Color(r, g, 0, 255);
        }
        if (this.sleepLabel) {
            this.sleepLabel.string = Math.ceil(value).toString();
        }
    }

    public updateTimer(seconds: number): void {
        if (this.timerLabel) {
            const m = Math.floor(Math.max(0, seconds) / 60);
            const s = Math.floor(Math.max(0, seconds) % 60);
            this.timerLabel.string = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }
    }
}
```

- [ ] **Step 3: Create ResultPanel.ts**

```typescript
// assets/scripts/ui/ResultPanel.ts
import { _decorator, Component, Label, Button } from 'cc';
import { GameManager } from '../core/GameManager';

const { ccclass } = _decorator;

@ccclass('ResultPanel')
export class ResultPanel extends Component {

    private titleLabel: Label | null = null;
    private sleepLabel: Label | null = null;

    onLoad(): void {
        const panel = this.node.getChildByName('Panel');
        if (!panel) return;

        this.titleLabel = panel.getChildByName('TitleLabel')?.getComponent(Label) ?? null;
        this.sleepLabel = panel.getChildByName('SleepLabel')?.getComponent(Label) ?? null;

        const btnReplay = panel.getChildByName('BtnReplay');
        const btnMenu = panel.getChildByName('BtnMenu');
        btnReplay?.on(Button.EventType.CLICK, this.onReplay, this);
        btnMenu?.on(Button.EventType.CLICK, this.onBackToMenu, this);
    }

    public show(success: boolean, sleepValue: number): void {
        if (this.titleLabel) {
            this.titleLabel.string = success ? '通关！' : '宝宝哭醒了...';
        }
        if (this.sleepLabel) {
            this.sleepLabel.string = `安睡度: ${Math.ceil(sleepValue)}`;
        }
    }

    private onReplay(): void {
        GameManager.startLevel(GameManager.currentLevelId);
    }

    private onBackToMenu(): void {
        GameManager.backToMenu();
    }
}
```

- [ ] **Step 4: Refresh assets and verify no compile errors**

Run: Refresh asset database.
Check: No TypeScript errors for the 3 UI scripts.

- [ ] **Step 5: Commit**

```
git add BabySleep/assets/scripts/ui/
git commit -m "feat: add UI scripts (MainMenuUI, HUD, ResultPanel)"
```

---

### Task 4: Level Logic Scripts

**Goal:** Create EventScheduler and LevelController — the core gameplay loop.

**Files:**
- Create: `BabySleep/assets/scripts/level/EventScheduler.ts`
- Create: `BabySleep/assets/scripts/level/LevelController.ts`

- [ ] **Step 1: Create EventScheduler.ts**

```typescript
// assets/scripts/level/EventScheduler.ts
import { _decorator, Component, Node, resources, Prefab, instantiate } from 'cc';
import { LevelConfig } from '../data/LevelConfig';
import { EVENT_CONFIGS, EventConfig } from '../data/EventConfig';
import { eventBus, GameEvents } from '../core/EventBus';
import { BaseEvent } from '../events/BaseEvent';

const { ccclass } = _decorator;

@ccclass('EventScheduler')
export class EventScheduler extends Component {

    private levelConfig: LevelConfig | null = null;
    private eventLayer: Node | null = null;
    private timeSinceLastSpawn: number = 0;
    private isScheduling: boolean = false;
    private activeEventCount: number = 0;
    private prefabCache: Map<string, Prefab> = new Map();

    public init(config: LevelConfig, eventLayer: Node): void {
        this.levelConfig = config;
        this.eventLayer = eventLayer;
        this.timeSinceLastSpawn = 0;
        this.activeEventCount = 0;
        this.isScheduling = true;

        eventBus.on(GameEvents.EVENT_RESOLVED, this.onEventComplete, this);
        eventBus.on(GameEvents.EVENT_FAILED, this.onEventComplete, this);

        this.preloadPrefabs();
    }

    onDestroy(): void {
        eventBus.off(GameEvents.EVENT_RESOLVED, this.onEventComplete, this);
        eventBus.off(GameEvents.EVENT_FAILED, this.onEventComplete, this);
    }

    private preloadPrefabs(): void {
        if (!this.levelConfig) return;
        for (const eventId of this.levelConfig.eventPool) {
            const config = EVENT_CONFIGS[eventId];
            if (config) {
                resources.load(config.prefabPath, Prefab, (err, prefab) => {
                    if (err) {
                        console.error(`Failed to load prefab: ${config.prefabPath}`, err);
                        return;
                    }
                    this.prefabCache.set(eventId, prefab!);
                });
            }
        }
    }

    public stopScheduling(): void {
        this.isScheduling = false;
    }

    update(dt: number): void {
        if (!this.isScheduling || !this.levelConfig) return;

        this.timeSinceLastSpawn += dt;

        if (this.timeSinceLastSpawn >= this.levelConfig.eventInterval) {
            this.timeSinceLastSpawn = 0;
            this.trySpawnEvent();
        }
    }

    private trySpawnEvent(): void {
        if (!this.levelConfig || !this.eventLayer) return;
        if (this.activeEventCount >= this.levelConfig.maxConcurrent) return;

        const pool = this.levelConfig.eventPool;
        const randomIndex = Math.floor(Math.random() * pool.length);
        const eventId = pool[randomIndex];
        const config = EVENT_CONFIGS[eventId];
        if (!config) return;

        const prefab = this.prefabCache.get(eventId);
        if (!prefab) {
            console.warn(`Prefab not loaded yet for event: ${eventId}`);
            return;
        }

        this.spawnEvent(config, prefab);
    }

    private spawnEvent(config: EventConfig, prefab: Prefab): void {
        const eventNode = instantiate(prefab);
        this.eventLayer!.addChild(eventNode);

        // Position at anchor point
        const anchor = this.eventLayer!.getChildByName(config.spawnAnchor);
        if (anchor) {
            eventNode.setPosition(anchor.position.clone());
        }

        // Initialize event component (finds subclass via instanceof)
        const eventComponent = eventNode.getComponent(BaseEvent);
        if (eventComponent) {
            eventComponent.init(config, this.levelConfig!.responseTimeMultiplier);
        }

        this.activeEventCount++;
        eventBus.emit(GameEvents.EVENT_SPAWNED, { eventId: config.id });
    }

    private onEventComplete(): void {
        this.activeEventCount = Math.max(0, this.activeEventCount - 1);
    }
}
```

- [ ] **Step 2: Create LevelController.ts**

```typescript
// assets/scripts/level/LevelController.ts
import { _decorator, Component, Node, Label, resources, Prefab, instantiate } from 'cc';
import { GameManager } from '../core/GameManager';
import { LevelConfig } from '../data/LevelConfig';
import { eventBus, GameEvents } from '../core/EventBus';
import { EventScheduler } from './EventScheduler';
import { HUD } from '../ui/HUD';
import { ResultPanel } from '../ui/ResultPanel';
import { BaseEvent } from '../events/BaseEvent';

const { ccclass } = _decorator;

@ccclass('LevelController')
export class LevelController extends Component {

    private sleepValue: number = 100;
    private timeRemaining: number = 0;
    private levelConfig: LevelConfig | null = null;
    private isLevelEnded: boolean = false;
    private scheduler: EventScheduler | null = null;
    private hud: HUD | null = null;
    private babyFace: Label | null = null;
    private eventLayer: Node | null = null;

    onLoad(): void {
        this.levelConfig = GameManager.currentLevelConfig;
        if (!this.levelConfig) {
            console.error('No level config found');
            return;
        }

        // Find nodes by name (all are siblings under Canvas)
        const canvas = this.node.parent!;
        this.eventLayer = canvas.getChildByName('EventLayer');
        this.hud = canvas.getChildByName('HUD')?.getComponent(HUD) ?? null;
        this.babyFace = canvas.getChildByName('BabyArea')?.getChildByName('BabyFace')?.getComponent(Label) ?? null;

        // Init state
        this.sleepValue = 100;
        this.timeRemaining = this.levelConfig.duration;
        this.isLevelEnded = false;

        // Init scheduler (same node)
        this.scheduler = this.getComponent(EventScheduler);
        if (this.scheduler && this.eventLayer) {
            this.scheduler.init(this.levelConfig, this.eventLayer);
        }

        // Listen for event outcomes
        eventBus.on(GameEvents.EVENT_RESOLVED, this.onEventResolved, this);
        eventBus.on(GameEvents.EVENT_FAILED, this.onEventFailed, this);

        this.updateDisplay();
    }

    onDestroy(): void {
        eventBus.off(GameEvents.EVENT_RESOLVED, this.onEventResolved, this);
        eventBus.off(GameEvents.EVENT_FAILED, this.onEventFailed, this);
    }

    update(dt: number): void {
        if (this.isLevelEnded || !this.levelConfig) return;

        this.timeRemaining -= dt;

        if (this.timeRemaining <= 0) {
            this.timeRemaining = 0;
            this.endLevel(true);
            return;
        }

        if (this.hud) {
            this.hud.updateTimer(this.timeRemaining);
        }
    }

    private onEventResolved(data: { eventId: string; penalty: number }): void {
        if (this.isLevelEnded) return;
        this.changeSleep(data.penalty);
    }

    private onEventFailed(data: { eventId: string; penalty: number }): void {
        if (this.isLevelEnded) return;
        this.changeSleep(data.penalty);
    }

    private changeSleep(amount: number): void {
        this.sleepValue = Math.max(0, Math.min(100, this.sleepValue + amount));
        eventBus.emit(GameEvents.SLEEP_CHANGED, { value: this.sleepValue });
        this.updateDisplay();

        if (this.sleepValue <= 0) {
            this.endLevel(false);
        }
    }

    private updateDisplay(): void {
        if (this.hud) {
            this.hud.updateSleep(this.sleepValue);
            this.hud.updateTimer(this.timeRemaining);
        }
        this.updateBabyFace();
    }

    private updateBabyFace(): void {
        if (!this.babyFace) return;
        if (this.sleepValue > 50) {
            this.babyFace.string = '😴';
        } else if (this.sleepValue > 20) {
            this.babyFace.string = '😟';
        } else if (this.sleepValue > 0) {
            this.babyFace.string = '😫';
        } else {
            this.babyFace.string = '😭';
        }
    }

    private endLevel(success: boolean): void {
        if (this.isLevelEnded) return;
        this.isLevelEnded = true;

        if (this.scheduler) {
            this.scheduler.stopScheduling();
        }

        // Destroy only active event nodes (not anchor nodes)
        if (this.eventLayer) {
            for (const child of [...this.eventLayer.children]) {
                if (child.getComponent(BaseEvent)) {
                    child.destroy();
                }
            }
        }

        eventBus.emit(GameEvents.LEVEL_END, { success, sleepValue: this.sleepValue });

        this.showResultPanel(success);
    }

    private showResultPanel(success: boolean): void {
        resources.load('prefabs/ui/ResultPanel', Prefab, (err, prefab) => {
            if (err || !prefab) {
                console.error('Failed to load ResultPanel prefab', err);
                return;
            }
            const panel = instantiate(prefab);
            this.node.parent!.addChild(panel);

            const resultComp = panel.getComponent(ResultPanel);
            if (resultComp) {
                resultComp.show(success, this.sleepValue);
            }
        });
    }
}
```

- [ ] **Step 3: Refresh assets and verify no compile errors**

Run: Refresh asset database.
Check: No TypeScript errors for EventScheduler and LevelController.

- [ ] **Step 4: Commit**

```
git add BabySleep/assets/scripts/level/
git commit -m "feat: add level logic (EventScheduler, LevelController)"
```

---

### Task 5: MainMenu Scene

**Goal:** Create MainMenu.scene with background, title, and start button.

**Files:**
- Create: `BabySleep/assets/scenes/MainMenu.scene`

**Node hierarchy:**

```
Canvas (cc.Canvas, cc.Widget full screen)
├── BgMenu (Sprite: dark blue #1a1a3e, Widget: stretch all)
├── Title (Label: "Baby Sleep", fontSize=72, color=white)
│   position: (0, 150)
└── BtnStart (Button + Sprite: green #4CAF50, UITransform: 200x60)
    └── Label (Label: "开始", fontSize=36, color=white)
    position: (0, -50)
    Script: MainMenuUI on Canvas node
```

- [ ] **Step 1: Create the scene**

Create scene at `db://assets/scenes/MainMenu.scene`. Open it.

- [ ] **Step 2: Build the node hierarchy**

On the Canvas node (auto-created with scene):

1. Create child `BgMenu` — 2DNode, add `cc.Sprite` (color: #1A1A3E), add `cc.Widget` (top=0, bottom=0, left=0, right=0 to stretch full screen).
2. Create child `Title` — 2DNode, add `cc.Label` (string: "Baby Sleep", fontSize: 72, color: #FFFFFF). Set position to (0, 150, 0).
3. Create child `BtnStart` — 2DNode, add `cc.Sprite` (color: #4CAF50), add `cc.Button`, set UITransform contentSize to (200, 60). Set position to (0, -50, 0).
4. Under `BtnStart`, create child `Label` — 2DNode, add `cc.Label` (string: "开始", fontSize: 36, color: #FFFFFF).

- [ ] **Step 3: Attach MainMenuUI script**

Attach `db://assets/scripts/ui/MainMenuUI.ts` to the Canvas node.

- [ ] **Step 4: Save scene**

Save the scene.

- [ ] **Step 5: Commit**

```
git add BabySleep/assets/scenes/MainMenu.scene
git commit -m "feat: create MainMenu scene"
```

---

### Task 6: Event & ResultPanel Prefabs

**Goal:** Create PhoneRingEvent, AlarmClockEvent, and ResultPanel prefabs under `resources/`.

**Files:**
- Create: `BabySleep/assets/resources/prefabs/events/PhoneRingEvent.prefab`
- Create: `BabySleep/assets/resources/prefabs/events/AlarmClockEvent.prefab`
- Create: `BabySleep/assets/resources/prefabs/ui/ResultPanel.prefab`

#### PhoneRingEvent prefab node hierarchy:

```
PhoneRingEvent (2DNode, UITransform: 140x160)
├── Bg (Sprite: blue #2196F3, UITransform: 140x160)
├── Icon (Label: "📱", fontSize=40)
│   position: (0, 40)
├── HintLabel (Label: "长按", fontSize=20, color=#FFFFFF)
│   position: (0, 5)
├── TimeBar (2DNode)
│   ├── BarBg (Sprite: #555555, UITransform: 120x8)
│   └── BarFill (Sprite: #FFD700, UITransform: 120x8, anchorX=0, position=(-60, 0))
│   position: (0, -40)
└── PressBar (2DNode)
    ├── BarBg (Sprite: #555555, UITransform: 120x12)
    └── BarFill (Sprite: #FFFFFF, UITransform: 120x12, anchorX=0, position=(-60, 0))
    position: (0, -60)
Script: LongPressEvent on root node
```

#### AlarmClockEvent prefab node hierarchy:

```
AlarmClockEvent (2DNode, UITransform: 140x140)
├── Bg (Sprite: red #F44336, UITransform: 140x140)
├── Icon (Label: "⏰", fontSize=40)
│   position: (0, 25)
├── HintLabel (Label: "点击", fontSize=20, color=#FFFFFF)
│   position: (0, -10)
└── TimeBar (2DNode)
    ├── BarBg (Sprite: #555555, UITransform: 120x8)
    └── BarFill (Sprite: #FFD700, UITransform: 120x8, anchorX=0, position=(-60, 0))
    position: (0, -45)
Script: ClickEvent on root node
```

#### ResultPanel prefab node hierarchy:

```
ResultPanel (2DNode, Widget: stretch all)
├── Mask (Sprite: #000000 opacity=150, Widget: stretch all, BlockInputEvents)
└── Panel (Sprite: #FFFFFF, UITransform: 400x300)
    ├── TitleLabel (Label: "通关！", fontSize=36, color=#333333)
    │   position: (0, 80)
    ├── SleepLabel (Label: "安睡度: 100", fontSize=24, color=#666666)
    │   position: (0, 20)
    ├── BtnReplay (Button + Sprite: #2196F3, UITransform: 150x50)
    │   └── Label (Label: "重玩", fontSize=28, color=#FFFFFF)
    │   position: (-100, -60)
    └── BtnMenu (Button + Sprite: #9E9E9E, UITransform: 150x50)
        └── Label (Label: "主菜单", fontSize=28, color=#FFFFFF)
        position: (100, -60)
Script: ResultPanel on root node
```

- [ ] **Step 1: Create directory structure**

Create folder `db://assets/resources/prefabs/events/` and `db://assets/resources/prefabs/ui/`.

- [ ] **Step 2: Build PhoneRingEvent nodes in current scene**

Open any scene. Build the PhoneRingEvent node hierarchy as described above:
- Root: 2DNode named "PhoneRingEvent", UITransform contentSize (140, 160).
- Add children: Bg, Icon, HintLabel, TimeBar (with BarBg + BarFill), PressBar (with BarBg + BarFill).
- All BarFill nodes: set UITransform anchorPoint to (0, 0.5) and position x = -60 (half of bar width).
- Attach `db://assets/scripts/events/LongPressEvent.ts` to root node.

- [ ] **Step 3: Save as PhoneRingEvent prefab**

Use create_prefab to save the root node as `db://assets/resources/prefabs/events/PhoneRingEvent.prefab`. Then delete the temp node from the scene.

- [ ] **Step 4: Build AlarmClockEvent nodes**

Build AlarmClockEvent node hierarchy as described above:
- Root: 2DNode named "AlarmClockEvent", UITransform contentSize (140, 140).
- Add children: Bg, Icon, HintLabel, TimeBar (with BarBg + BarFill).
- BarFill: anchorPoint (0, 0.5), position x = -60.
- Attach `db://assets/scripts/events/ClickEvent.ts` to root node.

- [ ] **Step 5: Save as AlarmClockEvent prefab**

Save as `db://assets/resources/prefabs/events/AlarmClockEvent.prefab`. Delete temp node.

- [ ] **Step 6: Build ResultPanel nodes**

Build ResultPanel node hierarchy as described above:
- Root: 2DNode named "ResultPanel", add Widget (stretch all).
- Mask: Sprite (black, opacity 150), Widget (stretch all), BlockInputEvents.
- Panel: Sprite (white), UITransform (400, 300).
- Inside Panel: TitleLabel, SleepLabel, BtnReplay (with child Label), BtnMenu (with child Label).
- Attach `db://assets/scripts/ui/ResultPanel.ts` to root node.

- [ ] **Step 7: Save as ResultPanel prefab**

Save as `db://assets/resources/prefabs/ui/ResultPanel.prefab`. Delete temp node.

- [ ] **Step 8: Commit**

```
git add BabySleep/assets/resources/
git commit -m "feat: create event and result panel prefabs"
```

---

### Task 7: RoomLevel Scene

**Goal:** Create RoomLevel.scene with all gameplay nodes wired up.

**Files:**
- Create: `BabySleep/assets/scenes/RoomLevel.scene`

**Node hierarchy:**

```
Canvas (cc.Canvas, cc.Widget full screen)
├── BgRoom (Sprite: beige #F5F0E1, Widget: stretch all)
├── HUD (2DNode, Widget: top=20, left=20, right=20)
│   ├── SleepBarBg (Sprite: #555555, UITransform: 300x24)
│   │   └── SleepBarFill (Sprite: #4CAF50, UITransform: 300x24, anchorX=0, position=(-150,0))
│   │   position: (-150, 0)
│   ├── SleepLabel (Label: "100", fontSize=20, color=#FFFFFF)
│   │   position: (30, 0)
│   └── TimerLabel (Label: "01:00", fontSize=24, color=#FFFFFF)
│       position: (250, 0)
│   Script: HUD
├── BabyArea (2DNode)
│   ├── Bed (Sprite: #5D4037, UITransform: 250x80)
│   └── BabyFace (Label: "😴", fontSize=64)
│       position: (0, 60)
│   position: (0, -200)
├── EventLayer (2DNode)
│   ├── AnchorPhone (2DNode, position=(300, 50))
│   └── AnchorAlarm (2DNode, position=(-300, 50))
└── LevelRoot (2DNode)
    Script: LevelController + EventScheduler
```

- [ ] **Step 1: Create the scene**

Create scene at `db://assets/scenes/RoomLevel.scene`. Open it.

- [ ] **Step 2: Build background and baby area**

On Canvas:
1. Create `BgRoom` — Sprite (#F5F0E1), Widget (stretch all).
2. Create `BabyArea` — 2DNode at position (0, -200).
3. Under `BabyArea`: create `Bed` — Sprite (#5D4037), UITransform (250, 80).
4. Under `BabyArea`: create `BabyFace` — Label ("😴", fontSize 64) at position (0, 60).

- [ ] **Step 3: Build HUD**

Under Canvas:
1. Create `HUD` — 2DNode. Add Widget (align top).
2. Under `HUD`: create `SleepBarBg` — Sprite (#555555), UITransform (300, 24), at position (-150, 0).
3. Under `SleepBarBg`: create `SleepBarFill` — Sprite (#4CAF50), UITransform (300, 24), anchorPoint (0, 0.5), at position (-150, 0).
4. Under `HUD`: create `SleepLabel` — Label ("100", fontSize 20, color #FFFFFF) at position (30, 0).
5. Under `HUD`: create `TimerLabel` — Label ("01:00", fontSize 24, color #FFFFFF) at position (250, 0).
6. Attach `db://assets/scripts/ui/HUD.ts` to `HUD` node.

- [ ] **Step 4: Build event layer and anchors**

Under Canvas:
1. Create `EventLayer` — 2DNode.
2. Under `EventLayer`: create `AnchorPhone` — 2DNode at position (300, 50).
3. Under `EventLayer`: create `AnchorAlarm` — 2DNode at position (-300, 50).

- [ ] **Step 5: Build LevelRoot and attach scripts**

Under Canvas:
1. Create `LevelRoot` — 2DNode.
2. Attach `db://assets/scripts/level/LevelController.ts` to `LevelRoot`.
3. Attach `db://assets/scripts/level/EventScheduler.ts` to `LevelRoot`.

- [ ] **Step 6: Save scene**

Save the scene.

- [ ] **Step 7: Commit**

```
git add BabySleep/assets/scenes/RoomLevel.scene
git commit -m "feat: create RoomLevel scene with full node hierarchy"
```

---

### Task 8: Integration Verification

**Goal:** Wire up build settings, run preview, and verify the complete game loop.

- [ ] **Step 1: Add scenes to build settings**

In Cocos Creator Project Settings → Scenes, add both scenes:
- `db://assets/scenes/MainMenu.scene` — set as start scene
- `db://assets/scenes/RoomLevel.scene`

This is required for `director.loadScene()` to find the scenes by name.

- [ ] **Step 2: Run preview**

Start preview (MCP: `run_project` or browser preview). The game should open on MainMenu.

- [ ] **Step 3: Verify main menu**

Expected: Dark blue background, "Baby Sleep" title, green "开始" button. Click the button → scene switches to RoomLevel.

- [ ] **Step 4: Verify level gameplay**

Expected in RoomLevel:
- HUD shows "100" sleep value, timer counts down from "01:00"
- After ~8 seconds, first event appears at AnchorPhone or AnchorAlarm position
- Click event (alarm): touch it → event disappears, sleep stays 100
- Long press event (phone): hold 2 seconds → progress bar fills → event disappears
- If event times out → sleep drops by 15

- [ ] **Step 5: Verify win condition**

Let timer run to 00:00 with sleep > 0. Expected: All events cleared, ResultPanel appears with "通关！" and final sleep value.

- [ ] **Step 6: Verify lose condition**

Let multiple events time out until sleep = 0. Expected: ResultPanel appears with "宝宝哭醒了..." immediately when sleep hits 0.

- [ ] **Step 7: Verify result panel buttons**

- Click "重玩" → RoomLevel reloads, timer resets to 01:00, sleep resets to 100.
- Click "主菜单" → scene switches back to MainMenu.

- [ ] **Step 8: Fix any issues found, then commit**

```
git add .
git commit -m "feat: Baby Sleep Level 1 MVP complete"
```
