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
