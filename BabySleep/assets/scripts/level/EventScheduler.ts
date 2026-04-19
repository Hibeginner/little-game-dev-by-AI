// assets/scripts/level/EventScheduler.ts
import { _decorator, Component, Node, resources, Prefab, instantiate } from 'cc';
import { LevelConfig } from '../data/LevelConfig';
import { EVENT_CONFIGS, EventConfig } from '../data/EventConfig';
import { eventBus, GameEvents } from '../core/EventBus';
import { BaseEvent } from '../events/BaseEvent';

const { ccclass } = _decorator;

@ccclass('EventScheduler')
export class EventScheduler extends Component {

    private levelConfig: LevelConfig | null = null;
    private eventLayer: Node | null = null;
    private timeSinceLastSpawn: number = 0;
    private isScheduling: boolean = false;
    private activeEventCount: number = 0;
    private prefabCache: Map<string, Prefab> = new Map();

    public init(config: LevelConfig, eventLayer: Node): void {
        this.levelConfig = config;
        this.eventLayer = eventLayer;
        this.timeSinceLastSpawn = 0;
        this.activeEventCount = 0;
        this.isScheduling = true;

        eventBus.on(GameEvents.EVENT_RESOLVED, this.onEventComplete, this);
        eventBus.on(GameEvents.EVENT_FAILED, this.onEventComplete, this);

        this.preloadPrefabs();
    }

    onDestroy(): void {
        eventBus.off(GameEvents.EVENT_RESOLVED, this.onEventComplete, this);
        eventBus.off(GameEvents.EVENT_FAILED, this.onEventComplete, this);
    }

    private preloadPrefabs(): void {
        if (!this.levelConfig) {
            return;
        }
        for (const eventId of this.levelConfig.eventPool) {
            const config = EVENT_CONFIGS[eventId];
            if (config) {
                resources.load(config.prefabPath, Prefab, (err, prefab) => {
                    if (err) {
                        console.error(`Failed to load prefab: ${config.prefabPath}`, err);
                        return;
                    }
                    this.prefabCache.set(eventId, prefab!);
                });
            }
        }
    }

    public stopScheduling(): void {
        this.isScheduling = false;
    }

    update(dt: number): void {
        if (!this.isScheduling || !this.levelConfig) return;

        this.timeSinceLastSpawn += dt;

        if (this.timeSinceLastSpawn >= this.levelConfig.eventInterval) {
            this.timeSinceLastSpawn = 0;
            this.trySpawnEvent();
        }
    }

    private trySpawnEvent(): void {
        if (!this.levelConfig || !this.eventLayer) {
            return;
        }
        if (this.activeEventCount >= this.levelConfig.maxConcurrent) {
            return;
        }

        const pool = this.levelConfig.eventPool;
        const randomIndex = Math.floor(Math.random() * pool.length);
        const eventId = pool[randomIndex];
        const config = EVENT_CONFIGS[eventId];
        if (!config) {
            return;
        }

        const prefab = this.prefabCache.get(eventId);
        if (!prefab) {
            console.warn(`Prefab not loaded yet for event: ${eventId}`);
            return;
        }

        this.spawnEvent(config, prefab);
    }

    private spawnEvent(config: EventConfig, prefab: Prefab): void {
        const eventNode = instantiate(prefab);
        this.eventLayer!.addChild(eventNode);

        // Position at anchor point
        const anchor = this.eventLayer!.getChildByName(config.spawnAnchor);
        if (anchor) {
            eventNode.setPosition(anchor.position.clone());
        }

        // Initialize event component (finds subclass via instanceof)
        const eventComponent = eventNode.getComponent(BaseEvent);
        if (eventComponent) {
            eventComponent.init(config, this.levelConfig!.responseTimeMultiplier);
        }

        this.activeEventCount++;
        eventBus.emit(GameEvents.EVENT_SPAWNED, { eventId: config.id });
    }

    private onEventComplete(): void {
        this.activeEventCount = Math.max(0, this.activeEventCount - 1);
    }
}
