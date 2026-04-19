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
