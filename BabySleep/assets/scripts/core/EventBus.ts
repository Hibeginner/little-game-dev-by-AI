// assets/scripts/core/EventBus.ts
import { EventTarget } from 'cc';

export enum GameEvents {
    SLEEP_CHANGED = 'SLEEP_CHANGED',
    EVENT_SPAWNED = 'EVENT_SPAWNED',
    EVENT_RESOLVED = 'EVENT_RESOLVED',
    EVENT_FAILED = 'EVENT_FAILED',
    LEVEL_END = 'LEVEL_END',
}

export const eventBus = new EventTarget();
