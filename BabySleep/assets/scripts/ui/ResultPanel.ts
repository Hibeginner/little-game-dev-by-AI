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
