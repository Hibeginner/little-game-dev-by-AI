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
