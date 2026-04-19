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
