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
