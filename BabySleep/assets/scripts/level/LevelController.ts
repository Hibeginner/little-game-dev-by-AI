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
