// assets/scripts/data/EventConfig.ts
export type InteractionType = 'click' | 'longPress' | 'drag' | 'combo';

export interface EventConfig {
    id: string;
    name: string;
    interactionType: InteractionType;
    timeWindow: number;
    requiredDuration?: number;
    comboSteps?: InteractionType[];
    sleepPenalty: number;
    sleepMinorPenalty: number;
    difficulty: 'easy' | 'medium' | 'hard';
    isDream: boolean;
    prefabPath: string;
    spawnAnchor: string;
}

export const EVENT_CONFIGS: Record<string, EventConfig> = {
    phone_ring: {
        id: 'phone_ring',
        name: '手机响铃',
        interactionType: 'longPress',
        timeWindow: 5,
        requiredDuration: 2,
        sleepPenalty: -15,
        sleepMinorPenalty: 0,
        difficulty: 'easy',
        isDream: false,
        prefabPath: 'prefabs/events/PhoneRingEvent',
        spawnAnchor: 'AnchorPhone',
    },
    alarm_clock: {
        id: 'alarm_clock',
        name: '闹钟响了',
        interactionType: 'click',
        timeWindow: 4,
        sleepPenalty: -15,
        sleepMinorPenalty: 0,
        difficulty: 'easy',
        isDream: false,
        prefabPath: 'prefabs/events/AlarmClockEvent',
        spawnAnchor: 'AnchorAlarm',
    },
};
