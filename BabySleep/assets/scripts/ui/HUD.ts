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
