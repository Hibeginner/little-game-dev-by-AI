# Baby Sleep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a "Whack-a-Mole" variant reaction game where players manage an infant's sleep by handling random interactive events (clicks, long-presses, drags) in a room and dream setting over 15 progressive levels.

**Architecture:** Cocos Creator 3.x project utilizing a single GameManager for state, a shared RoomLevel/DreamLevel scene, an EventScheduler to spawn prefabs based on LevelConfig, and BaseEvent derived components handling input and time-window lifecycles.

**Tech Stack:** Cocos Creator 3.x, TypeScript, localStorage (SaveManager).

---

### Task 1: Project Scaffolding & Core Architecture setup

**Goal:** Initialize the Cocos project and create the foundational manager scripts.

**Files:**
- Create: `assets/scripts/core/GameManager.ts`
- Create: `assets/scripts/core/SaveManager.ts`
- Create: `assets/scripts/core/EventBus.ts`
- Create: `assets/scripts/data/LevelConfig.ts`
- Create: `assets/scripts/data/EventConfig.ts`

- [ ] **Step 1: Create the Cocos project**

```bash
# Assuming Cocos Dashboard is installed, create an empty 2D project via CLI or instruct the user to do so via Dashboard if CLI is unavailable.
# For plan purposes, we assume the user creates it in D:\little-game\BabySleep and we work within D:\little-game\BabySleep
# If not already created, stop and ask the user to create an empty Cocos 3.x 2D project named "BabySleep" in the working directory.
```

- [ ] **Step 2: Create EventBus**

```typescript
// assets/scripts/core/EventBus.ts
import { EventTarget } from 'cc';
export const eventBus = new EventTarget();

export enum GameEvents {
    SLEEP_CHANGED = 'SLEEP_CHANGED',
    EVENT_SPAWNED = 'EVENT_SPAWNED',
    EVENT_RESOLVED = 'EVENT_RESOLVED',
    EVENT_FAILED = 'EVENT_FAILED',
    LEVEL_END = 'LEVEL_END'
}
```

- [ ] **Step 3: Create SaveManager**

```typescript
// assets/scripts/core/SaveManager.ts
export interface SaveData {
    levelStars: Record<number, number>;
}

export class SaveManager {
    private static readonly SAVE_KEY = 'baby_sleep_save';
    
    static load(): SaveData {
        const data = localStorage.getItem(this.SAVE_KEY);
        if (data) {
            try { return JSON.parse(data); } catch (e) { }
        }
        return { levelStars: {} };
    }

    static save(data: SaveData) {
        localStorage.setItem(this.SAVE_KEY, JSON.stringify(data));
    }

    static getStars(levelId: number): number {
        return this.load().levelStars[levelId] || 0;
    }

    static saveStars(levelId: number, stars: number) {
        const data = this.load();
        if (stars > (data.levelStars[levelId] || 0)) {
            data.levelStars[levelId] = stars;
            this.save(data);
        }
    }
}
```

- [ ] **Step 4: Create EventConfig and LevelConfig basic structures**

```typescript
// assets/scripts/data/EventConfig.ts
export type InteractionType = 'click' | 'longPress' | 'drag' | 'combo';

export interface EventDef {
    id: string;
    interactionType: InteractionType;
    timeWindow: number;
    sleepPenalty: number;
    sleepMinorPenalty: number;
    prefabName: string;
}

export const EVENTS: Record<string, EventDef> = {
    'phone_ring': { id: 'phone_ring', interactionType: 'longPress', timeWindow: 5, sleepPenalty: 15, sleepMinorPenalty: 0, prefabName: 'Event_Phone' },
    'vase_fall': { id: 'vase_fall', interactionType: 'click', timeWindow: 5, sleepPenalty: 15, sleepMinorPenalty: 0, prefabName: 'Event_Vase' }
    // Add others from spec later
};
```

```typescript
// assets/scripts/data/LevelConfig.ts
export interface LevelDef {
    id: number;
    name: string;
    duration: number;
    eventPool: string[];
    maxConcurrent: number;
    eventInterval: number;
    responseTimeMultiplier: number;
    isDream: boolean;
}

export const LEVELS: Record<number, LevelDef> = {
    1: { id: 1, name: 'Night One', duration: 60, eventPool: ['phone_ring'], maxConcurrent: 1, eventInterval: 8, responseTimeMultiplier: 1.0, isDream: false },
    2: { id: 2, name: 'Night Two', duration: 60, eventPool: ['phone_ring', 'vase_fall'], maxConcurrent: 1, eventInterval: 7, responseTimeMultiplier: 1.0, isDream: false }
    // Add others from spec later
};
```

- [ ] **Step 5: Create GameManager**

```typescript
// assets/scripts/core/GameManager.ts
import { director } from 'cc';
import { LevelDef, LEVELS } from '../data/LevelConfig';

export class GameManager {
    private static _instance: GameManager;
    public static get instance() {
        if (!this._instance) this._instance = new GameManager();
        return this._instance;
    }

    public currentLevelId: number = 1;

    public startLevel(levelId: number) {
        this.currentLevelId = levelId;
        const config = LEVELS[levelId];
        if (config.isDream) {
            director.loadScene('DreamLevel');
        } else {
            director.loadScene('RoomLevel');
        }
    }

    public getCurrentConfig(): LevelDef {
        return LEVELS[this.currentLevelId];
    }
}
```

---

### Task 2: Base Event System

**Goal:** Create the abstract BaseEvent component that handles the time window and failure logic for all interactive events.

**Files:**
- Create: `assets/scripts/events/BaseEvent.ts`

- [ ] **Step 1: Write BaseEvent script**

```typescript
// assets/scripts/events/BaseEvent.ts
import { _decorator, Component, Node } from 'cc';
import { EventDef } from '../data/EventConfig';
import { eventBus, GameEvents } from '../core/EventBus';

const { ccclass, property } = _decorator;

@ccclass('BaseEvent')
export class BaseEvent extends Component {
    protected config!: EventDef;
    protected timeRemaining: number = 0;
    protected isResolved: boolean = false;
    protected multiplier: number = 1.0;

    init(config: EventDef, timeMultiplier: number) {
        this.config = config;
        this.multiplier = timeMultiplier;
        this.timeRemaining = config.timeWindow * timeMultiplier;
        this.isResolved = false;
    }

    update(dt: number) {
        if (this.isResolved) return;
        
        this.timeRemaining -= dt;
        this.onTimeUpdate(this.timeRemaining / (this.config.timeWindow * this.multiplier));

        if (this.timeRemaining <= 0) {
            this.fail();
        }
    }

    // Override in subclasses to update UI (like the red circle timer)
    protected onTimeUpdate(normalizedTime: number) {}

    protected resolve() {
        if (this.isResolved) return;
        this.isResolved = true;
        eventBus.emit(GameEvents.EVENT_RESOLVED, this.config);
        this.node.destroy();
    }

    protected fail() {
        if (this.isResolved) return;
        this.isResolved = true;
        eventBus.emit(GameEvents.EVENT_FAILED, this.config);
        this.node.destroy();
    }
}
```

---

### Task 3: Interaction Components (Click & LongPress)

**Goal:** Implement specific interactive behaviors by extending BaseEvent.

**Files:**
- Create: `assets/scripts/events/ClickEvent.ts`
- Create: `assets/scripts/events/LongPressEvent.ts`

- [ ] **Step 1: Write ClickEvent**

```typescript
// assets/scripts/events/ClickEvent.ts
import { _decorator, Node } from 'cc';
import { BaseEvent } from './BaseEvent';
const { ccclass } = _decorator;

@ccclass('ClickEvent')
export class ClickEvent extends BaseEvent {
    onLoad() {
        this.node.on(Node.EventType.TOUCH_END, this.onClick, this);
    }

    onClick() {
        if (this.isResolved) return;
        this.resolve();
    }
}
```

- [ ] **Step 2: Write LongPressEvent**

```typescript
// assets/scripts/events/LongPressEvent.ts
import { _decorator, Node } from 'cc';
import { BaseEvent } from './BaseEvent';
const { ccclass } = _decorator;

@ccclass('LongPressEvent')
export class LongPressEvent extends BaseEvent {
    private requiredTime: number = 2.0; // Seconds to hold
    private currentHoldTime: number = 0;
    private isHolding: boolean = false;

    onLoad() {
        this.node.on(Node.EventType.TOUCH_START, this.onTouchStart, this);
        this.node.on(Node.EventType.TOUCH_END, this.onTouchEnd, this);
        this.node.on(Node.EventType.TOUCH_CANCEL, this.onTouchEnd, this);
    }

    onTouchStart() {
        if (this.isResolved) return;
        this.isHolding = true;
    }

    onTouchEnd() {
        this.isHolding = false;
        this.currentHoldTime = 0; // Reset or decay based on design, reset is simpler
        this.updateHoldUI(0);
    }

    update(dt: number) {
        super.update(dt);
        if (this.isResolved) return;

        if (this.isHolding) {
            this.currentHoldTime += dt;
            this.updateHoldUI(this.currentHoldTime / this.requiredTime);
            
            if (this.currentHoldTime >= this.requiredTime) {
                this.resolve();
            }
        }
    }

    private updateHoldUI(progress: number) {
        // Optional: Update a progress bar or scale a node to show hold progress
    }
}
```

---

### Task 4: Level Controller and Event Scheduler

**Goal:** Implement the logic that manages the sleep meter, timer, and spawning random events.

**Files:**
- Create: `assets/scripts/level/LevelController.ts`
- Create: `assets/scripts/level/EventScheduler.ts`

- [ ] **Step 1: Write LevelController**

```typescript
// assets/scripts/level/LevelController.ts
import { _decorator, Component, Node } from 'cc';
import { eventBus, GameEvents } from '../core/EventBus';
import { GameManager } from '../core/GameManager';
import { EventDef } from '../data/EventConfig';

const { ccclass, property } = _decorator;

@ccclass('LevelController')
export class LevelController extends Component {
    public sleepValue: number = 100;
    public timeRemaining: number = 0;
    private isGameOver: boolean = false;

    start() {
        const config = GameManager.instance.getCurrentConfig();
        this.timeRemaining = config.duration;
        this.sleepValue = 100;

        eventBus.on(GameEvents.EVENT_RESOLVED, this.onEventResolved, this);
        eventBus.on(GameEvents.EVENT_FAILED, this.onEventFailed, this);
    }

    onDestroy() {
        eventBus.off(GameEvents.EVENT_RESOLVED, this.onEventResolved, this);
        eventBus.off(GameEvents.EVENT_FAILED, this.onEventFailed, this);
    }

    update(dt: number) {
        if (this.isGameOver) return;

        this.timeRemaining -= dt;
        if (this.timeRemaining <= 0) {
            this.timeRemaining = 0;
            this.endGame(true); // Win
        }
    }

    onEventResolved(evt: EventDef) {
        this.modifySleep(-evt.sleepMinorPenalty);
    }

    onEventFailed(evt: EventDef) {
        this.modifySleep(-evt.sleepPenalty);
    }

    private modifySleep(delta: number) {
        if (this.isGameOver) return;
        this.sleepValue += delta;
        this.sleepValue = Math.max(0, Math.min(100, this.sleepValue));
        
        eventBus.emit(GameEvents.SLEEP_CHANGED, this.sleepValue);

        if (this.sleepValue <= 0) {
            this.endGame(false); // Lose
        }
    }

    private endGame(isWin: boolean) {
        this.isGameOver = true;
        let stars = 0;
        if (isWin) {
            if (this.sleepValue >= 80) stars = 3;
            else if (this.sleepValue >= 50) stars = 2;
            else stars = 1;
        }
        eventBus.emit(GameEvents.LEVEL_END, { isWin, stars });
    }
}
```

- [ ] **Step 2: Write EventScheduler**

```typescript
// assets/scripts/level/EventScheduler.ts
import { _decorator, Component, Node, Prefab, instantiate, resources } from 'cc';
import { GameManager } from '../core/GameManager';
import { EVENTS } from '../data/EventConfig';
import { BaseEvent } from '../events/BaseEvent';

const { ccclass, property } = _decorator;

@ccclass('EventScheduler')
export class EventScheduler extends Component {
    @property(Node)
    public eventContainer: Node = null!; // Where spawned prefabs go

    private timeSinceLastEvent: number = 0;
    private activeEventCount: number = 0;
    private isRunning: boolean = true;

    start() {
        // Assume level controller stops this on game over
        // We'd also need to load prefabs dynamically or assign them in the editor.
        // For simplicity in this plan, assume prefabs are placed in resources/prefabs/
    }

    update(dt: number) {
        if (!this.isRunning) return;
        
        const config = GameManager.instance.getCurrentConfig();
        this.timeSinceLastEvent += dt;

        if (this.timeSinceLastEvent >= config.eventInterval && this.activeEventCount < config.maxConcurrent) {
            this.spawnRandomEvent();
            this.timeSinceLastEvent = 0;
        }
    }

    spawnRandomEvent() {
        const config = GameManager.instance.getCurrentConfig();
        const pool = config.eventPool;
        if (pool.length === 0) return;

        const randomId = pool[Math.floor(Math.random() * pool.length)];
        const evtDef = EVENTS[randomId];

        resources.load(`prefabs/${evtDef.prefabName}`, Prefab, (err, prefab) => {
            if (err) return;
            const node = instantiate(prefab);
            node.setParent(this.eventContainer);
            
            // Assume the prefab has the correct BaseEvent derived component attached
            const evtComp = node.getComponent(BaseEvent);
            if (evtComp) {
                evtComp.init(evtDef, config.responseTimeMultiplier);
                this.activeEventCount++;
                
                // Hook node destruction to decrement active count
                const origDestroy = node.destroy.bind(node);
                node.destroy = () => {
                    this.activeEventCount--;
                    return origDestroy();
                };
            }
        });
    }
    
    stop() { this.isRunning = false; }
}
```

---

### Task 5: UI Implementation (HUD & Result Panel)

**Goal:** Create the UI to show sleep meter, timer, and the end-of-level screen.

**Files:**
- Create: `assets/scripts/ui/HUD.ts`
- Create: `assets/scripts/ui/ResultPanel.ts`

- [ ] **Step 1: Write HUD script**

```typescript
// assets/scripts/ui/HUD.ts
import { _decorator, Component, Label, ProgressBar } from 'cc';
import { eventBus, GameEvents } from '../core/EventBus';
import { LevelController } from '../level/LevelController';

const { ccclass, property } = _decorator;

@ccclass('HUD')
export class HUD extends Component {
    @property(ProgressBar) sleepBar: ProgressBar = null!;
    @property(Label) timerLabel: Label = null!;
    @property(LevelController) levelController: LevelController = null!;

    start() {
        eventBus.on(GameEvents.SLEEP_CHANGED, this.onSleepChanged, this);
    }

    onDestroy() {
        eventBus.off(GameEvents.SLEEP_CHANGED, this.onSleepChanged, this);
    }

    update(dt: number) {
        if (this.levelController) {
            this.timerLabel.string = Math.ceil(this.levelController.timeRemaining).toString();
        }
    }

    onSleepChanged(val: number) {
        this.sleepBar.progress = val / 100;
    }
}
```

- [ ] **Step 2: Write ResultPanel script**

```typescript
// assets/scripts/ui/ResultPanel.ts
import { _decorator, Component, Label, Node } from 'cc';
import { eventBus, GameEvents } from '../core/EventBus';
import { GameManager } from '../core/GameManager';
import { SaveManager } from '../core/SaveManager';

const { ccclass, property } = _decorator;

@ccclass('ResultPanel')
export class ResultPanel extends Component {
    @property(Node) panelRoot: Node = null!;
    @property(Label) titleLabel: Label = null!;
    @property(Label) starsLabel: Label = null!;

    start() {
        this.panelRoot.active = false;
        eventBus.on(GameEvents.LEVEL_END, this.onLevelEnd, this);
    }

    onDestroy() {
        eventBus.off(GameEvents.LEVEL_END, this.onLevelEnd, this);
    }

    onLevelEnd(data: { isWin: boolean, stars: number }) {
        this.panelRoot.active = true;
        if (data.isWin) {
            this.titleLabel.string = "Baby is Asleep!";
            this.starsLabel.string = "★".repeat(data.stars);
            SaveManager.saveStars(GameManager.instance.currentLevelId, data.stars);
        } else {
            this.titleLabel.string = "Baby Woke Up!";
            this.starsLabel.string = "Failed";
        }
    }

    onRetryClicked() {
        GameManager.instance.startLevel(GameManager.instance.currentLevelId);
    }

    onNextClicked() {
        GameManager.instance.startLevel(GameManager.instance.currentLevelId + 1);
    }
}
```

---

Plan complete and saved to `docs/superpowers/plans/2026-04-08-baby-sleep.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?