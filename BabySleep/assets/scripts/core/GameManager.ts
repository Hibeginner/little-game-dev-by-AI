// assets/scripts/core/GameManager.ts
import { director, Scene } from 'cc';
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
        director.loadScene(config.sceneName, function (error: null | Error, scene?: Scene) {
            console.log('Scene loaded');
            if (!error && scene) {
                console.log('Scene name:', scene.name);
            }
        });
    }

    public static backToMenu(): void {
        director.loadScene('MainMenu');
    }
}
